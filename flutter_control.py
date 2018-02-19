#!/usr/bin/env python3
import multiprocessing as mp
import grpc
import rover_pb2_grpc
import rover_pb2
import serial
import re
import time


MAX_VELOCITY = 24000

REGEX_PATTERN = """Steer: (0[xX][0-9a-fA-F]+), Throttle: (0[xX][0-9a-fA-F]+)"""
_READ_ERROR_LIMIT = 3

def main():

    # Wait for other modules to come online.
    time.sleep(1)

    read_errors = 0

    steering_initial_val = None
    throttle_initial_val = None

    channel = grpc.insecure_channel('localhost:50051')
    stub = rover_pb2_grpc.ExchangeStub(channel)

    while True:
        ser = serial.Serial('/dev/ttyACM0', timeout=0.1)  # open serial port
        line = None
        try:
            ser.write(bytes('-', 'utf-8'))
            line = ser.readline()
            if not line:
                read_errors += 1
                # Send this the first few errors, then stop.
                # Keeps the module quiet when all is normal,
                # so bluetooth control can be used.
                if read_errors < _READ_ERROR_LIMIT:
                    stop_all_motors(stub)
            else:
                read_errors = 0
        except:
            stop_all_motors(stub)

        matched_values = re.search(REGEX_PATTERN, str(line))
        if matched_values:
            steering = int(matched_values.group(1), 16)
            throttle = int(matched_values.group(2), 16)

            if steering_initial_val is None:
                steering_initial_val = steering
                throttle_initial_val = throttle
            # print("Got Steering %d and Throttle %d"%(steering, throttle))

            steering -= steering_initial_val
            throttle -= throttle_initial_val

            if throttle < 0:
                throttle *= 0.2

            throttle *= -140
            steering *= -0.25


            send_value(stub, steering, throttle)
        ser.reset_input_buffer()


def stop_all_motors(stub):
    print("STOP ALL MOTORS")
    send_value(stub, 0, 0)
    time.sleep(0.1)
    send_value(stub, 0, 0)
    time.sleep(0.1)
    send_value(stub, 0, 0)

def send_value(stub, steering, throttle):
    if throttle > 50:
        steering_multiplier = 10000
    else:
        steering_multiplier = -10000
    fr_rpm = throttle - (steering_multiplier * steering) / 100.0
    fl_rpm = throttle + (steering_multiplier * steering) / 100.0
    br_rpm = fr_rpm
    bl_rpm = fl_rpm
    fl_rpm *= -1
    br_rpm *= -1

    fr_rpm = min(MAX_VELOCITY, fr_rpm)
    fl_rpm = min(MAX_VELOCITY, fl_rpm)
    br_rpm = min(MAX_VELOCITY, br_rpm)
    bl_rpm = min(MAX_VELOCITY, bl_rpm)

    rpm = rover_pb2.RPM(
        fr = int(fr_rpm),
        fl = int(fl_rpm),
        br = int(br_rpm),
        bl = int(bl_rpm)
      )
    try:
        status = stub.SendControl(rover_pb2.Control(rpm_command=rpm))
    except:
        print("GRPC Exception in Flutter Control")

if __name__ == "__main__":
    main()
