#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import copy
import time
import datetime
import struct
import socket
from queue import Queue
from queue import Empty  ##
import threading
import numpy as np
#from this import i

from numpy.compat import long

from GBCR3_Reg import *
import pyvisa as visa
from command_interpret import *
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1.inset_locator import zoomed_inset_axes
from mpl_toolkits.axes_grid1.inset_locator import mark_inset

from crc32_8 import crc32_8

'''
@author: Wei Zhang
@date: 2020-11-14
This script is used to test GBCR3 SEU. It mainly includes I2C communication, Ethernet communication, and eight 
channels bit error record.
'''
hostname = '192.168.2.6'  # FPGA IP address
port = 1024  # port number

# ---------------------------
# 
# ------------------------------------------------------------------#
def main():
    # #  Create a directory named path with date of today
    userdefinedir = "GBCR2_SEE_Test"
    userdefinedir_log = "%s_log" % userdefinedir

    today = datetime.date.today()
    # TimeD = time.localtime()
    TimeD = time.strftime("%H-%M-%S", time.localtime())
    # todaystr = today.isoformat() + "-" + TimeD + "_Results"
    todaystr = "QAResults"
    timestr = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
    try:
        os.mkdir(todaystr)
        print("Directory %s was created!" % todaystr)
    except FileExistsError:
        print("Directory %s already exists!" % todaystr)
    # userdefine_dir = todaystr + "./%s"%userdefinedir
    # userdefine_dir = todaystr + "./%s/"%userdefinedir + TimeD
    userdefine_dir = todaystr + "/" + timestr
    print(userdefine_dir)
    try:
        os.mkdir(userdefine_dir)
    except FileExistsError:
        print("User define directories already created!!!")

    num_file = int(sys.argv[1])  # total files will be read back
    store_dict = userdefine_dir

    # 20220428 dbw for single #queue = Queue()  # define a queue
    # 20220428 #receive_data = Receive_data('Receive_data', queue, num_file)  # initial receive_data class
    Receive_data(store_dict, num_file)

    print(" line 66, All jobs are done!")
# end def main


# class Receive_data(threading.Thread):  # threading class
# 20220428 #def __init__(self, name, queue, num_file):
# def __init__(self, name, store_dict, num_file):
#    threading.Thread.__init__(self, name=name)
# 20220428 #self.queue = queue
#    self.num_file = num_file
#    self.store_dict = store_dict  # 20220428 #
def print_bytes_hex(data):
    lin = ['0x%02X' % i for i in data]
    print(" ".join(lin))

def parse_datetime(datetime_str, format="%Y-%m-%d %H:%M:%S")：
    return datetime.strptime(datetime_str, format)

def generate_summary(store_dict):
    summary_file = f"{store_dict}/summary.txt"
    with open(summary_file, 'w') as summary:
        summary.write("Channel | Injected Errors | Error Count | Start Time | End Time | Duration (min) | Start Inj/Obs | End Inj/Obs | Ninj | Nobs\n")
        
        for i in range(8):
            ch_file = f"{store_dict}/Ch{i}.TXT"
            if os.path.exists(ch_file):
                with open(ch_file, 'r') as infile:
                    lines = infile.readlines()
                    if lines:
                        last_line = lines[-1].strip().split()
                        channel = i
                        injected_errors = last_line[2]  # Assuming injected errors are at index 2
                        error_count = last_line[3]  # Assuming error count is at index 3
                        date_str = last_line[0] + " " + last_line[1]  # Combine date and time
                        start_time = parse_datetime(date_str)
                        # You can use last line for end time or handle time more precisely here
                        end_time = start_time  # Assuming end time is the same for now

                        # Calculate duration (in minutes)
                        duration_minutes = (end_time - start_time).total_seconds() / 60

                        # Example for inj_gen and inj_obs based on the line structure:
                        # For this example, assume we can extract start and end inj_gen, inj_obs:
                        start_inj = last_line[4]  # Assuming injection start is at index 4
                        start_obs = last_line[5]  # Assuming observation start is at index 5
                        end_inj = last_line[6]  # Assuming injection end is at index 6
                        end_obs = last_line[7]  # Assuming observation end is at index 7

                        # Write the summary to the file
                        summary.write(f"{channel} | {injected_errors} | {error_count} | "
                                       f"{start_time.strftime('%Y-%m-%d %H:%M:%S')} | "
                                       f"{end_time.strftime('%Y-%m-%d %H:%M:%S')} | "
                                       f"{duration_minutes:.1f} | {start_inj} / {start_obs} | "
                                       f"{end_inj} / {end_obs} | {int(end_inj) - int(start_inj)} | "
                                       f"{int(end_obs) - int(start_obs)}\n")
    
    with open(summary_file, 'r') as f:
        print(f.read())

    print(f"Summary saved to {summary_file}")
