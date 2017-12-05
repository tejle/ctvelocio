#!/usr/bin/env python

# Copyright 2017 Justin Searle
#
# Based on code from https://github.com/jsr5194/velocio-ace-remote and used with permission
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import re
import sys
import time
import serial

# define serial connection
ser = serial.Serial(
    port='/dev/ttyACM0',
    baudrate=9600,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS
)


def print_help():
    print ""
    print "********************************************************************************"
    print "*                                                                              *"
    print "*                             Control Things Velocio                           *"
    print "*                                 version 1.0.1                                *"
    print "*                                                                              *"
    print "********************************************************************************"
    print ""
    print " Usage: python ctvelocio [instruction]"
    print ""
    print " Control Instructions:"
    print " \tplay \t\t\tstart the routine at current position"
    print " \tpause\t\t\tpause the routine at current position"
    print " \treset\t\t\treset the routine to the beginning"
    print " \tset_output_1_off\tset output 1 to off"
    print " \tset_output_2_off\tset output 2 to off"
    print " \tset_output_3_off\tset output 3 to off"
    print " \tset_output_4_off\tset output 4 to off"
    print " \tset_output_5_off\tset output 5 to off"
    print " \tset_output_6_off\tset output 6 to off"
    print " \tset_output_all_off\tset all output to off"
    print ""
    print " \tset_output_1_on\t\tset output 1 to on"
    print " \tset_output_2_on\t\tset output 2 to on"
    print " \tset_output_3_on\t\tset output 3 to on"
    print " \tset_output_4_on\t\tset output 4 to on"
    print " \tset_output_5_on\t\tset output 5 to on"
    print " \tset_output_6_on\t\tset output 6 to on"
    print " \tset_output_all_on\tset all output to on"
    print ""
    print ""
    print " Read Instructions:"
    print ""
    print " \tread_input_bits\t\tquery the input bits and print the response"
    print " \tread_output_bits\tquery the output bits and print the response"
    print ""
    print ""
    print " Debug Instructions:"
    print ""
    print " \tenter_debug\t\tput the device into debug mode for testing"
    print " \texit_debug\t\texit the device debug mode for normal operation"
    print " \tstep_into\t\tstandard procedure"
    print " \tstep_out\t\tstandard procedure"
    print " \tstep_over\t\tstandard procedure"
    print ""
    print ""
    print " Sending RAW messages:"
    print ""
    print " \t--raw XX YY ZZ\t\tsends [XX, YY, ZZ]"
    print " \t--raw XX [00,04]\tsends with range substitution [XX 00], [XX, 01], [XX, ...]"
    print ""
    print " Example:\tpython ctvelocio play"
    print " Example:\tpython ctvelocio read_output_bits"
    print " Example:\tpython ctvelocio exit_debug"
    print ""
    print ""
    exit(1)


def raw_to_instruction(raw):
    raw_str = ''.join(raw)
    number_range = '\\[([0-9a-fA-F]{2}),([0-9a-fA-F]{2})\\]'
    matches = re.search(number_range, raw_str)
    if matches:
        limits = [ord(x.decode('hex')) for x in matches.groups()]
        values = []
        for index in range(limits[0], limits[1] + 1):
            raw_gen = re.sub(number_range, str.format('{:02x}', index), raw_str, 1)
            for mod_msg in raw_to_instruction(raw_gen):
                values.append(mod_msg)
        return values
    return [raw_str.decode('hex')]


def as_normal_chars(charcode):
    if (64 < charcode < 123) or (58 > charcode > 47):
        return chr(charcode)
    return '_'


def as_mixed_chars(charcode):
    if (64 < charcode < 123) or (58 > charcode > 47):
        return '\033[92m ' + chr(charcode) + '\033[0m'
    if charcode == 32:
        return ' _'
    if charcode == ord('.'):
        return ' .'
    if charcode == 255:
        return str.format('\033[2m{:02x}\033[0m', charcode)
    return str.format('{:02x}', charcode)


# sends a set of instructions to the connected device
# @param instruction_set : an array of commands to send to the PLC in hex
# @param printstring     : runtime message for the user
def send_instruction(instruction_set, printstring):
    # clear out any leftover data
    if ser.inWaiting() > 0:
        ser.flushInput()

    if printstring == "raw":
        instruction_set = raw_to_instruction(instruction_set)

    # perform the write
    for instruction in instruction_set:
        tx_raw = [ord(elem) for elem in instruction]
        tx_hex = ' '.join(str.format('{:02x}', x) for x in tx_raw)

        ser.write(instruction)
        time.sleep(0.1)

        rx_raw = []
        while ser.inWaiting() > 0:
            rx_raw.append(ord(ser.read()))

        rx_hex = ' '.join(str.format('{:02x}', x) for x in rx_raw)
        rx_str = ''.join(map(as_normal_chars, rx_raw))
        rx_mix = ' '.join(map(as_mixed_chars, rx_raw))

        time.sleep(0.1)

        print "\033[1mtx:\033[0m %s \033[1mrx:\033[0m %s" % (tx_hex, rx_mix)


def main():
    # handle input errors
    if len(sys.argv) == 1:
        print_help()

    # get cmd line arg
    param = sys.argv[1]

    # check for help request
    if param == "-h" or param == "--help":
        print_help()

    # initiate the connection
    ser.isOpen()

    # process the instruction
    if commands.has_key(param):
        send_instruction(commands[param], param)

    # raw messages
    elif param == "--raw" and len(sys.argv) > 1:
        send_instruction( sys.argv[2:], "raw")

    else:
        print_help()

    # clean up
    ser.close()


