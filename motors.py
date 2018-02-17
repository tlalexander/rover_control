
import multiprocessing as mp
from time import sleep
from time import time
from vesc import CanVesc
import sys
import os
import math
import numpy as np
import threading


from concurrent import futures
import grpc
import rover_pb2
import rover_pb2_grpc

end_program = False

MAX_CURRENT = 10
MAX_BRAKE_CURRENT = 1

P_SCALAR = 1/250.0
D_SCALAR = 1/100.0

_NUM_ERRORS_TO_AVERAGE = 3

throttle_left = 0
throttle_right = 0
throttle_back_left = 0
throttle_back_right = 0

lock = None

# Don't forget to set up CAN with:
# ip link set can0 up type can bitrate 1000000

def main(e, argv):
    if len(argv) != 2:
          print('Provide CAN device name (can0, slcan0 etc.)')
          sys.exit(0)
    vesc = CanVesc(argv[1])

    global lock
    lock = threading.Lock()

    print("Blah")

    # Start Motor Control Thread
    control_thread = ControlThread(name = "MotionControlThread", lock=lock, event=e, vesc=vesc)  # ...Instantiate a thread and pass a unique ID to it
    control_thread.daemon = True
    control_thread.start()
    sleep(0.5)

    ACCELERATION = 50000

    print("Blahblah")

    with lock:
             control_thread.motor0.acceleration = ACCELERATION
             control_thread.motor1.acceleration = ACCELERATION
             #control_thread.motor2.acceleration = ACCELERATION
             #control_thread.motor3.acceleration = ACCELERATION
    SPEED = 1000

    if False:
        # do some debug shit. Make this false for normal operaton.
        with lock:
            control_thread.motor1.velocity_goal = -SPEED
            control_thread.motor0.velocity_goal = SPEED
        sleep(200)


    print("GRPC Server Exception!")

    try:
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        rover_pb2_grpc.add_ExchangeServicer_to_server(
        Exchange(), server)
        server.add_insecure_port('[::]:50051')
        server.start()
        print("STARTED GRPC SERVER")
    except:
        print("GRPC Server Exception!")

    global throttle_left
    global throttle_right
    global throttle_back_left
    global throttle_back_right
    while True:
        sleep(.01)
        with lock:
            control_thread.motor0.velocity_goal = throttle_right * -1
            control_thread.motor1.velocity_goal = throttle_left * -1
            #control_thread.motor2.velocity_goal = throttle_back_right
            #control_thread.motor3.velocity_goal = -throttle_back_left

        pass
    e.set()



class Exchange(rover_pb2_grpc.ExchangeServicer):

  def SendControl(self, request, context):
      global lock
      with lock:
          try:
              global throttle_left
              global throttle_right
              global throttle_back_left
              global throttle_back_right

              #print("ControlService")
              #print(dir(request.rpm_command))

              throttle_right = request.rpm_command.fr
              throttle_left = request.rpm_command.fl
              throttle_back_right = request.rpm_command.br
              throttle_back_left = request.rpm_command.bl
              message = rover_pb2.Status(rpm=33)
             # print("MADE MESSAGE")
              return message
          except:
              print("Unexpected proto error: %r", sys.exc_info())


# def test():
#     server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
#     rover_pb2_grpc.add_ExchangeServicer_to_server(
#     Exchange(), server)
#     server.add_insecure_port('[::]:50051')
#     server.start()
#     while True:
#         sleep(10)
#         pass


