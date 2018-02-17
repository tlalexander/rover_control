
# This script starts up the rover software.
import os
import sys
import subprocess
import multiprocessing as mp
import motors
import advertise
import gatt
import flutter_control
from time import sleep


_CAN_PORT = "can0"

_CAN_SETUP_COMMAND = "ip link set %s up type can bitrate 1000000" % _CAN_PORT


_RESET_BLUETOOTH_COMMAND = "/home/pi/rover/restart_bluetooth.sh"


def main():
    # return
    mp.set_start_method('fork')

    #sleep(10)

    # Set up CAN
    subprocess.call(_CAN_SETUP_COMMAND, shell=True)

    # Reset Bluetooth
    subprocess.call(_RESET_BLUETOOTH_COMMAND, shell=True)

    sleep(1)

    # Launch Rover App (Motor Control)
    p1 = mp.Process(target=motors.launchTarget, args=(_CAN_PORT, ))
    p1.start()
    #p1.join()

    # Launch Bluetooth Control Program
    p2 = mp.Process(target=gatt.main)
    p2.start()
    #p2.join()

    # Launch Bluetooth Channel Advertisement Program
    p3 = mp.Process(target=advertise.main)
    p3.start()
    #p3.join()

    # Launch Flutter Remote Control Program
    p4 = mp.Process(target=flutter_control.main)
    p4.start()
    #p4.join()

if __name__ == '__main__':
    main()
