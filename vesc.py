from enum import Enum
import socket
import struct
import sys
import binascii
from time import sleep
# CAN frame packing/unpacking (see `struct can_frame` in <linux/can.h>)
can_frame_fmt = "=IB3x8s"


class VescCommand(Enum):
    COMM_FW_VERSION = 0x00
    COMM_JUMP_TO_BOOTLOADER = 0x01
    COMM_ERASE_NEW_APP = 0x02
    COMM_WRITE_NEW_APP_DATA = 0x03
    COMM_GET_VALUES = 0x04
    COMM_SET_DUTY = 0x05
    COMM_SET_CURRENT = 0x06
    COMM_SET_CURRENT_BRAKE = 0x07
    COMM_SET_RPM = 0x08
    CAN_PACKET_SEND_ROVER_DETAILS = 0x09
    COMM_SET_HANDBRAKE = 0x0A
    COMM_SET_DETECT = 0x0B
    COMM_SET_SERVO_POS = 0x0C
    COMM_SET_MCCONF = 0x0D
    COMM_GET_MCCONF = 0x0E
    COMM_GET_MCCONF_DEFAULT = 0x0F
    COMM_SET_APPCONF = 0x10
    COMM_GET_APPCONF = 0x11
    COMM_GET_APPCONF_DEFAULT = 0x12
    COMM_SAMPLE_PRINT = 0x13
    COMM_TERMINAL_CMD = 0x14
    COMM_PRINT = 0x15
    COMM_ROTOR_POSITION = 0x16
    COMM_EXPERIMENT_SAMPLE = 0x17
    COMM_DETECT_MOTOR_PARAM = 0x18
    COMM_DETECT_MOTOR_R_L = 0x19
    COMM_DETECT_MOTOR_FLUX_LINKAGE = 0x1A
    COMM_DETECT_ENCODER = 0x1B
    COMM_DETECT_HALL_FOC = 0x1C
    COMM_REBOOT = 0x1D
    COMM_ALIVE = 0x1E
    COMM_GET_DECODED_PPM = 0x1F
    COMM_GET_DECODED_ADC = 0x20
    COMM_GET_DECODED_CHUK = 0x21
    COMM_FORWARD_CAN = 0x22
    COMM_SET_CHUCK_DATA = 0x23
    COMM_CUSTOM_APP_DATA = 0x24
    COMM_NRF_START_PAIRING = 0x25
    COMM_ROTOR_POSITION_CUMULATIVE = 0x26
    COMM_SET_CURRENT_GET_POSITION = 0x27
    COMM_SEND_ROVER_DETAILS = 0x28


class CanCommand(Enum):
    SET_DUTY = 0x00
    SET_CURRENT = 0x01
    SET_CURRENT_BRAKE = 0x02
    SET_RPM = 0x03
    #SET_POS = 0x04
    FILL_RX_BUFFER = 0x05
    FILL_RX_BUFFER_LONG = 0x06
    PROCESS_RX_BUFFER = 0x07
    PROCESS_SHORT_BUFFER = 0x08
    STATUS = 0x09
    SET_CURRENT_REL = 0x10
    SET_CURRENT_BRAKE_REL = 0x11
    SEND_ROVER_DETAILS = 0x04


_DEBUG_FRAME = False


class CanVesc():

    def __init__(self, interface):
        self.sock = socket.socket(socket.AF_CAN, socket.SOCK_RAW, socket.CAN_RAW)
        try:
            self.sock.bind((interface,))
            self.open = True
        except OSError as err:
                print("OS error: {0}: %r".format(err) % interface)
                self.open = False
        self.data_buffer = []

    def build_can_frame(self, command, device_id, data):
        # VESC commands are 0-9
        can_id = (command.value << 8) | device_id
        # I don't know why yet, but the VESC has an extra bit high in the ID.
        can_id = 0x80000000 | can_id
        can_dlc = len(data)  # Set the CAN Data Length Code
        data = data.ljust(8, b'\x00')
        return struct.pack(can_frame_fmt, can_id, can_dlc, data)

    def dissect_can_frame(self, frame):
        can_id, can_dlc, data = struct.unpack(can_frame_fmt, frame)
        return (can_id, can_dlc, data[:can_dlc])

    def set_motor_rpm(self, erpm, device_id):
        try:
            data = bytearray(erpm.to_bytes(7, byteorder='big'))
            data[0] = 0x01  # "rx_buffer_last_id" in VESC firmware
            data[1] = 0x00  # "commands_send" in VESC firmware
            data[2] = VescCommand.COMM_SET_RPM.value
            frame = self.build_can_frame(CanCommand.PROCESS_SHORT_BUFFER, device_id, data)
            print(frame) if _DEBUG_FRAME else None
            self.sock.send(frame)
        except socket.error:
            print('Error sending CAN frame') if _DEBUG_FRAME else None

    def set_motor_current(self, current_amps, device_id, brake=True):
        try:
            if brake:
                command = CanCommand.SET_CURRENT_BRAKE
            else:
                command = CanCommand.SET_CURRENT
            data = bytearray(struct.pack('>i', int(current_amps*1000)))
            frame = self.build_can_frame(command, device_id, data)
            print(frame) if _DEBUG_FRAME else None
            self.sock.send(frame)
        except socket.error:
            print('Error sending CAN frame') if _DEBUG_FRAME else None

    def process_packet(self, motors):
        if not self.open:
            #print("VESC NOT OPEN")
            return
        packet, addr = self.sock.recvfrom(16)
        #print(packet)
        canid, dlc, data = self.dissect_can_frame(packet)
        can_command = canid>>8 & 0xFF
        sender_id = canid & 0xFF
        for m in motors:
          if m.canId == sender_id:
            motor = m
        if not motor:
            return
        #print(sender_id)
        msg1 = 'Received: can_id=%x, can_dlc=%x, data=%s' % (canid, dlc, data)
        msg2 = "%r" % packet
    #
        #sys.stdout.write("%s\n" % msg1)
        #sys.stdout.write("%s\n" % msg2)
        #sys.stdout.flush()
        #angle = struct.unpack('>i', data[3:])[0]
        #print(angle)
        #self.position = angle
        #print(canid)
        if can_command == CanCommand.SEND_ROVER_DETAILS.value:
            #print('Recieved Rover Packet: %r' % data)
            motor.position = struct.unpack('>i', data[0:4])[0]
            motor.velocity_feedback = struct.unpack('>f', data[4:])[0]
        if can_command == CanCommand.FILL_RX_BUFFER.value:
            for b in data[1:dlc-2]:
                self.data_buffer.append(b)
            #print(hex(can_command))
        if can_command == CanCommand.PROCESS_RX_BUFFER.value:
            #print(self.data_buffer)
            self.data_buffer = []


        if can_command == CanCommand.PROCESS_SHORT_BUFFER.value:
            if data[2] == 0x16:
                angle = struct.unpack('>i', data[3:])[0]
                #print(angle/100000.0)
                #print(' ' * (int(data[4]/2)) + '.')
                #print(packet)
            self.data_buffer.append(data[1:dlc-2])
        #print(hex(can_command))

    def packCanId(self, command, device_id):

        return can_id
