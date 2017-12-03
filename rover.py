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

# Don't forget to set up CAN with:
# ip link set can0 up type can bitrate 500000


def main(e):
    if len(sys.argv) != 2:
          print('Provide CAN device name (can0, slcan0 etc.)')
          sys.exit(0)
    vesc = CanVesc(sys.argv[1])

    test_frame = bytearray([0x01,0x08,0x00,0x80,0x03,0x00,0x00,0x00,0x00,0x00,0x04,0x00,0x00,0x00,0x00,0x00])

    #vesc.sock.send(test_frame)

    #vesc.set_motor_current(0, 0)

    lasttime = time()


    vesc.set_motor_current(0, 0)
    set_val = 0

    desired_rpm = 1000

    MAX_CURRENT = 35
    MAX_BRAKE_CURRENT = 5

    P_SCALAR = 1/25.0

    while True:



        # lasttime = time()
        cf, addr = vesc.sock.recvfrom(16)
        #
        #
        # print((time()-lasttime)*1e6)
        # lasttime = time()
        #
        vesc.process_packet(cf)

        #vesc.rpm = 2100

        error =  desired_rpm - vesc.rpm

        set_val = error * P_SCALAR

        #print(error)

        if set_val > MAX_CURRENT:
            set_val = MAX_CURRENT
        elif set_val < -MAX_BRAKE_CURRENT:
            set_val = -MAX_BRAKE_CURRENT
        # elif set_val < 0:
        #     set_val = 0

        print(set_val)





        vesc.set_motor_current(set_val, 0)
        sleep(0.001)

        # if time() > lasttime + 2:
        #     lasttime = time()
        #     if desired_rpm == 500:
        #         desired_rpm = 100
        #     else:
        #         desired_rpm = 500


        #print(vesc.rpm)

        #sleep(1)



    # print("raw frame:")
        #print(' 0x'.join('{:02X}'.format(a) for a in cf))
        # data_string = "[ "
        # for b in cf:
        #     data_string += '0x{:02X},'.format(b)
        # data_string += "]\n"
        # sys.stdout.write(data_string)
        # sys.stdout.flush()
        #print(data_string)

    # vesc.set_motor_rpm(1000, 1)
    # sleep(2)
    # vesc.set_motor_rpm(0, 1)
    #
    # sys.exit(0)


    lock = threading.Lock()

    control_thread = ControlThread(name = "MotionControlThread", lock=lock, event=e, vesc=vesc)  # ...Instantiate a thread and pass a unique ID to it
    control_thread.daemon = True
    control_thread.start()
    sleep(0.5)

    # while True:
    #     with lock:
    #         if mythread.motor.position > 5:
    #             mythread.motor.velocity_setpoint = -1.0
    #         if mythread.motor.position < -5:
    #             mythread.motor.velocity_setpoint = 1.0

    while True:
        with lock:
            control_thread.motor.acceleration = 5
            control_thread.motor.velocity_setpoint = 1.0
        sleep(2)
        with lock:
            control_thread.motor.acceleration = 20
            control_thread.motor.velocity_setpoint = 5.0
        sleep(2)
    with lock:
        control_thread.motor.velocity_setpoint = 0
    sleep(4)
    with lock:
        control_thread.motor.disable()
    e.set()


    #vesc.set_motor_rpm(1000, 0)

    #print(b'\x00\x08\x00\x80\x07\x00\x00\x00\x01\x00\x08\x00\x00\x03\xe8\x00')

# create a raw socket and bind it to the given CAN interface


class ControlThread(threading.Thread):

    def __init__(self, name, lock, event, vesc):
        threading.Thread.__init__(self)
        self.name = name
        self.lock = lock
        self.event = event
        self.motor = Motor(vesc, 1)

    def run(self):
        print("{} started!".format(self.getName()))              # "Thread-x started!"
        #sleep(1)                                      # Pretend to work for a second
        #print("{} finished!".format(self.getName()))             # "Thread-x finished!"

        cols = int(display_columns)

        start_time = time()

        _TIMESTEP = 0.001
        _RENDERESTEP = .005

        tick1 = time()
        tick2 = time()
        s = 0
        while not self.event.isSet():
            self.lock.acquire()
            clock = time()
            if clock > tick1:
                tick1 += _RENDERESTEP
                self.motor.set_speed()
                self.motor.plot_position(cols, 30.0)
            if clock > tick2:
                tick2 += _TIMESTEP
                self.motor.tick_velocity(_TIMESTEP)
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


    def set_speed(self):
        self.vesc.set_motor_rpm(int(self.velocity*1000), self.canId)

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
        self.set_speed()



def print_spaces(num_spaces):
    print(' ' * num_spaces + '.')

if __name__ == "__main__":
    # execute only if run as a script
    e = threading.Event()
    try:
        main(e)
    except KeyboardInterrupt:
        e.set()
