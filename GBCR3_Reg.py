#!/usr/bin/env python
# -*- coding: utf-8 -*-
import copy
'''
GBCR3 TDC Test Block class
'''

#--------------------------------------------------------------------------#
## Manage GBCR3 chip's internal registers map
# Allow combining and disassembling individual registers
class GBCR3_Reg(object):
    ## @var _defaultRegMap default register values
    _defaultRegMap = {
        'CH1_CML_AmplSel'       :   0x7,
        'CH1_EQ_ATT'            :   0x3,
        'CH1_Dis_EQ_LF'         :   0,
        'CH1_CTLE_MFSR'         :   0xb,
        'CH1_CTLE_HFSR'         :   0xb,
        'CH1_Dis_LPF'           :   0,
        'CH1_Dis_DFF'           :   1,
        'CH1_Disable'           :   0,
        'CH2_CML_AmplSel'       :   0x7,
        'CH2_EQ_ATT'            :   0x3,
        'CH2_Dis_EQ_LF'         :   0,
        'CH2_CTLE_MFSR'         :   0xb,
        'CH2_CTLE_HFSR'         :   0xb,
        'CH2_Dis_LPF'           :   0,
        'CH2_Dis_DFF'           :   1,
        'CH2_Disable'           :   0,
        'CH3_CML_AmplSel'       :   0x7,
        'CH3_EQ_ATT'            :   0x3,
        'CH3_Dis_EQ_LF'         :   0,
        'CH3_CTLE_MFSR'         :   0xb,
        'CH3_CTLE_HFSR'         :   0xb,
        'CH3_Dis_LPF'           :   0,
        'CH3_Dis_DFF'           :   1,
        'CH3_Disable'           :   0,
        'CH4_CML_AmplSel'       :   0x7,
        'CH4_EQ_ATT'            :   0x3,
        'CH4_Dis_EQ_LF'         :   0,
        'CH4_CTLE_MFSR'         :   0xb,
        'CH4_CTLE_HFSR'         :   0xb,
        'CH4_Dis_LPF'           :   0,
        'CH4_Dis_DFF'           :   1,
        'CH4_Disable'           :   0,
        'CH5_CML_AmplSel'       :   0x7,
        'CH5_EQ_ATT'            :   0x3,
        'CH5_Dis_EQ_LF'         :   0,
        'CH5_CTLE_MFSR'         :   0xb,
        'CH5_CTLE_HFSR'         :   0xb,
        'CH5_Dis_LPF'           :   0,
        'CH5_Dis_DFF'           :   1,
        'CH5_Disable'           :   0,
        'CH6_CML_AmplSel'       :   0x7,
        'CH6_EQ_ATT'            :   0x3,
        'CH6_Dis_EQ_LF'         :   0,
        'CH6_CTLE_MFSR'         :   0xb,
        'CH6_CTLE_HFSR'         :   0xb,
        'CH6_Dis_LPF'           :   0,
        'CH6_Dis_DFF'           :   1,
        'CH6_Disable'           :   0,
        'CH7_CML_AmplSel'       :   0x7,
        'CH7_EQ_ATT'            :   0x3,
        'CH7_Dis_EQ_LF'         :   0,
        'CH7_CTLE_MFSR'         :   0xb,
        'CH7_CTLE_HFSR'         :   0xb,
        'CH7_Dis_LPF'           :   0,
        'CH7_Dis_DFF'           :   1,
        'CH7_Disable'           :   0,

        'dllCapReset'           :   0,
        'dllEnable'             :   1,
        'dllChargePumpCurrent'  :   0xf,
        'dllForceDown'          :   0,

        'dllClockDelay_CH7'     :   0x5,
        'dllClockDelay_CH6'     :   0x5,
        'dllClockDelay_CH5'     :   0x5,
        'dllClockDelay_CH4'     :   0x5,
        'dllClockDelay_CH3'     :   0x5,
        'dllClockDelay_CH2'     :   0x5,
        'dllClockDelay_CH1'     :   0x5,
        'dllClockDelay_CH0'     :   0x5,

        'Dis_Tx'                :   0,
        'Rx_Equa'               :   0x0,
        'Rx_invData'            :   0,
        'Rx_enTermination'      :   1,
        'Rx_setCM'              :   1,
        'Rx_Enable'             :   1,

        'Tx1_DL_SR'             :   0x5,
        'Tx1_Dis_DL_Emp'        :   0,
        'Tx1_DL_ATT'            :   0x0,
        'Tx1_Dis_DL_LPF_BIAS'   :   0,
        'Tx1_Dis_DL_BIAS'       :   1,

        'Tx2_DL_SR'             :   0x5,
        'Tx2_Dis_DL_Emp'        :   0,
        'Tx2_DL_ATT'            :   0x0,
        'Tx2_Dis_DL_LPF_BIAS'   :   0,
        'Tx2_Dis_DL_BIAS'       :   1,
    }

    ## @var register map local to the class
    _regMap = {}

    def __init__(self):
        self._regMap = copy.deepcopy(self._defaultRegMap)

    ## Setters for each register
    def set_register(self, name, value, mask=0x6):
        if name in self._regMap:
            self._regMap[name] = value & mask
        else:
            raise KeyError(f"Register {name} not found in register map.")

    ## Setting channel-specific parameters
    def set_channel_params(self, channel, CML_AmplSel=None, EQ_ATT=None, CTLE_MFSR=None, CTLE_HFSR=None):
        if 1 <= channel <= 7:
            if CML_AmplSel is not None:
                self.set_register(f'CH{channel}_CML_AmplSel', CML_AmplSel, 0x7)
            if EQ_ATT is not None:
                self.set_register(f'CH{channel}_EQ_ATT', EQ_ATT, 0x3)
            if CTLE_MFSR is not None:
                self.set_register(f'CH{channel}_CTLE_MFSR', CTLE_MFSR, 0xf)
            if CTLE_HFSR is not None:
                self.set_register(f'CH{channel}_CTLE_HFSR', CTLE_HFSR, 0xf)
        else:
            raise ValueError("Channel must be between 1 and 7.")

    ## Get I2C register configuration vector
    def get_config_vector(self):
        reg_value = []
        for ch in range(1, 8):
            reg_value += [
                self._regMap[f'CH{ch}_Dis_EQ_LF'] << 5 | self._regMap[f'CH{ch}_EQ_ATT'] << 3 | self._regMap[f'CH{ch}_CML_AmplSel'],
                self._regMap[f'CH{ch}_CTLE_HFSR'] << 4 | self._regMap[f'CH{ch}_CTLE_MFSR'],
                self._regMap[f'CH{ch}_Disable'] << 2 | self._regMap[f'CH{ch}_Dis_DFF'] << 1 | self._regMap[f'CH{ch}_Dis_LPF']
            ]
        reg_value += [
            self._regMap['dllEnable'] << 1 | self._regMap['dllCapReset'],
            self._regMap['dllForceDown'] << 4 | self._regMap['dllChargePumpCurrent'],
            self._regMap['dllClockDelay_CH7'] << 4 | self._regMap['dllClockDelay_CH6'],
            self._regMap['dllClockDelay_CH5'] << 4 | self._regMap['dllClockDelay_CH4'],
            self._regMap['dllClockDelay_CH3'] << 4 | self._regMap['dllClockDelay_CH2'],
            self._regMap['dllClockDelay_CH1'] << 4 | self._regMap['dllClockDelay_CH0'],
            self._regMap['Rx_Enable'] << 6 | self._regMap['Rx_setCM'] << 5 | self._regMap['Rx_enTermination'] << 4 |
            self._regMap['Rx_invData'] << 3 | self._regMap['Rx_Equa'] << 1 | self._regMap['Dis_Tx'],
            self._regMap['Tx1_DL_ATT'] << 4 | self._regMap['Tx1_Dis_DL_Emp'] << 3 | self._regMap['Tx1_DL_SR'],
            self._regMap['Tx1_Dis_DL_BIAS'] << 1 | self._regMap['Tx1_Dis_DL_LPF_BIAS'],
            self._regMap['Tx2_DL_ATT'] << 4 | self._regMap['Tx2_Dis_DL_Emp'] << 3 | self._regMap['Tx2_DL_SR'],
            self._regMap['Tx2_Dis_DL_BIAS'] << 1 | self._regMap['Tx2_Dis_DL_LPF_BIAS']
        ]
        return reg_value