# # define a receive data function
def Receive_data(store_dict, num_file):
    # begin iic initilization -----------------------------------------------------------------------------------#
    # write, read back, and compare

    Slave_Addr = 0x23
    GBCR3_Reg1 = GBCR3_Reg()
    print("start GBCR3 reg config")
    
    iic_write_val = [0 for i in range(32)] 

    print("declared iic_write_val")

    iic_write_val = GBCR3_Reg1.configure_all(iic_write_val)
    
    print("Line 126, Written values are ", end = "")
    print_bytes_hex(iic_write_val)
    # ## write data into I2C register one by one
    for i in range(len(iic_write_val)):
        iic_write(1, Slave_Addr, 0, i, iic_write_val[i])
    print("Written values:", iic_write_val)

    ## read back  data from I2C register one by one
    iic_read_val = []
    for i in range(len(iic_write_val)):
        iic_read_val += [iic_read(0, Slave_Addr, 1, i)]
    if iic_read_val == iic_write_val:
        print("Written =  Read: %s"%(iic_read_val))
    else:
        print("Written != Read: %s"%(iic_read_val))
    #end iic initilization -----------------------------------------------------------------------------------#


    for files in range(num_file):

        if files % 10 == 0:
            # # read back  data from I2C register one by one
            with open("./%s/I2C.TXT" % store_dict, 'a') as infile_iic:
                lasttime = datetime.datetime.now()
                iic_read_val = []
                for iic_read_index in range(len(iic_write_val)):
                    iic_read_val += [iic_read(0, Slave_Addr, 1, iic_read_index)]
                if iic_read_val == iic_write_val:
                    print("%s W == R: %s" % (lasttime, iic_read_val))
                    infile_iic.write("%s Written ==  Read: %s\n" % (lasttime, iic_read_val))
                else:
                    print("%s W!= R: %s" % (lasttime, iic_read_val))
                    infile_iic.write("%s Written !=  Read: %s\n" % (lasttime, iic_read_val))
                # end if
                infile_iic.flush()
            # end with

            # # read supply current IDD
            with open("./%s/IDD.TXT" % store_dict, 'a') as infile_Idd:
                lasttime = datetime.datetime.now()
                current = Current_monitor()
                print("IDD: %s %.3f mA" % (lasttime, current[1]))
                infile_Idd.write("%s %.3f mA\n" % (lasttime, current[1]))
                infile_Idd.flush()
            # end with
        # end if files % 10 == 0

        mem_data = cmd_interpret.read_data_fifo(50000)
        # ensure mem_data have 50001 byte
        for i in range(50000 - len(mem_data)):
            mem_data.append(0)
        mem_data.append(-1)
        if files % 10 == 0:
            print("{} is producing {} to the queue!".format('Receive_data', files))
        # end if files % 10 == 0 
        exec_data(mem_data, store_dict)
        # 20220428 #for i in range(50000):
        # 20220428 #    self.queue.put(mem_data[i])
    # end for files in range(self.num_file)
    print("line 181, 'Receive_data' finished!")
    generate_summary(store_dict)
    # 20220428 #self.queue.put(-1)
# end def run
# ---------------------------------------------------------------------------------------------#

