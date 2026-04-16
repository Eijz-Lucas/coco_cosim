from .base import *
import cocotb
import numpy as np
from cocotb.triggers import RisingEdge, ValueChange
from cocotb.clock import Clock

# async def drive_async_ram(addr_sig, rdata_sig, memory):
#     """异步读 RAM：addr 变化 -> rdata 立即更新"""

#     if 'X' in str(addr_sig.value):
#         rdata_sig.value = 0
#     else:
#         rdata_sig.value = int(memory.read(0,int(addr_sig.value),1))

#     while True:
#         await ValueChange(addr_sig)
#         addr = int(addr_sig.value)
#         rdata_sig.value = int(memory.read(0,addr,1))

class sub_one_input_trans(BaseTransaction):
    addr_add:int
    len_add:int
    ram_rdata_add:list
    
class sub_one_output_trans(BaseTransaction):
    fifo_write_data_add:int
    
class sub_one_model(BaseModel):
    def __init__(self, in_queue, exp_queue, name="sub_one_sw_model"):
        super().__init__(in_queue, exp_queue, name)

    def run(self):
        pass

class sub_one_driver(BaseDriver):
    def __init__(self, dut, name="sub_one_driver"):
        super().__init__(dut, name)

    async def run(self, inst):
        pass

class sub_one_output_monitor(BaseMonitor):
    def __init__(self, dut, act_queue, name="sub_one_output_monitor"):
        super().__init__(dut, act_queue, name)

    async def run(self):
        pass

class sub_one_input_monitor(BaseMonitor):
    def __init__(self, dut, in_queue, name="sub_one_input_monitor"):
        super().__init__(dut, in_queue, name)
    
    async def run(self):
        pass
                    
class sub_one_scoreboard(BaseScoreboard):
    def __init__(self, act_queue, exp_queue, name="sub_one_scoreboard"):
        super().__init__(act_queue, exp_queue, name)
        
    async def run(self):
        pass

class sub_one_cosim(CoSimBase):
    def __init__(self, dut):
        super().__init__(dut, sub_one_model, sub_one_driver, sub_one_input_monitor, sub_one_output_monitor, sub_one_scoreboard) 
    
    async def execute(self, inst, memory):
        pass
