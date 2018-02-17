
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



class Exchange(rover_pb2_grpc.ExchangeServicer):

  def SendControl(self, request, context):
      print("ControlService")
      print(dir(request))

      #print("GOT RPM PROTO IN MOTOR CONTROL: V1 %r, V2 %r" % (request.rpm_command.fr, request.rpm_command.fl))

      return rover_pb2.Status(
              rpm = rover_pb2.RPM(
                      fr = 33,
                      fl = 33,
                      br = 0,
                      bl = 0
                  ))

def test():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    rover_pb2_grpc.add_ExchangeServicer_to_server(
    Exchange(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    while True:
        sleep(10)
        pass



if __name__ == "__main__":
    test()