# ---------------------------------------------------------------------
# ------------------------#
def exec_data(mem_data, store_dict):
    isEnd = False
    count = 0
    aligned = 0
    i = 0
    #
    # Collect frame stat=2*Aligned+Err by channel  
    # Ch=9 is filler without channel ID 
    #
    ChStat = [
        [0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0,0,0]
    ]
    # for i in range(6250)
    while i < 50001:
        # get 8 words to combine a frame
        val = [0, 0, 0, 0, 0, 0, 0, 0]
        for k in range(8):
            if i > 50000:
                isEnd = True
            else:
                val[k] = mem_data[i]
                i = i + 1
            #end if
        if val[-1] < 0:
            # print("line 204", val)
            isEnd = True
        if isEnd:
            break
        Rawdata = val[0] << (96 + 128) | val[1] << (64 + 128) | val[2] << (32 + 128) | val[3] << 128 | val[4] << 96 | val[5] << 64 | val[6] << 32 | val[7]
        # end get 8 words
        # if i<200: 
        #  print("i=%5i aligned=%i Rawdata=%x" % (i,aligned,Rawdata) )
        # #end if
        # tentative evaluation Error flag and channel ID  
        StatErr  = val[0]>>31&1 
        StatChan = val[0]>>27&0xF  
        if aligned == 1:
            error_flag = (
                                 Rawdata & 0x8000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000) >> (127 + 128)  # error flag

            # if aligned, display on the screen and save to files
            if error_flag == 1:
                channel_id = (
                                     Rawdata & 0x7800_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000) >> (
                                     123 + 128)  # channel Id
                time_stamp = (
                                     Rawdata & 0x07ff_ffff_ffff_f800_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000) >> (
                                     79 + 128 - 4)  # time stamp
                inject_error = (
                                       Rawdata & 0x0000_0000_0000_07ff_f800_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000) >> (
                                       59 + 128)  # inject error
                expected_code = (
                                        Rawdata & 0x0000_0000_0000_0000_07ff_ffff_f800_0000_0000_0000_0000_0000_0000_0000_0000_0000) >> (
                                        27 + 128)
                received_code = (
                                        Rawdata & 0x0000_0000_0000_0000_0000_0000_07ff_ffff_f800_0000_0000_0000_0000_0000_0000_0000) >> 123  # received data
                error_position = (
                                         Rawdata & 0x0000_0000_0000_0000_0000_0000_0000_0000_07ff_ffff_f800_0000_0000_0000_0000_0000) >> 91
                error_counter = (
                                        Rawdata & 0x0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_07ff_ffff_ffff_ffff_0000_0000) >> 32
                crc32 = (
                                Rawdata & 0x0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_ffff_ffff) >> 0
                cal_crc_data = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                for k in range(28):
                    shift = 0xff00_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000 >> (k * 8)
                    cal_crc_data[k] = (Rawdata & shift) >> (248 - k * 8)
                # end for
                cal_crc32 = crc32_8(cal_crc_data[0], 0xffff_ffff)
                for k in range(27):
                    cal_crc32_t = crc32_8(cal_crc_data[k + 1], cal_crc32)
                    cal_crc32 = cal_crc32_t

                Time = datetime.datetime.now()
                print('%s %d %d %d %d %d %08x %08x %08x %d' % (
                    Time, channel_id, inject_error, error_counter, cal_crc32 - crc32, time_stamp,
                    expected_code, received_code, error_position, crc32))
                with open("./%s/ChAll.TXT" % store_dict,
                          'a') as infile:  # # 'a': add, will not cover previous infor
                    infile.write('%s %d %d %d %d %d %08x %08x %08x %d\n' % (
                        Time, channel_id, inject_error, error_counter, cal_crc32 - crc32, time_stamp,
                        expected_code, received_code, error_position, crc32))
                    infile.flush()
                with open("./%s/Ch%d.TXT" % (store_dict, channel_id),
                          'a') as infile:  # # 'a': add, will not cover previous infor
                    infile.write('%s %d %d %d %d %d %08x %08x %08x %d\n' % (
                        Time, channel_id, inject_error, error_counter, cal_crc32 - crc32, time_stamp,
                        expected_code, received_code,
                        error_position, crc32))
                    infile.flush()
                # Frame stat Aligned with Error
                if channel_id < 10:
                    ChStat[3][channel_id] = ChStat[3][channel_id] + 1
                else:
                    print("Bad channel_id %i" % channel_id)
                #end if
            else:  # error_flag != 1
                count = count + 1
                if count % 1000000 == 0:
                    print("received data is filler: %x" % Rawdata)
                if Rawdata != 0x3c5c_7c5c_0000_0000_0000_0000_1234_4321_7d6d_7a5a_0000_0000_0000_0000_5566_6655:
                    aligned = 0
                    print("Line 276, ALignment loss Rawdata is %x" % Rawdata)
                # Current frame state reevaluated
                StatVal = 2*aligned
                ChStat[StatVal][StatChan] = ChStat[StatVal][StatChan] + 1   
            # end if error_flag
        else:  # aligned != 1
            if i<200:
                print("Not aligned chan=%i  Rawdata=%x" % (StatChan,Rawdata))
            while aligned == 0:
                if i > 50000:
                    isEnd = True
                else:
                    value = mem_data[i]
                    i = i + 1
                    if value < 0:
                        isEnd = True
                    else:
                        for k in range(7):
                            val[k] = val[k + 1]
                        val[7] = value
                        Rawdata = val[0] << (96 + 128) | val[1] << (64 + 128) | val[2] << (32 + 128) | val[3] << 128 | val[4] << 96 | val[5] << 64 | val[6] << 32 | val[7]
                    # end if
                    if Rawdata == 0x3c5c_7c5c_0000_0000_0000_0000_1234_4321_7d6d_7a5a_0000_0000_0000_0000_5566_6655:
                        #print("aligned here")
                        aligned = 1
                        # Filler frame without channel - use chan=9
                        ChStat[2][9] = ChStat[2][9] + 1;
                    else:
                        #print("not aligned here")
                        aligned = 0
                        # make best attempt to dead reckoning alignment for no-alignment frames 
                        remainder = i % 8
                        if isEnd==0 and remainder==1:  
                            ErrNA  = val[0]>>31&1 
                            ChanNA = val[0]>>27&0xF
                            if ChanNA>9:
                                print("Not aligned i=%i bad chan=%i  Rawdata=%x" % (i,ChanNA,Rawdata))
                                ChanNA = 9
                            else:
                                print("Not aligned i=%i chan=%i  Rawdata=%x" % (i,ChanNA,Rawdata))
                            #end if
                            ChStat[ErrNA][ChanNA] = ChStat[ErrNA][ChanNA] + 1 
                        #end if remainer = 1 
                    # end if
                if isEnd:
                    break
            # end while aligned
        # end if aligned
    # end for 6250. One buffer is done.

    #print("loops ended")
        
    for m in range(10):
        ChanCnt = 0
        for n in range(4):
            ChanCnt = ChanCnt + ChStat[n][m]
        #end for 
        #print non-zero channel stat
        if ChanCnt>0:
            print(" file summary Chan %i: Aligned Err/OK=%i/%i Not aligned Err/OK=%i/%i" % (m,ChStat[3][m],ChStat[2][m],ChStat[1][m],ChStat[0][m]))
        #end if
    #end for
    #print(" line 306 %s finished!" % self.name)


