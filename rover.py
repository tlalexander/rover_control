from time import sleep
from time import time
from vesc import CanVesc
import sys
import os
import math
import numpy as np
import threading

end_program = False

display_rows, display_columns = os.popen('stty size', 'r').read().split()

MAX_CURRENT = 35
MAX_BRAKE_CURRENT = 5

P_SCALAR = 1/15.0
D_SCALAR = 1/3.0

_NUM_ERRORS_TO_AVERAGE = 3

# Don't forget to set up CAN with:
# ip link set can0 up type can bitrate 1000000

def main(e):
    if len(sys.argv) != 2:
          print('Provide CAN device name (can0, slcan0 etc.)')
          sys.exit(0)
    vesc = CanVesc(sys.argv[1])

    lasttime = time()


    lock = threading.Lock()

    control_thread = ControlThread(name = "MotionControlThread", lock=lock, event=e, vesc=vesc)  # ...Instantiate a thread and pass a unique ID to it
    control_thread.daemon = True
    control_thread.start()
    sleep(0.5)

    SPEED = 500
    while True:
        with lock:
            control_thread.motor1.acceleration = 1500
            control_thread.motor0.acceleration = 1500
            control_thread.motor1.velocity_goal = -SPEED
            control_thread.motor0.velocity_goal = SPEED
        sleep(2)
        with lock:
            control_thread.motor1.velocity_goal = SPEED
            control_thread.motor0.velocity_goal = -SPEED
        sleep(2)
        # with lock:
        #     control_thread.motor1.velocity_goal = -1000
        #     control_thread.motor0.velocity_goal = 500
        # sleep(0.5)
        # with lock:
        #     control_thread.motor.acceleration = 40000
        #     control_thread.motor.velocity_setpoint = 30000
        # sleep(1)
        # with lock:
        #     control_thread.motor.acceleration = 40000
        #     control_thread.motor.velocity_setpoint = 500
        # sleep(1)
    with lock:
        control_thread.motor0.velocity_goal = 0
    sleep(4)
    with lock:
        control_thread.motor0.disable()
    e.set()


class ControlThread(threading.Thread):

    def __init__(self, name, lock, event, vesc):
        threading.Thread.__init__(self)
        self.name = name
        self.lock = lock
        self.event = event
        self.vesc = vesc
        self.motor0 = Motor(vesc, 0)
        self.motor1 = Motor(vesc, 1)

    def run(self):
        print("{} started!".format(self.getName()))

        cols = int(display_columns)

        start_time = time()

        _TIMESTEP = 0.001
        _RENDERESTEP = .05

        tick = time()
        rendertick = tick
        #s = 0

        self.motor0.set_current(0)
        self.motor1.set_current(0)

        while not self.event.isSet():
            self.lock.acquire()
            clock = time()
            if clock > tick:
                self.vesc.process_packet([self.motor0, self.motor1])
                self.vesc.process_packet([self.motor0, self.motor1])
                self.motor0.tick_velocity(_TIMESTEP + clock-tick)
                self.motor0.update_values(_TIMESTEP, clock-tick)
                self.motor1.tick_velocity(_TIMESTEP + clock-tick)
                self.motor1.update_values(_TIMESTEP, clock-tick)
                tick += _TIMESTEP
            if clock > rendertick:
                print("Motor0 Velocity: %r, Motor1 Velocity %r" % (int(self.motor0.velocity_feedback), int(self.motor1.velocity_feedback)))
                rendertick += _RENDERESTEP
            self.lock.release()
        self.motor0.disable()
        self.motor1.disable()


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

    def plot_position(self, cols, scale_factor):
        s = cols/2  +  ((cols/2) * (self.velocity_command / scale_factor))
        print_spaces(int(s))

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
    # execute only if run as a script
    e = threading.Event()
    try:
        main(e)
    except KeyboardInterrupt:
        e.set()
        print('EXIT')
        sleep(0.1)
