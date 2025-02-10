#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import time
import datetime
import struct
import socket
from queue import Queue
from queue import Empty
import threading
import numpy as np

from GBCR3_Reg import *
from numpy.compat import long
import pyvisa as visa
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1.inset_locator import zoomed_inset_axes
from mpl_toolkits.axes_grid1.inset_locator import mark_inset

from command_interpret import command_interpret
from crc32_8 import crc32_8

hostname = '192.168.2.6'  # Fixed FPGA IP address
port = 1024               # Port number

def print_bytes_hex(data):
    lin = ['0x%02X' % x for x in data]
    print(" ".join(lin))

def generate_summary(store_dict):
    summary_file = f"{store_dict}/summary.txt"
    with open(summary_file, 'w') as summary:
        summary.write("Channel | Injected Errors | Error Count\n")
        for i in range(8):
            ch_file = f"{store_dict}/Ch{i}.TXT"
            if os.path.exists(ch_file):
                with open(ch_file, 'r') as infile:
                    lines = infile.readlines()
                    if lines:
                        last_line = lines[-1].strip().split()
                        summary.write(f"{i} | {last_line[2]} | {last_line[3]}\n")
    print(f"Summary saved to {summary_file}")

def Receive_data(store_dict, num_file):
    Slave_Addr = 0x23
    GBCR3_Reg1 = GBCR3_Reg()

    # Initialize iic_write_val and configure registers
    iic_write_val = [0 for i in range(32)]
    iic_write_val = GBCR3_Reg1.configure_all(iic_write_val)

    print("Line 126, Written values are ", end="")
    print_bytes_hex(iic_write_val)

    # Write to I2C registers
    for i in range(len(iic_write_val)):
        iic_write(1, Slave_Addr, 0, i, iic_write_val[i])
    print(f"Written values: {iic_write_val}")

    # Read back data and validate
    iic_read_val = []
    for i in range(len(iic_write_val)):
        iic_read_val += [iic_read(0, Slave_Addr, 1, i)]
    if iic_read_val == iic_write_val:
        print(f"Written = Read: {iic_read_val}")
    else:
        print(f"Written != Read: {iic_read_val}")

    for files in range(num_file):
        if files % 10 == 0:
            # Write I2C data to file
            with open(f"./{store_dict}/I2C.TXT", 'a') as infile_iic:
                lasttime = datetime.datetime.now()
                iic_read_val = []
                for iic_read_index in range(len(iic_write_val)):
                    iic_read_val += [iic_read(0, Slave_Addr, 1, iic_read_index)]
                if iic_read_val == iic_write_val:
                    print(f"{lasttime} W == R: {iic_read_val}")
                    infile_iic.write(f"{lasttime} Written ==  Read: {iic_read_val}\n")
                else:
                    print(f"{lasttime} W!= R: {iic_read_val}")
                    infile_iic.write(f"{lasttime} Written !=  Read: {iic_read_val}\n")
                infile_iic.flush()

            # Read supply current IDD
            with open(f"./{store_dict}/IDD.TXT", 'a') as infile_Idd:
                lasttime = datetime.datetime.now()
                current = Current_monitor()
                print(f"IDD: {lasttime} {current[1]:.3f} mA")
                infile_Idd.write(f"{lasttime} {current[1]:.3f} mA\n")
                infile_Idd.flush()

        mem_data = cmd_interpret.read_data_fifo(50000)
        for i in range(50000 - len(mem_data)):
            mem_data.append(0)
        mem_data.append(-1)
        if files % 10 == 0:
            print(f"{'Receive_data'} is producing {files} to the queue!")

        exec_data(mem_data, store_dict)
    
    print("'Receive_data' finished!")
    generate_summary(store_dict)

def exec_data(mem_data, store_dict):
    isEnd = False
    count = 0
    aligned = 0
    i = 0
    ChStat = [[0, 0, 0, 0, 0, 0, 0, 0, 0, 0] for _ in range(4)]

    while i < 50001:
        val = [0] * 8
        for k in range(8):
            if i > 50000:
                isEnd = True
            else:
                val[k] = mem_data[i]
                i += 1
        if val[-1] < 0:
            isEnd = True
        if isEnd:
            break
        Rawdata = sum(val[k] << (128 * (7 - k)) for k in range(8))

        if aligned == 1:
            error_flag = (Rawdata >> (127 + 128)) & 0x1
            if error_flag == 1:
                channel_id = (Rawdata >> (123 + 128)) & 0x7
                time_stamp = (Rawdata >> (79 + 128 - 4)) & 0x7FF_FFFFFF8000000000000000
                inject_error = (Rawdata >> (59 + 128)) & 0xFFFFF8000000000000
                expected_code = (Rawdata >> (27 + 128)) & 0x7FFFFF8000000000000000000000
                received_code = (Rawdata >> 123) & 0x7FFFFFFF800000000000000000000
                error_position = (Rawdata >> 91) & 0x7FFFFFFF8000000000
                error_counter = (Rawdata >> 32) & 0x7FF_FFFFFF_00000000
                crc32 = Rawdata & 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
                cal_crc_data = [0] * 28
                for k in range(28):
                    shift = 0xFF00_0000_0000_0000_0000_0000_0000_0000 >> (k * 8)
                    cal_crc_data[k] = (Rawdata & shift) >> (248 - k * 8)
                cal_crc32 = crc32_8(cal_crc_data[0], 0xFFFF_FFFF)
                for k in range(27):
                    cal_crc32 = crc32_8(cal_crc_data[k + 1], cal_crc32)

                Time = datetime.datetime.now()
                print(f'{Time} {channel_id} {inject_error} {error_counter} {cal_crc32 - crc32} {time_stamp} {expected_code} {received_code} {error_position} {crc32}')
                with open(f"./{store_dict}/ChAll.TXT", 'a') as infile:
                    infile.write(f'{Time} {channel_id} {inject_error} {error_counter} {cal_crc32 - crc32} {time_stamp} {expected_code} {received_code} {error_position} {crc32}\n')
                    infile.flush()
                with open(f"./{store_dict}/Ch{channel_id}.TXT", 'a') as infile:
                    infile.write(f'{Time} {channel_id} {inject_error} {error_counter} {cal_crc32 - crc32} {time_stamp} {expected_code} {received_code} {error_position} {crc32}\n')
                    infile.flush()

                if channel_id < 10:
                    ChStat[3][channel_id] += 1
                else:
                    print(f"Bad channel_id {channel_id}")
            else:
                count += 1
                if count % 1000000 == 0:
                    print(f"received data is filler: {Rawdata}")
                if Rawdata != 0x3c5c_7c5c_0000_0000_0000_0000_1234_4321_7d6d_7a5a_0000_0000_0000_0000_5566_6655:
                    aligned = 0
                    print(f"Line 276, Alignment loss Rawdata is {Rawdata}")
                StatVal = 2 * aligned
                ChStat[StatVal][StatChan] += 1
        else:
            if i < 200:
                print(f"Not aligned chan={StatChan} Rawdata={Rawdata}")
            while aligned == 0:
                if i > 50000:
                    isEnd = True
                else:
                    value = mem_data[i]
                    i += 1
                    if value < 0:
                        isEnd = True
                    else:
                        for k in range(7):
                            val[k] = val[k + 1]
                        val[7] = value
                        Rawdata = sum(val[k] << (128 * (7 - k)) for k in range(8))
                if isEnd:
                    break