# --------------------------------------------------------------------------#



# ---------------------------------------------------------------------------------------------#
## Current_Monitor
def Current_monitor():
    I2C_Addr = 0x9e >> 1  # I2C address of first LTC2991, note that

    # iic_write(1, I2C_Addr, 0, 0x06, 0x99)       # V1-V2 differential, Filter enabled, V3-V4 differential, Filter enabled
    iic_write(1, I2C_Addr, 0, 0x06, 0x11)  # V1-V2 differential, Filter enabled, V3-V4 differential, Filter enabled
    # print(iic_read(0, I2C_Addr, 1, 0x06))       # read back control register

    iic_write(1, I2C_Addr, 0, 0x01, 0x38)  # V1-V2 and V3-V4 enabled, VCC and T internal enabled

    # print(hex(iic_read(0, I2C_Addr, 1, 0x00)))  # status low 
    # print(hex(iic_read(0, I2C_Addr, 1, 0x01)))  # status high
    V12_Volt = 0
    I12 = 0
    V12_MSB = iic_read(0, I2C_Addr, 1, 0x0C)  # V1-V2 MSB
    V12_LSB = iic_read(0, I2C_Addr, 1, 0x0D)  # V1-V2 LSB
    V12_Valid = (V12_MSB & 0x80) >> 7
    V12_Sign = (V12_MSB & 0x40) >> 6
    if V12_Sign == 0:
        V12_Volt = ((V12_MSB & 0x3f) << 8 | V12_LSB) * 19.075 * 1E-6
    I12 = 982.5 * V12_Volt - 10.489
    # print("V1-V2 volt: %.3f V, I12：%.3f mA"%(V12_Volt, I12))

    V34_Volt = 0
    I34 = 0
    V34_MSB = iic_read(0, I2C_Addr, 1, 0x10)  # V3-V4 MSB
    V34_LSB = iic_read(0, I2C_Addr, 1, 0x11)  # V3-V4 LSB
    V34_Valid = (V34_MSB & 0x80) >> 7
    V34_Sign = (V34_MSB & 0x40) >> 6
    if V34_Sign == 0:
        V34_Volt = ((V34_MSB & 0x3f) << 8 | V34_LSB) * 19.075 * 1E-6
    I34 = 949.0 * V34_Volt + 0.0258
    # print("V3-V4 volt: %.3f V, I34：%.3f mA"%(V34_Volt, I34))

    VCC_MSB = iic_read(0, I2C_Addr, 1, 0x1C)  # VCC MSB
    VCC_LSB = iic_read(0, I2C_Addr, 1, 0x1D)  # VCC LSB

    VCC_Volt = ((VCC_MSB & 0x3f) << 8 | VCC_LSB) * 0.00030518 + 2.5
    # print("VCC volt: %.3f"%VCC_Volt)
    return [I12, I34]