if __name__ == "__main__":

    ###
    # define the instructions
    ###

    # control instructions
    press_stop = ["\x56\xff\xff\x00\x06\xf3"]

    press_play = ["\x56\xff\xff\x00\x07\xf1\x01"]
    press_pause = ["\x56\xff\xff\x00\x07\xf1\x02"]
    step_into = ["\x56\xff\xff\x00\x07\xf1\x03"]
    step_out = ["\x56\xff\xff\x00\x07\xf1\x04"]
    step_over = ["\x56\xff\xff\x00\x07\xf1\x05"]
    press_reset = ["\x56\xff\xff\x00\x07\xf1\x06"]
    exit_debug = ["\x56\xff\xff\x00\x07\xf0\x01"]
    enter_debug = ["\x56\xff\xff\x00\x07\xf0\x02"]

    set_output_1_off = ["\x56\xff\xff\x00\x15\x11\x01\x00\x01\x00\x00\x09\x01\x00\x00\x01\x00\x01\x00\x00\x00"]
    set_output_2_off = ["\x56\xff\xff\x00\x15\x11\x01\x00\x01\x00\x00\x09\x01\x00\x00\x01\x00\x02\x00\x00\x00"]
    set_output_3_off = ["\x56\xff\xff\x00\x15\x11\x01\x00\x01\x00\x00\x09\x01\x00\x00\x01\x00\x04\x00\x00\x00"]
    set_output_4_off = ["\x56\xff\xff\x00\x15\x11\x01\x00\x01\x00\x00\x09\x01\x00\x00\x01\x00\x08\x00\x00\x00"]
    set_output_5_off = ["\x56\xff\xff\x00\x15\x11\x01\x00\x01\x00\x00\x09\x01\x00\x00\x01\x00\x10\x00\x00\x00"]
    set_output_6_off = ["\x56\xff\xff\x00\x15\x11\x01\x00\x01\x00\x00\x09\x01\x00\x00\x01\x00\x20\x00\x00\x00"]

    set_output_1_on = ["\x56\xff\xff\x00\x15\x11\x01\x00\x01\x00\x00\x09\x01\x00\x00\x01\x00\x01\x00\x00\x01"]
    set_output_2_on = ["\x56\xff\xff\x00\x15\x11\x01\x00\x01\x00\x00\x09\x01\x00\x00\x01\x00\x02\x00\x00\x01"]
    set_output_3_on = ["\x56\xff\xff\x00\x15\x11\x01\x00\x01\x00\x00\x09\x01\x00\x00\x01\x00\x04\x00\x00\x01"]
    set_output_4_on = ["\x56\xff\xff\x00\x15\x11\x01\x00\x01\x00\x00\x09\x01\x00\x00\x01\x00\x08\x00\x00\x01"]
    set_output_5_on = ["\x56\xff\xff\x00\x15\x11\x01\x00\x01\x00\x00\x09\x01\x00\x00\x01\x00\x10\x00\x00\x01"]
    set_output_6_on = ["\x56\xff\xff\x00\x15\x11\x01\x00\x01\x00\x00\x09\x01\x00\x00\x01\x00\x20\x00\x00\x01"]

    set_output_all_off = ["\x56\xff\xff\x00\x15\x11\x01\x00\x01\x00\x00\x09\x01\x00\x00\x01\x00\x3f\x00\x00\x00"]
    set_output_all_on = ["\x56\xff\xff\x00\x15\x11\x01\x00\x01\x00\x00\x09\x01\x00\x00\x01\x00\x3f\x00\x00\x01"]

    # read instructions
    read_input_bits = [
        "\x56\xff\xff\x00\x08\x0a\x00\x01",
        "\x56\xff\xff\x00\x08\x0a\x00\x02",
        "\x56\xff\xff\x00\x08\x0a\x00\x03",
        "\x56\xff\xff\x00\x08\x0a\x00\x04",
        "\x56\xff\xff\x00\x08\x0a\x00\x05",
        "\x56\xff\xff\x00\x08\x0a\x00\x06"
    ]

    read_output_bits = [
        "\x56\xff\xff\x00\x08\x0a\x00\x07",
        "\x56\xff\xff\x00\x08\x0a\x00\x08",
        "\x56\xff\xff\x00\x08\x0a\x00\x09",
        "\x56\xff\xff\x00\x08\x0a\x00\x0a",
        "\x56\xff\xff\x00\x08\x0a\x00\x0b",
        "\x56\xff\xff\x00\x08\x0a\x00\x0c"
    ]

    commands = {
        "play": press_play,
        "pause": press_pause,
        "reset": press_reset,
        "step_into": step_into,
        "step_out": step_out,
        "step_over": step_over,
        "enter_debug": enter_debug,
        "exit_debug": exit_debug,
        "set_output_1_off": set_output_1_off,
        "set_output_1_on": set_output_1_on,
        "set_output_2_off": set_output_2_off,
        "set_output_2_on": set_output_2_on,
        "set_output_3_off": set_output_3_off,
        "set_output_3_on": set_output_3_on,
        "set_output_4_off": set_output_4_off,
        "set_output_4_on": set_output_4_on,
        "set_output_5_off": set_output_5_off,
        "set_output_5_on": set_output_5_on,
        "set_output_6_off": set_output_6_off,
        "set_output_6_on": set_output_6_on,
        "set_output_all_on": set_output_all_on,
        "set_output_all_off": set_output_all_off,
        "read_input_bits": read_input_bits,
        "read_output_bits": read_output_bits}

    try:
        main()

    except Exception as e:
        print ""
        print "[!] ERROR"
        print "[!] MSG: %s" % e
        print ""
        exit(1)
