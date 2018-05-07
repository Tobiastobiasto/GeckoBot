# -*- coding: utf-8 -*-
"""
Created on Mon May 07 14:01:53 2018

@author: AmP
"""

from __future__ import print_function

import __builtin__
import threading
import time
import traceback
import sys
import Adafruit_BBIO.GPIO as GPIO
import Adafruit_BBIO.ADC as ADC

from termcolor import colored

PWMREFMODE = "P9_10"
PRESSUREREFMODE = "P9_11"
PATTERNREFMODE = "P9_12"
WALKINGCONFIRM = "P9_13"
INFINITYMODE = "P9_14"

PWMLED = ""
PRESSURELED = ""
PATTERNLED = ""
WALKINGCONFIRMLED = ""
INFINITYLED = ""

DISCRETEPRESSUREREF = ["P9_15", "P9_16", "P9_17", "P9_18"]
CONTINUOUSPRESSUREREF = ["P9_15", "P9_16", "P9_17", "P9_18",
                         "P9_15", "P9_16", "P9_17", "P9_18"]


def print(*args, **kwargs):
    __builtin__.print(colored('Comm_Thread: ', 'red'), *args, **kwargs)


class HUIThread(threading.Thread):
    def __init__(self, cargo):
        """ """
        threading.Thread.__init__(self)
        self.cargo = cargo

        print('Initialize HUI Thread ...')
        ADC.setup()

        GPIO.setup(PWMREFMODE, GPIO.IN)
        GPIO.setup(PRESSUREREFMODE, GPIO.IN)
        GPIO.setup(PATTERNREFMODE, GPIO.IN)
        GPIO.setup(WALKINGCONFIRM, GPIO.IN)
        GPIO.setup(INFINITYMODE, GPIO.IN)

        GPIO.setup(PWMLED, GPIO.OUT)
        GPIO.setup(PRESSURELED, GPIO.OUT)
        GPIO.setup(PATTERNLED, GPIO.OUT)
        GPIO.setup(WALKINGCONFIRMLED, GPIO.OUT)
        GPIO.setup(INFINITYLED, GPIO.OUT)

        for pin in DISCRETEPRESSUREREF:
            GPIO.setup(pin, GPIO.IN)
        for pin in CONTINUOUSPRESSUREREF:
            GPIO.setup(pin, GPIO.IN)

        GPIO.add_event_detect(PWMREFMODE, GPIO.RISING)
        GPIO.add_event_detect(PRESSUREREFMODE, GPIO.RISING)
        GPIO.add_event_detect(PATTERNREFMODE, GPIO.RISING)
        GPIO.add_event_detect(WALKINGCONFIRM, GPIO.RISING)
        GPIO.add_event_detect(INFINITYMODE, GPIO.RISING)

    def run(self):
        """ run HUI """
        print('Running HUI Thread ...')

        try:
            while self.cargo.state != 'EXIT':
                try:
                    self.get_tasks()
                except:
                    print('\n--caught exception! in HUI Thread--\n')
                    print("Unexpected error:\n", sys.exc_info()[0])
                    print(sys.exc_info()[1])
                    traceback.print_tb(sys.exc_info()[2])
                    print('\nBreaking the HUI loop ...')
                    break
        finally:
            print('Exit the HUI Thread ...')
            self.cargo.state = 'EXIT'

        print('HUI Thread is done ...')

    def check_state(self):
        new_state = None
        if GPIO.event_detected(PWMREFMODE):
            new_state = 'USER_CONTROL'
        if GPIO.event_detected(PRESSUREREFMODE):
            new_state = 'USER_REFERENCE'
        if GPIO.event_detected(PATTERNREFMODE):
            new_state = 'REFERENCE_TRACKING'
        return new_state if new_state else self.cargo.state

    def set_leds(self):
        actual_state = self.cargo.actual_state
        for pin, state in [(PWMLED, "USER_CONTROL"),
                           (PRESSURELED, "USER_REFERENCE"),
                           (PATTERNLED, "REFERENCE_TRACKING")]:
            GPIO.output(pin, GPIO.HIGH if actual_state == state else GPIO.LOW)
        for pin, state in [(WALKINGCONFIRMLED, self.cargo.wcomm.is_active),
                           (INFINITYLED, self.cargo.wcomm.infmode)]:
            GPIO.output(pin, GPIO.HIGH if state else GPIO.LOW)

    def get_tasks(self):
        pass

    def change_state(self, state):
        self.cargo.state = state
        while not self.cargo.actual_state == state:
            time.sleep(self.cargo.sampling_time)

    def set_valve(self):
        for idx, pin in enumerate(CONTINUOUSPRESSUREREF):
            self.cargo.pwm_task[str(idx)] = ADC.read(pin)
            self.cargo.pwm_task[str(idx)] = ADC.read(pin)  # bug-> read twice

    def set_ref(self):
        for idx, pin in enumerate(CONTINUOUSPRESSUREREF):
            self.cargo.ref_task[str(idx)] = ADC.read(pin)
            self.cargo.ref_task[str(idx)] = ADC.read(pin)

    def set_dvalve(self):
        for idx, pin in enumerate(DISCRETEPRESSUREREF):
            self.cargo.dvalve_task[str(idx)] = (
                True if GPIO.input(pin) else False)

    def set_walking(self):
        if GPIO.event_detected(WALKINGCONFIRM):
            confirm = self.cargo.wcomm.confirm
            self.cargo.wcomm.confirm = not confirm

    def set_infmode(self):
        if GPIO.event_detected(INFINITYMODE):
            state = self.cargo.wcomm.infmode
            self.cargo.wcomm.infmode = not state
