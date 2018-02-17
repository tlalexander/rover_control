#!/usr/bin/env python3
import multiprocessing as mp
import grpc
import rover_pb2_grpc
import rover_pb2
import serial
import re


REGEX_PATTERN = """Steer: (0[xX][0-9a-fA-F]+), Throttle: (0[xX][0-9a-fA-F]+)"""

def main():

    steering_initial_val = None
    throttle_initial_val = None

    channel = grpc.insecure_channel('localhost:50051')
    stub = rover_pb2_grpc.ExchangeStub(channel)

    while True:
        ser = serial.Serial('/dev/ttyACM0')  # open serial port
        line = ser.readline()
        matched_values = re.search(REGEX_PATTERN, str(line))
        if matched_values:
            steering = int(matched_values.group(1), 16)
            throttle = int(matched_values.group(2), 16)

            if steering_initial_val is None:
                steering_initial_val = steering
                throttle_initial_val = throttle

            #print("Got Steering %d and Throttle %d"%(steering, throttle))

            steering -= steering_initial_val
            throttle -= throttle_initial_val
            throttle *= -156
            steering *= -0.25

            fr_rpm = throttle - (throttle * steering) / 100.0
            fl_rpm = throttle + (throttle * steering) / 100.0
            br_rpm = fr_rpm
            bl_rpm = fl_rpm
            fl_rpm *= -1
            br_rpm *= -1

            rpm = rover_pb2.RPM(
                fr = int(fr_rpm),
                fl = int(fl_rpm),
                br = int(br_rpm),
                bl = int(bl_rpm)
              )
            status = stub.SendControl(rover_pb2.Control(rpm_command=rpm))

if __name__ == "__main__":
    main()
