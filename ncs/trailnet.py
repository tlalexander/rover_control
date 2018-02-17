
from __future__ import division

import mvnc.mvncapi as fx
from PIL import Image
import numpy as np
import picamera
import math

import matplotlib.pyplot as plt
import matplotlib.image as mpimg


DIRECTION_FILTER_INNOV_COEFF_ = 1.0
DNN_TURN_ANGLE_ = 10.0
DNN_LATERAL_CORR_ANGLE_ = 10.0


font = {'family': 'serif',
        'color':  'darkred',
        'weight': 'normal',
        'size': 16,
        }

def load_image( infilename ):
    img = Image.open( infilename )
    img.load()
    return img

def convert_image(image):
    return  np.asarray( img, dtype="float16" )

def save_image( npdata, outfilename ):
    img = Image.fromarray( np.asarray( np.clip(npdata,0,255), dtype="uint8"), "L" )
    img.save( outfilename )

def computeDNNControl(class_probabilities):
    # Normalize probabilities just in case. We have 6 classes, they are disjoint - 1st 3 are rotations and 2nd 3 are translations
    prob_sum = class_probabilities[0] + class_probabilities[1] + class_probabilities[2]
    assert prob_sum != 0
    left_view_p   = class_probabilities[0] / prob_sum
    right_view_p  = class_probabilities[2] / prob_sum

    prob_sum = class_probabilities[3] + class_probabilities[4] + class_probabilities[5]
    assert prob_sum != 0
    left_side_p   = class_probabilities[3] / prob_sum
    right_side_p  = class_probabilities[5] / prob_sum

    # Compute turn angle from probabilities. Positive angle - turn left, negative - turn right, 0 - go straight
    current_turn_angle_deg =  DNN_TURN_ANGLE_*(right_view_p - left_view_p) + DNN_LATERAL_CORR_ANGLE_*(right_side_p - left_side_p)

    # Do sanity check and convert to radians
    current_turn_angle_deg = max(-90.0, min(current_turn_angle_deg, 90.0))   # just in case to avoid bad control
    current_turn_angle_rad = math.degrees(current_turn_angle_deg)

    # TLA - Not sure what this variable should be...
    turn_angle_ = 0

    # Filter computed turning angle with the exponential filter
    turn_angle_ = turn_angle_*(1 - DIRECTION_FILTER_INNOV_COEFF_) + current_turn_angle_rad * DIRECTION_FILTER_INNOV_COEFF_ # TODO: should this protected by a lock?
    turn_angle_rad = turn_angle_
    # end of turning angle filtering

    print("DNN turn angle: %4.2f deg.", math.degrees(turn_angle_rad));

    # Create control values that lie on a unit circle to mimic max joystick control values that are on a unit circle
    linear_control_val  = math.cos(turn_angle_rad);
    angular_control_val = math.sin(turn_angle_rad);

    return linear_control_val, angular_control_val


# main entry point for the program
if __name__=="__main__":

     # set the logging level for the NC API
    fx.SetGlobalOption(fx.GlobalOption.LOG_LEVEL, 0)

    # get a list of names for all the devices plugged into the system
    ncs_names = fx.EnumerateDevices()
    if (len(ncs_names) < 1):
        print("Error - no NCS devices detected, verify an NCS device is connected.")
        quit()


    # get the first NCS device by its name.  For this program we will always open the first NCS device.
    dev = fx.Device(ncs_names[0])


    # try to open the device.  this will throw an exception if someone else has it open already
    try:
        dev.OpenDevice()
    except:
        print("Error - Could not open NCS device.")
        quit()


    graph_blob = "/home/pi/rover/ncs/trailnet_graph"
    #graph_blob = "/home/pi/rover/TrailNet/graph"
    with open(graph_blob, mode='rb') as f:
        blob = f.read()

    print("Hello NCS! Device opened normally.")
    graph = dev.AllocateGraph(blob)
    #graph = dev.AllocateGraph("/home/pi/Programming/ncsdk/examples/caffe/AlexNet/graph")

    img_names= ["trail_small.jpg", "trail_small_right.jpg", "trail_small_left.jpg"]

    plt.ion()
    plt.show()

    camera = picamera.PiCamera()
    camera.hflip = False
    camera.vflip = False
    for image in range(100):
        camera.resolution = (320,180)

        filename = 'images/image_%d.jpg'%image
        camera.capture(filename)
        img = load_image(filename)
        data = convert_image(img)
        #print(data.shape)
        if (graph.LoadTensor(data.astype(np.float16), 'user object')):
            #print("LoadTensor success")
            output, userobj = graph.GetResult()
            translation, steering = computeDNNControl(output)

            print("Translation: %g, rotation %g" % (translation, steering))

            #
            # rotation = [output[0], output[2]]
            # translation = [output[3], output[5]]
            # turn_dir = "Left" if output[3]>output[5] else "Right"
            #
            # print(output)
            # print(turn_dir)
            # print("Max Rotation: %d, Max Translation: %d, filename: %s" %(np.argmax(rotation), np.argmax(translation), filename))

            #print(output)
            #print(userobj)
            plt.gcf().clear()
            imgplot = plt.imshow(img)
            # for txt in fig.texts:
            #     txt.set_visible(False)
            plt.text(20, -20, steering)
            plt.xticks([])
            plt.yticks([])
            plt.draw()
            plt.pause(0.001)
            plt.savefig('%s.png' % filename)

    graph.DeallocateGraph()
    try:
        dev.CloseDevice()
    except:
        print("Error - could not close NCS device.")
        quit()

    print("Goodbye NCS! Device closed normally.")
    print("NCS device working.")
