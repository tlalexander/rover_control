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

P_SCALAR = 1/25.0
D_SCALAR = 1/3.0

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

    while True:
        with lock:
            control_thread.motor.acceleration = 60000
            control_thread.motor.velocity_setpoint = 10000
        sleep(1)
        with lock:
            control_thread.motor.acceleration = 10000
            control_thread.motor.velocity_setpoint = 20000
        sleep(3)
        with lock:
            control_thread.motor.acceleration = 40000
            control_thread.motor.velocity_setpoint = 30000
        sleep(1)
        with lock:
            control_thread.motor.acceleration = 40000
            control_thread.motor.velocity_setpoint = 500
        sleep(1)
    with lock:
        control_thread.motor.velocity_setpoint = 0
    sleep(4)
    with lock:
        control_thread.motor.disable()
    e.set()


class ControlThread(threading.Thread):

    def __init__(self, name, lock, event, vesc):
        threading.Thread.__init__(self)
        self.name = name
        self.lock = lock
        self.event = event
        self.motor = Motor(vesc, 0)

    def run(self):
        print("{} started!".format(self.getName()))              # "Thread-x started!"
        #sleep(1)                                      # Pretend to work for a second
        #print("{} finished!".format(self.getName()))             # "Thread-x finished!"

        cols = int(display_columns)

        start_time = time()

        _TIMESTEP = 0.001
        _RENDERESTEP = .005

        tick1 = time()
        tick2 = tick1
        #s = 0

        self.motor.set_current(0)

        errors = [0]*3

        while not self.event.isSet():
            self.lock.acquire()
            clock = time()
            if clock > tick1:
                tick1 += _RENDERESTEP
                #self.motor.set_speed()
                #self.motor.plot_position(cols, 30.0)
            if clock > tick2:
                tick2 += _TIMESTEP
                self.motor.tick_velocity(_TIMESTEP)
                cf, addr = self.motor.vesc.sock.recvfrom(16)
                self.motor.vesc.process_packet(cf)
                error =  self.motor.velocity - self.motor.vesc.rpm

                errors.insert(0, error)
                errors.pop()

                error_diffs = [i-j for i, j in zip(errors[:-1], errors[1:])]
                average_errors = 0
                for e in error_diffs:
                    average_errors += e
                average_errors /= len(error_diffs)
                # print(error_diffs)

                current_command = error * P_SCALAR + D_SCALAR * average_errors
                last_error = error

                if current_command > MAX_CURRENT:
                    current_command = MAX_CURRENT
                elif current_command < -MAX_BRAKE_CURRENT:
                    current_command = -MAX_BRAKE_CURRENT

                #print(current_command)
                self.motor.set_current(current_command)

            self.lock.release()
        motor.disable()


class Motor:
    def __init__(self, vesc, canId):
        self.velocity = 0
        self.position = 0
        self.acceleration = 0
        self.velocity_setpoint = 0
        self.vesc = vesc
        self.canId = canId


    def set_current(self, current_command):
        self.vesc.set_motor_current(current_command, self.canId)

    def plot_position(self, cols, scale_factor):
        s = cols/2  +  ((cols/2) * (self.velocity / scale_factor))
        print_spaces(int(s))

    def tick_velocity(self, tick_length):
        if self.velocity != self.velocity_setpoint:
            increment = self.acceleration * tick_length * np.sign(self.velocity_setpoint-self.velocity)
            #print("velocity %d, velocity setpoint %f, increment %f, position %g" % (int(self.velocity*1000), self.velocity_setpoint, increment, self.position))
            self.velocity += increment
        self.tick_position(tick_length)

    def tick_position(self, tick_length):
        self.position += self.velocity * tick_length

    def disable(self):
        self.velocity = 0
        self.position = 0
        self.acceleration = 0
        self.velocity_setpoint = 0
        self.set_current(0)



def print_spaces(num_spaces):
    print(' ' * num_spaces + '.')

if __name__ == "__main__":
    # execute only if run as a script
    e = threading.Event()
    try:
        main(e)
    except KeyboardInterrupt:
        e.set()