def Current_monitor():
    I2C_Addr = 0x9e >> 1
    iic_write(1, I2C_Addr, 0, 0x06, 0x11)
    iic_write(1, I2C_Addr, 0, 0x01, 0x38)

    V12_Volt = 0
    I12 = 0
    V12_MSB = iic_read(0, I2C_Addr, 1, 0x0C)
    V12_LSB = iic_read(0, I2C_Addr, 1, 0x0D)
    V12_Valid = (V12_MSB & 0x80) >> 7
    V12_Sign = (V12_MSB & 0x40) >> 6
    if V12_Sign == 0:
        V12_Volt = ((V12_MSB & 0x3f) << 8 | V12_LSB) * 19.075 * 1E-6
    I12 = 982.5 * V12_Volt - 10.489

    V34_Volt = 0
    I34 = 0
    V34_MSB = iic_read(0, I2C_Addr, 1, 0x10)
    V34_LSB = iic_read(0, I2C_Addr, 1, 0x11)
    V34_Valid = (V34_MSB & 0x80) >> 7
    V34_Sign = (V34_MSB & 0x40) >> 6
    if V34_Sign == 0:
        V34_Volt = ((V34_MSB & 0x3f) << 8 | V34_LSB) * 19.075 * 1E-6
    I34 = 949.0 * V34_Volt + 0.0258

    VCC_MSB = iic_read(0, I2C_Addr, 1, 0x1C)
    VCC_LSB = iic_read(0, I2C_Addr, 1, 0x1D)

    VCC_Volt = ((VCC_MSB & 0x3f) << 8 | VCC_LSB) * 0.00030518 + 2.5
    return [I12, I34]

def main():
    if len(sys.argv) != 2:
        print("Usage: python main.py <num_file>")
        sys.exit(1)

    num_file = int(sys.argv[1])
    store_dict = userdefine_dir
    userdefinedir = "GBCR3_SEE_Test"
    userdefinedir_log = f"{userdefinedir}_log"

    todaystr = "QAResults_6"
    timestr = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
    try:
        os.mkdir(todaystr)
        print(f"Directory {todaystr} was created!")
    except FileExistsError:
        print(f"Directory {todaystr} already exists!")

    userdefine_dir = todaystr + "/" + timestr
    try:
        os.mkdir(userdefine_dir)
    except FileExistsError:
        print(f"Directory {userdefine_dir} already exists!")

    # Initialize GBCR3_Reg instance
    GBCR3_Reg1 = GBCR3_Reg()
    iic_write_val = [0 for i in range(32)]

    # Configure all registers
    iic_write_val = GBCR3_Reg1.configure_all(iic_write_val)

    print("Line 126, Written values are ", end="")
    print_bytes_hex(iic_write_val)

    # Write to I2C
    Slave_Addr = 0x23
    for i in range(len(iic_write_val)):
        iic_write(1, Slave_Addr, 0, i, iic_write_val[i])
    print(f"Written values: {iic_write_val}")

    # Read back data and validate
    iic_read_val = []
    for i in range(len(iic_write_val)):
        iic_read_val += [iic_read(0, Slave_Addr, 1, i)]
    if iic_read_val == iic_write_val:
        print(f"Written = Read: {iic_read_val}")
    else:
        print(f"Written != Read: {iic_read_val}")

    # Proceed with other tasks like receiving data, etc.
    Receive_data(store_dict, num_file)
    print("All jobs done.")

## if statement
if __name__ == "__main__":
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error:
        print("Failed to create socket!")
        sys.exit()
    try:
        s.connect((hostname, port))
    except socket.error:
        print(f"failed to connect to ip:{hostname}")
    cmd_interpret = command_interpret(s)
    try:
        main()
    except KeyboardInterrupt:
        print("\nApplication exit!")
    except:
        print("Command Failed")

    s.close()
