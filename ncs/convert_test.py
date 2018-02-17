
from __future__ import division

#import cv2
from PIL import Image
import numpy as np
import math
from skimage.transform import resize



def load_image( infilename ):
    img = Image.open( infilename )
    img.load()
    return img

def convert_image(image):
    return  np.asarray( img, dtype="float16" )

def save_image( npdata, outfilename ):
    img = Image.fromarray( np.asarray( np.clip(npdata,0,255), dtype="uint8"), "L" )
    img.save( outfilename )


def PrepareImage(img, dim):
    imgw = img.shape[1]
    imgh = img.shape[0]
    imgb = np.empty((dim[1], dim[0], 3))
    imgb.fill(0.5)

    if imgh/imgw > dim[1]/dim[0]:
        neww = int(imgw * dim[1] / imgh)
        newh = dim[1]
    else:
        newh = int(imgh * dim[0] / imgw)
        neww = dim[0]
        offx = int((dim[0] - neww)/2)
        offy = int((dim[1] - newh)/2)

    print("H: %d, W: %d" %(imgh, imgw))

    print("nH: %d, nW: %d, offx: %d, offy: %d" %(newh, neww, offx, offy))

    imgb[offy:offy+newh,offx:offx+neww,:] = resize(img.copy()/255.0,(newh,neww),1)
    im = imgb[:,:,(2,1,0)]
    return im, int(offx*imgw/neww), int(offy*imgh/newh), neww/dim[0], newh/dim[1]


def PrepareImageNoCV(img, dim):
    imgw = 320
    imgh = 180
    imgb = np.empty((dim[1], dim[0], 3))
    imgb.fill(0.5)

    if imgh/imgw > dim[1]/dim[0]:
        neww = int(imgw * dim[1] / imgh)
        newh = dim[1]
    else:
        newh = int(imgh * dim[0] / imgw)
        neww = dim[0]
        offx = int((dim[0] - neww)/2)
        offy = int((dim[1] - newh)/2)

    print("H: %d, W: %d" %(imgh, imgw))

    print("nH: %d, nW: %d, offx: %d, offy: %d" %(newh, neww, offx, offy))

    #img2 = np.array(img)

    imgb[offy:offy+newh,offx:offx+neww,:] = resize(img.copy()/255.0,(newh,neww),1)
    im = imgb[:,:,(2,1,0)]
    return im, int(offx*imgw/neww), int(offy*imgh/newh), neww/dim[0], newh/dim[1]

# main entry point for the program
if __name__=="__main__":

    filename = 'images/image_27.jpg'
    img = load_image(filename)
    #data = convert_image(img)

    #print(data.shape)
    #print(data)

    pil_image = Image.open(filename).convert('RGB')
    open_cv_image = np.array(pil_image)
    # Convert RGB to BGR
    open_cv_image = open_cv_image[:, :, ::-1].copy()


    # img2 = cv2.imread(filename)
    # imgw = img2.shape[1]
    # imgh = img2.shape[0]
    #
    dim = (320,180)

    im,offx,offy,xscale,yscale = PrepareImageNoCV(open_cv_image, dim)

    print(im)

    print("Goodbye.")
