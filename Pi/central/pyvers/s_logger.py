#!/usr/bin/env python3
# Using python 3

# set up i2c on the pi
# first, un-blacklist i2c
# next, add the i2c modules to the loaded kernel modules
# afterthat, install i2c-tools and reboot
# finally, run i2cdetect

# install smbus2

# change i2c baudrate to 50kHz, if using i2c

import time
import socket
import sys

import Rpi.GPIO

import pod_periph

# Emergency brake
EBRAKE_ACTU_L_FORW = 0
EBRAKE_ACTU_L_BACK = 0
EBRAKE_ACTU_R_FORW = 0
EBRAKE_ACTU_R_BACK = 0
EBRAKE_POTENT_L = 0
EBRAKE_POTENT_R = 0
EBRAKE_EMAG_L = 0
EBRAKE_EMAG_R = 0

# Main brake
MAINB_ACTU_L_FORW = 0
MAINB_ACTU_L_BACK = 0
MAINB_ACTU_R_FORW = 0
MAINB_ACTU_R_BACK = 0

# Actuators
ACTU_FORW = []
ACTU_BACK = []

# Record values
PROX_LF = 0
PROX_RF = 0

# Report on velocity + acceleration
# Calc distance traveled
IMU_BUS = 1
IMU_CH = 0x28

# Actuators
EXT_FREE = 0
RET_FREE = 1
EXT_TIME = 2
RET_TIME = 3
EXT_DIST = 4
RET_DIST = 5
EXT_TARG = 6
RET_TARG = 7
HALT = 8

# Electromagnet
ON = 0
OFF = 1

# Target states
EBRAKE_ACTU_L_STATE = [HALT, None]
EBRAKE_ACTU_R_STATE = [HALT, None]
MAINB_ACTU_L_STATE = [HALT, None]
MAINB_ACTU_R_STATE = [HALT, None]
EBRAKE_EMAG_L_STATE = [OFF]
EBRAKE_EMAG_R_STATE = [OFF]

ACTU_STATE = []  # 2d list

cli = pod_periph.Client()

l_potentiometer = pod_periph.AnalogSensor("emergencypotent_left", EBRAKE_POTENT_L)
r_potentiometer = pod_periph.AnalogSensor("emergencypotent_right", EBRAKE_POTENT_R)
imu = pod_periph.IMUSensor("imu", IMU_CH)

sensor_ports = [
    imu,
    pod_periph.AnalogSensor("prox0", PROX_LF),
    pod_periph.AnalogSensor("prox1", PROX_RF),
    l_potentiometer,
    r_potentiometer
]


def update_sensors():
    for sensor in sensor_ports:
        sensor.update_sensor(cli)


def log(outfile):
    for sensor in sensor_ports:
        outfile.write(sensor.data_string())


def actuator_state(state: int, data: [], actu_ex_pin: int, actu_re_pin: int, r_p: pod_periph.AnalogSensor = None, l_p: pod_periph.AnalogSensor = None):
    if state == EXT_FREE:
        Rpi.GPIO.output(actu_re_pin, Rpi.GPIO.LOW)
        Rpi.GPIO.output(actu_ex_pin, Rpi.GPIO.HIGH)
    elif state == RET_FREE:
        Rpi.GPIO.output(actu_ex_pin, Rpi.GPIO.LOW)
        Rpi.GPIO.output(actu_re_pin, Rpi.GPIO.HIGH)
    elif state == EXT_TIME:
        Rpi.GPIO.output(actu_re_pin, Rpi.GPIO.LOW)
        if time.time() < data[0]:
            Rpi.GPIO.output(actu_ex_pin, Rpi.GPIO.HIGH)
        else:
            Rpi.GPIO.output(actu_ex_pin, Rpi.GPIO.LOW)
    elif state == RET_TIME:
        Rpi.GPIO.output(actu_ex_pin, Rpi.GPIO.LOW)
        if time.time() < data[0]:
            Rpi.GPIO.output(actu_re_pin, Rpi.GPIO.HIGH)
        else:
            Rpi.GPIO.output(actu_re_pin, Rpi.GPIO.LOW)
    elif state == EXT_DIST:
        Rpi.GPIO.output(actu_re_pin, Rpi.GPIO.LOW)
        if r_p is not None:
            if r_p.value[0] < data[0] + data[1] or data is None:
                Rpi.GPIO.output(actu_ex_pin, Rpi.GPIO.LOW)
            else:
                Rpi.GPIO.output(actu_ex_pin, Rpi.GPIO.LOW)
        else:
            Rpi.GPIO.output(actu_ex_pin, Rpi.GPIO.LOW)
    elif state == RET_DIST:
        Rpi.GPIO.output(actu_ex_pin, Rpi.GPIO.LOW)
        if r_p is not None:
            if r_p.value[0] > data[0] + data[1]:
                Rpi.GPIO.output(actu_ex_pin, Rpi.GPIO.LOW)
            else:
                Rpi.GPIO.output(actu_ex_pin, Rpi.GPIO.LOW)
        else:
            Rpi.GPIO.output(actu_ex_pin, Rpi.GPIO.LOW)
    elif state == EXT_TARG:
        Rpi.GPIO.output(actu_ex_pin, Rpi.GPIO.LOW)
        if r_p is not None:
            if r_p.value[0] > data[0]:
                Rpi.GPIO.output(actu_ex_pin, Rpi.GPIO.LOW)
            else:
                Rpi.GPIO.output(actu_ex_pin, Rpi.GPIO.LOW)
        else:
            Rpi.GPIO.output(actu_ex_pin, Rpi.GPIO.LOW)
    elif state == RET_TARG:
        Rpi.GPIO.output(actu_ex_pin, Rpi.GPIO.LOW)
        if r_p is not None:
            if r_p.value[0] == data[0]:
                Rpi.GPIO.output(actu_ex_pin, Rpi.GPIO.LOW)
            else:
                Rpi.GPIO.output(actu_ex_pin, Rpi.GPIO.LOW)
        else:
            Rpi.GPIO.output(actu_ex_pin, Rpi.GPIO.LOW)
    elif state == HALT:
        Rpi.GPIO.output(actu_ex_pin, Rpi.GPIO.LOW)
        Rpi.GPIO.output(actu_ex_pin, Rpi.GPIO.LOW)


