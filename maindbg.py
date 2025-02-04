#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import time
import datetime
import socket

from GBCR3_Reg import GBCR3_Reg 
from command_interpret import *

def main():
    userdefinedir = "GBCR3_SEE_Test"
    todaystr = "QAResults_6"
    timestr = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
    userdefine_dir = f"{todaystr}/{timestr}"

    os.makedirs(userdefine_dir, exist_ok=True)

    num_file = int(sys.argv[1])
    store_dict = userdefine_dir

    GBCR3_Reg1 = GBCR3_Reg()
    for ch in range(1, 8):
        GBCR3_Reg1.set_channel_params(ch, CML_AmplSel=7, CTLE_MFSR=10, CTLE_HFSR=7)
    
    GBCR3_Reg1.set_register('Tx1_Dis_DL_BIAS', 0, 0x1)
    GBCR3_Reg1.set_register('Tx2_Dis_DL_BIAS', 0, 0x1)

    iic_write_val = GBCR3_Reg1.get_config_vector()
    print(f"Written values: {[hex(val) for val in iic_write_val]}")

    Receive_data(store_dict, num_file)

    print("All jobs are done!")


if __name__ == "__main__":
    
    hostname = '192.168.2.6'
    port = 1024
    
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((hostname, port))
    except socket.error as e:
        print(f"Failed to connect: {e}")
        sys.exit()
    
    cmd_interpret = command_interpret(s)

    try:
        main()
    except KeyboardInterrupt:
        print("\nApplication exit!")
    except Exception as e:
        print(f"Command Failed: {e}")

    s.close()