# ---------------------------------------------------------------------------------------------#

# ---------------------------------------------------------------------------------------------#
# # IIC write slave device
# @param mode[1:0] : '0'is 1 bytes read or wirte, '1' is 2 bytes read or write, '2' is 3 bytes read or write
# @param slave[7:0] : slave device address
# @param wr: 1-bit '0' is write, '1' is read
# @param reg_addr[7:0] : register address
# @param data[7:0] : 8-bit write data
def iic_write(mode, slave_addr, wr, reg_addr, data):
    val = mode << 24 | slave_addr << 17 | wr << 16 | reg_addr << 8 | data
    cmd_interpret.write_config_reg(4, 0xffff & val)
    cmd_interpret.write_config_reg(5, 0xffff & (val >> 16))
    time.sleep(0.1)
    cmd_interpret.write_pulse_reg(0x0001)  # reset ddr3 data fifo
    time.sleep(0.1)


# ---------------------------------------------------------------------------------------------#


# ---------------------------------------------------------------------------------------------#
## IIC read slave device
# @param mode[1:0] : '0'is 1 bytes read or wirte, '1' is 2 bytes read or write, '2' is 3 bytes read or write
# @param slave[6:0]: slave device address
# @param wr: 1-bit '0' is write, '1' is read
# @param reg_addr[7:0] : register address
def iic_read(mode, slave_addr, wr, reg_addr):
    val = mode << 24 | slave_addr << 17 | 0 << 16 | reg_addr << 8 | 0x00  # write device addr and reg addr
    cmd_interpret.write_config_reg(4, 0xffff & val)
    cmd_interpret.write_config_reg(5, 0xffff & (val >> 16))
    time.sleep(0.01)
    cmd_interpret.write_pulse_reg(0x0001)  # Sent a pulse to IIC module

    val = mode << 24 | slave_addr << 17 | wr << 16 | reg_addr << 8 | 0x00  # write device addr and read one byte
    cmd_interpret.write_config_reg(4, 0xffff & val)
    cmd_interpret.write_config_reg(5, 0xffff & (val >> 16))
    time.sleep(0.01)
    cmd_interpret.write_pulse_reg(0x0001)  # Sent a pulse to IIC module
    time.sleep(0.1)  # delay 10ns then to read data
    return cmd_interpret.read_status_reg(0) & 0xff


# ---------------------------------------------------------------------------------------------#



# ------------------------------------------------------------------------------------------------#
## if statement
if __name__ == "__main__":
    try:  # try socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # initial socket
    except socket.error:
        print("Failed to create socket!")
        sys.exit()
    try:  # try ethernet connection
        s.connect((hostname, port))  # connect socket
    except socket.error:
        print("failed to connect to ip:" + hostname)
    cmd_interpret = command_interpret(s)  # Class instance
    GBCR3_Reg1 = GBCR3_Reg()  # New a class
    try:
        main()  # execute main function
    except KeyboardInterrupt:
        print("\nApplication exit!")
    except:
        print("Command Failed")

    s.close()  # close socket