def update_actuators():
    if EBRAKE_EMAG_L_STATE == OFF:
        Rpi.GPIO.output(EBRAKE_EMAG_L, Rpi.GPIO.LOW)
    elif EBRAKE_EMAG_L_STATE == ON:
        Rpi.GPIO.output(EBRAKE_EMAG_L, Rpi.GPIO.HIGH)
    if EBRAKE_EMAG_R_STATE == OFF:
        Rpi.GPIO.output(EBRAKE_EMAG_R, Rpi.GPIO.LOW)
    elif EBRAKE_EMAG_R_STATE == ON:
        Rpi.GPIO.output(EBRAKE_EMAG_R, Rpi.GPIO.HIGH)

    actuator_state(EBRAKE_ACTU_L_STATE[0], EBRAKE_ACTU_L_STATE[1], EBRAKE_ACTU_L_FORW, EBRAKE_ACTU_L_BACK, r_potentiometer, l_potentiometer)
    actuator_state(EBRAKE_ACTU_R_STATE[0], EBRAKE_ACTU_R_STATE[1], EBRAKE_ACTU_R_FORW, EBRAKE_ACTU_R_BACK, r_potentiometer, l_potentiometer)
    actuator_state(MAINB_ACTU_L_STATE[0], MAINB_ACTU_L_STATE[1], MAINB_ACTU_L_FORW, MAINB_ACTU_L_BACK)
    actuator_state(MAINB_ACTU_R_STATE[0], MAINB_ACTU_R_STATE[1], MAINB_ACTU_R_FORW, MAINB_ACTU_R_BACK)


def mag(vec: (int, int, int)):
    return vec[0] * vec[0] + vec[1] * vec[1] + vec[2] * vec[2]


def send(s: socket.socket):
    """
    Updates GUI.
    :param s: socket to send data over

    List of data to be sent to GUI, numbers must be in string format in the following order...
        [ E-Brake Potentiometer, Height, Velocity, Acceleration, Distance Traveled ]
    """

    payload = " ".join([l_potentiometer.value, (sensor_ports[1].value + sensor_ports[2].value)/2, mag(imu.value[0]),
                        mag(imu.value[4]), mag(imu.value[1])])
    s.sendto(payload.encode(), (IP_ADDRESS, PORT))