class ControlThread(threading.Thread):

    def __init__(self, name, lock, event, vesc):
        threading.Thread.__init__(self)
        self.name = name
        self.lock = lock
        self.event = event
        self.vesc = vesc
        self.motor0 = Motor(vesc, 0)
        self.motor1 = Motor(vesc, 1)
        #self.motor2 = Motor(vesc, 2)
        #self.motor3 = Motor(vesc, 3)

    def run(self):
        print("{} started!".format(self.getName()))

        start_time = time()

        _TIMESTEP = 0.001
        _RENDERESTEP = .05

        tick = time()
        rendertick = tick
        #s = 0

        motors = [self.motor0, self.motor1]#, self.motor2, self.motor3]

        for motor in motors:
            print("Zero motor %d" % motor.canId)
            motor.set_current(0)

        while not self.event.isSet():
            self.lock.acquire()
            clock = time()
            if clock > tick:
                #print("Clock tick time")
                for _ in motors:
                    #print("process motors")
                    self.vesc.process_packet(motors)
                for motor in motors:
                    #print("Tick motors")
                    motor.tick_velocity(_TIMESTEP + clock-tick)
                    motor.update_values(_TIMESTEP, clock-tick)
                print(clock-tick)
                tick = _TIMESTEP + time()
            if clock > rendertick:
                #print("Motor0 Velocity: %r, Motor1 Velocity %r" % (int(self.motor0.velocity_feedback), int(self.motor1.velocity_feedback)))
                rendertick += _RENDERESTEP
            self.lock.release()
        for motor in motors:
            motor.disable()


class Motor:
    def __init__(self, vesc, canId):
        self.velocity_command = 0
        self.velocity_feedback = 0
        self.position = 0
        self.acceleration = 0
        self.velocity_goal = 0
        self.vesc = vesc
        self.canId = canId
        self.errors = [0] * _NUM_ERRORS_TO_AVERAGE
        self.last_error = 0

    def update_values(self, interval, overrun):
        error =  self.velocity_command - self.velocity_feedback


        self.errors.insert(0, error)
        self.errors.pop()

        error_diffs = [i-j for i, j in zip(self.errors[:-1], self.errors[1:])]
        average_error_diffs = 0
        for e in error_diffs:
            average_error_diffs += e
        average_error_diffs /= len(error_diffs)

        #print("Velocity Command %r, velocity_feedback %r, error %r" % (self.velocity_command, self.velocity_feedback, average_error_diffs))
        #print(self.errors)


        d_comp = interval/(interval+overrun)

        current_command = error * P_SCALAR + D_SCALAR * average_error_diffs * d_comp

        self.last_error = error

        if (current_command * np.sign(self.velocity_command)) > 0:
            brake = False
            if current_command > MAX_CURRENT:
                current_command = MAX_CURRENT
            elif current_command < -MAX_CURRENT:
                current_command = -MAX_CURRENT
        else:
            brake = True
            if current_command > MAX_BRAKE_CURRENT:
                current_command = MAX_BRAKE_CURRENT
            elif current_command < -MAX_BRAKE_CURRENT:
                current_command = -MAX_BRAKE_CURRENT

        self.set_current(current_command, brake)

    def set_current(self, current_command, brake=True):
        self.vesc.set_motor_current(current_command, self.canId, brake)

    def tick_velocity(self, tick_length):
        if self.velocity_command != self.velocity_goal:
            # Increment by acceleration * tick_length with the appropriate sign
            increment = self.acceleration * tick_length * np.sign(self.velocity_goal-self.velocity_command) # * np.sign(self.velocity_goal)
            #print("velocity %d, velocity setpoint %f, increment %f, position %g" % (int(self.velocity*1000), self.velocity_setpoint, increment, self.position))
            self.velocity_command += increment
        self.tick_position(tick_length)

    def tick_position(self, tick_length):
        self.position += self.velocity_command * tick_length

    def disable(self):
        self.velocity_command = 0
        self.position = 0
        self.acceleration = 0
        self.velocity_goal = 0
        self.set_current(-0.001, brake=True)
        print('DISABLE')



def print_spaces(num_spaces):
    print(' ' * num_spaces + '.')

if __name__ == "__main__":
    mp.set_start_method('fork')
    #test()
    e = threading.Event()
    try:
        main(e, sys.argv)
    except KeyboardInterrupt:
        e.set()
        print('EXIT')
        sleep(0.1)



def launchTarget(argv):
    #test()
    e = threading.Event()
    try:
        main(e, [0, argv])
    except KeyboardInterrupt:
        e.set()
        print('EXIT')
        sleep(0.1)
