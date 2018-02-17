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
    COMM_SET_POS = 0x09
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


class CanCommand(Enum):
    SET_DUTY = 0x00
    SET_CURRENT = 0x01
    SET_CURRENT_BRAKE = 0x02
    SET_RPM = 0x03
    SET_POS = 0x04
    FILL_RX_BUFFER = 0x05
    FILL_RX_BUFFER_LONG = 0x06
    PROCESS_RX_BUFFER = 0x07
    PROCESS_SHORT_BUFFER = 0x08
    PACKET_STATUS = 0x09


_DEBUG_FRAME = True


class CanVesc:

    def __init__(self, interface):
        self.sock = socket.socket(socket.AF_CAN, socket.SOCK_RAW, socket.CAN_RAW)
        try:
            self.sock.bind((interface,))
        except OSError as err:
                print("OS error: {0}: %r".format(err) % interface)

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
            # send erpm command
            data = bytearray(erpm.to_bytes(7, byteorder='big'))
            data[0] = 0x01  # "rx_buffer_last_id" in VESC firmware
            data[1] = 0x00  # "commands_send" in VESC firmware
            data[2] = VescCommand.COMM_SET_RPM.value
            frame = self.build_can_frame(CanCommand.PROCESS_SHORT_BUFFER, device_id, data)
            print(frame) if _DEBUG_FRAME else None
            self.sock.send(frame)
        except socket.error:
            print('Error sending CAN frame')

    def packCanId(self, command, device_id):

        return can_id