def recv(s: socket.socket):
    """
    Expecting commands like <Target name> <value>

    Target names:
        EBRAKE_ACTU
        EBRAKE_ACTU_L
        EBRAKE_ACTU_R
        EBRAKE_EMAG
        EBRAKE_EMAG_L
        EBRAKE_EMAG_R
        MAINB_ACTU
        MAINB_ACTU_L
        MAINB_ACTU_R

    value:
        for actuators:
            0 = HALT
            1 = EXTEND
            2 = RETRACT
        for electromag:
            0 = OFF
            1 = ON

    :param s: ssocket to send through
    """
    while True:
        try:
            (data, addr) = s.recvfrom(2048)
            command = data.decode()
            command = command.split()
            if len(command) >= 2:
                target = command[0]
                movement = command[1]
                if target == "EBRAKE_ACTU":
                    if movement == 0:
                        EBRAKE_ACTU_L_STATE = HALT
                        EBRAKE_ACTU_R_STATE = HALT
                    elif movement == 1:
                        EBRAKE_ACTU_L_STATE = EXT_FREE
                        EBRAKE_ACTU_R_STATE = EXT_FREE
                    elif movement == 2:
                        EBRAKE_ACTU_L_STATE = RET_FREE
                        EBRAKE_ACTU_R_STATE = RET_FREE
                elif target == "EBRAKE_ACTU_L":
                    if movement == 0:
                        EBRAKE_ACTU_L_STATE = HALT
                    elif movement == 1:
                        EBRAKE_ACTU_L_STATE = EXT_FREE
                    elif movement == 2:
                        EBRAKE_ACTU_L_STATE = RET_FREE
                elif target == "EBRAKE_ACTU_R":
                    if movement == 0:
                        EBRAKE_ACTU_R_STATE = HALT
                    elif movement == 1:
                        EBRAKE_ACTU_R_STATE = EXT_FREE
                    elif movement == 2:
                        EBRAKE_ACTU_R_STATE = RET_FREE
                elif target == "EBRAKE_EMAG":
                    if movement == 0:
                        EBRAKE_EMAG_L_STATE = OFF
                        EBRAKE_EMAG_R_STATE = OFF
                    if movement == 1:
                        EBRAKE_EMAG_L_STATE = ON
                        EBRAKE_EMAG_R_STATE = ON
                elif target == "EBRAKE_EMAG_L":
                    if movement == 0:
                        EBRAKE_EMAG_L_STATE = OFF
                    if movement == 1:
                        EBRAKE_EMAG_L_STATE = ON
                elif target == "EBRAKE_EMAG_R":
                    if movement == 0:
                        EBRAKE_EMAG_R_STATE = OFF
                    if movement == 1:
                        EBRAKE_EMAG_R_STATE = ON
                elif target == "MAINB_ACTU":
                    if movement == 0:
                        MAINB_ACTU_L_STATE = HALT
                        MAINB_ACTU_R_STATE = HALT
                    elif movement == 1:
                        MAINB_ACTU_L_STATE = EXT_FREE
                        MAINB_ACTU_R_STATE = EXT_FREE
                    elif movement == 2:
                        MAINB_ACTU_L_STATE = RET_FREE
                        MAINB_ACTU_R_STATE = RET_FREE
                elif target == "MAINB_ACTU_L":
                    if movement == 0:
                        MAINB_ACTU_L_STATE = HALT
                    elif movement == 1:
                        MAINB_ACTU_L_STATE = EXT_FREE
                    elif movement == 2:
                        MAINB_ACTU_L_STATE = RET_FREE
                elif target == "MAINB_ACTU_R":
                    if movement == 0:
                        MAINB_ACTU_R_STATE = HALT
                    elif movement == 1:
                        MAINB_ACTU_R_STATE = EXT_FREE
                    elif movement == 2:
                        MAINB_ACTU_R_STATE = RET_FREE
                else:
                    pass
        except socket.timeout as e:
            err = e.args[0]
            # this next if/else is a bit redundant, but illustrates how the
            # timeout exception is setup
            if err == 'timed out':
                time.sleep(1)
                print('recv timed out, retry later')
                break
            else:
                print(e)
                sys.exit(1)
        except socket.error as e:
            # Something else happened, handle error, exit, etc.
            print(e)
            sys.exit(1)


if __name__ == "__main__":
    IP_ADDRESS = "192.168.1.11"  # TODO CHANGE THIS TO COMPUTER'S IP ADDRESS!!!
    PORT = 3002  # If you change this change in gui.py as well.

    hostName = socket.gethostbyname('0.0.0.0')
    gui_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    gui_sock.bind((hostName, PORT))
    gui_sock.setblocking(False)

    logfile = open("temp_log.txt")
    start = time.time()

    Rpi.GPIO.setup(EBRAKE_ACTU_L_BACK, Rpi.GPIO.OUT, initial=Rpi.GPIO.LOW)
    Rpi.GPIO.setup(EBRAKE_ACTU_L_FORW, Rpi.GPIO.OUT, initial=Rpi.GPIO.LOW)
    Rpi.GPIO.setup(EBRAKE_ACTU_R_BACK, Rpi.GPIO.OUT, initial=Rpi.GPIO.LOW)
    Rpi.GPIO.setup(EBRAKE_ACTU_R_FORW, Rpi.GPIO.OUT, initial=Rpi.GPIO.LOW)
    Rpi.GPIO.setup(EBRAKE_EMAG_L, Rpi.GPIO.OUT, initial=Rpi.GPIO.LOW)
    Rpi.GPIO.setup(EBRAKE_EMAG_L, Rpi.GPIO.OUT, initial=Rpi.GPIO.LOW)
    Rpi.GPIO.setup(MAINB_ACTU_L_FORW, Rpi.GPIO.OUT, initial=Rpi.GPIO.LOW)
    Rpi.GPIO.setup(MAINB_ACTU_L_BACK, Rpi.GPIO.OUT, initial=Rpi.GPIO.LOW)
    Rpi.GPIO.setup(MAINB_ACTU_R_FORW, Rpi.GPIO.OUT, initial=Rpi.GPIO.LOW)
    Rpi.GPIO.setup(MAINB_ACTU_R_BACK, Rpi.GPIO.OUT, initial=Rpi.GPIO.LOW)

    while True:
        update_sensors()
        log(logfile)
        send(gui_sock)
        recv(gui_sock)
        update_actuators()
