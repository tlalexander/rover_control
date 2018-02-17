#!/usr/bin/env python3


import struct

import grpc
import rover_pb2
import rover_pb2_grpc




def main():
    channel = grpc.insecure_channel('localhost:50051')
    stub = rover_pb2_grpc.ExchangeStub(channel)

    print(dir(stub))
    rpm = rover_pb2.RPM(
        fr = 0,
        fl = 0,
        br = 0,
        bl = 0
      )
    status = stub.SendControl( rover_pb2.Control(rpm_command=rpm) )

if __name__ == '__main__':
    main()
