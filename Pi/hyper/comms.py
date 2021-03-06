from RPi import GPIO
from enum import Enum
import serial


class WriteDir(Enum):
    EXTEND = 2
    NEUTRAL = 0
    RETRACT = 1


class CommPort:
    def __init__(self):
        self.ser = serial.Serial(port="/dev/ttyACM0", baudrate=115200, parity=serial.PARITY_NONE,
                                 stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS)
        self.ser.isOpen()

        GPIO.setmode(GPIO.BCM)

        GPIO.setup(0, GPIO.OUT, initial=GPIO.LOW)  # start cmd
        GPIO.setup(23, GPIO.OUT, initial=GPIO.LOW)  # cmd type
        GPIO.setup(24, GPIO.OUT, initial=GPIO.LOW)  # write dir 0
        GPIO.setup(25, GPIO.OUT, initial=GPIO.LOW)  # write dir 1
        GPIO.setup(1, GPIO.IN)  # finish cmd

        GPIO.setup(5, GPIO.OUT, initial=GPIO.LOW)  # id pin 0
        GPIO.setup(12, GPIO.OUT, initial=GPIO.LOW)  # id pin 1
        GPIO.setup(13, GPIO.OUT, initial=GPIO.LOW)  # id pin 2
        GPIO.setup(16, GPIO.OUT, initial=GPIO.LOW)  # id pin 3
        GPIO.setup(26, GPIO.OUT, initial=GPIO.LOW)  # id pin 4
        print("comms initialized")

    def __del__(self):
        self.ser.close()
        GPIO.cleanup()
        print("freed comm resources")

    def readDigital(self, sensor_id):
        self.__reset()
        self.__set_type(False)
        self.__write_dir(WriteDir.EXTEND)
        self.__write_id(sensor_id)
        self.ser.flush()
        self.__finish()
        return bool(self.ser.readline())

    def readAnalog(self, sensor_id):
        self.__reset()
        self.__set_type(False)
        self.__write_dir(WriteDir.NEUTRAL)
        self.__write_id(sensor_id)
        self.ser.flush()
        self.__finish()
        return int(self.ser.readline())

    def writeDigitalActuator(self, out_id, direction):
        self.__reset()
        self.__set_type(True)
        self.__write_id(out_id)
        self.__write_dir(direction)
        self.__finish()

    def writeDigial(self, out_id, val):
        self.__reset()
        self.__set_type(True)
        self.__write_id(out_id)
        self.__write_dir(WriteDir.FORWARD if val else WriteDir.NEUTRAL)
        self.__finish()

    def __reset(self):
        GPIO.output(0, GPIO.LOW)
        while GPIO.input(1) != GPIO.LOW:
            pass

    def __set_type(self, cmd_type):
        GPIO.output(23, GPIO.HIGH if cmd_type else GPIO.LOW)

    def __write_id(self, target_id):
        GPIO.output(5, GPIO.HIGH if (target_id & 0x1) != 0 else GPIO.LOW)
        GPIO.output(12, GPIO.HIGH if (target_id & 0x2) != 0 else GPIO.LOW)
        GPIO.output(13, GPIO.HIGH if (target_id & 0x4) != 0 else GPIO.LOW)
        GPIO.output(16, GPIO.HIGH if (target_id & 0x8) != 0 else GPIO.LOW)
        GPIO.output(26, GPIO.HIGH if (target_id & 0x10) != 0 else GPIO.LOW)

    def __write_dir(self, direction):
        if direction == WriteDir.EXTEND:
            GPIO.output(24, GPIO.HIGH)
            GPIO.output(25, GPIO.LOW)
        elif direction == WriteDir.RETRACT:
            GPIO.output(24, GPIO.LOW)
            GPIO.output(25, GPIO.HIGH)
        else:
            GPIO.output(24, GPIO.LOW)
            GPIO.output(25, GPIO.LOW)

    def __finish(self):
        GPIO.output(0, GPIO.HIGH)
        while GPIO.input(1) != GPIO.HIGH:
            pass


class UDPPort:
    # TODO complete this class
    def __init__(self):
        pass

    def read(self):
        pass

    def write(self):
        pass
