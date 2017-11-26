from time import sleep
from time import time
from vesc import CanVesc
import sys
import os
import math
import numpy as np
import threading

display_rows, display_columns = os.popen('stty size', 'r').read().split()

# Don't forget to set up CAN with:
# ip link set can0 up type can bitrate 500000


def main():
    if len(sys.argv) != 2:
          print('Provide CAN device name (can0, slcan0 etc.)')
          sys.exit(0)
    vesc = CanVesc(sys.argv[0])
    #motion_control_loop()                                # Four times...
    mythread = ControlThread(name = "MotionControlThread")  # ...Instantiate a thread and pass a unique ID to it
    mythread.start()                                   # ...Start the thread
    lock = threading.Lock()
    sleep(0.1)

    while True:
        with lock:
            if mythread.motor.position > 5:
                mythread.motor.velocity_setpoint = -1.0
            if mythread.motor.position < -5:
                mythread.motor.velocity_setpoint = 1.0

    sleep(4)
    with lock:
        mythread.motor.velocity_setpoint = -1.0
    sleep(4)
    with lock:
        mythread.motor.velocity_setpoint = 1.0


    #vesc.set_motor_rpm(1000, 0)

    #print(b'\x00\x08\x00\x80\x07\x00\x00\x00\x01\x00\x08\x00\x00\x03\xe8\x00')

# create a raw socket and bind it to the given CAN interface


class ControlThread(threading.Thread):

    def run(self):
        print("{} started!".format(self.getName()))              # "Thread-x started!"
        #sleep(1)                                      # Pretend to work for a second
        #print("{} finished!".format(self.getName()))             # "Thread-x finished!"

        cols = int(display_columns)

        start_time = time()

        _TIMESTEP = 0.001
        _RENDERESTEP = .1

        self.motor = Motor()

        self.motor.acceleration = .5
        self.motor.velocity_setpoint = 1.0
        self.motor.velocity = -1.0

        tick1 = time()
        tick2 = time()
        s = 0
        while True:
            clock = time()
            if clock > tick1:
                tick1 += _RENDERESTEP
                self.motor.plot_position(cols, 10.0)
            if clock > tick2:
                tick2 += _TIMESTEP
                self.motor.tick_velocity(_TIMESTEP)


class Motor:
    def __init__(self):
        self.velocity = 0
        self.position = 0
        self.acceleration = 0
        self.velocity_setpoint = 0


    def set_speed(self):
        print_spaces(self.velocity)

    def plot_position(self, cols, scale_factor):
        s = cols/2  +  ((cols/2) * (self.position / scale_factor))
        print_spaces(int(s))

    def tick_velocity(self, tick_length):
        if self.velocity != self.velocity_setpoint:
            increment = self.acceleration * tick_length * np.sign(self.velocity_setpoint-self.velocity)
            #print("velocity %g, velocity setpoint %f, increment %f, position %g" % (self.velocity, self.velocity_setpoint, increment, self.position))
            self.velocity += increment
        self.tick_position(tick_length)

    def tick_position(self, tick_length):
        self.position += self.velocity * tick_length



def print_spaces(num_spaces):
    print(' ' * num_spaces + '.')

if __name__ == "__main__":
    # execute only if run as a script
    main()
