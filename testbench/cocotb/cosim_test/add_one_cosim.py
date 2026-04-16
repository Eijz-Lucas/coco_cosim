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

class add_one_input_trans(BaseTransaction):
    addr:int
    len:int
    ram_rdata:np.ndarray
    
class add_one_output_trans(BaseTransaction):
    ram_addr:list
    fifo_write_data:np.ndarray
    
class add_one_model(BaseModel):
    def __init__(self, in_queue, exp_queue, name="add_one_sw_model"):
        super().__init__(in_queue, exp_queue, name)

    async def run(self):
        while True:
            if not self.in_queue.empty():
                trans = await self.in_queue.get()
                exp_ram_addr = []
                for i in range(trans.len):
                    exp_ram_addr.append(trans.addr + i)
                exp_fifo_write_data = trans.ram_rdata + 1
                exp_trans = add_one_output_trans(ram_addr=exp_ram_addr, fifo_write_data=exp_fifo_write_data)
                await self.exp_queue.put(exp_trans)

class add_one_driver(BaseDriver):
    def __init__(self, dut, name="add_one_driver"):
        super().__init__(dut, name)

    async def run(self, inst):
        if inst.op == "add_one":
            dut = self.dut
            dut.en_add.value = 1
            dut.len_add.value = inst.len
            dut.addr_add.value = inst.addr
            await RisingEdge(dut.clk)
            dut.en_add.value = 0
            dut.len_add.value = 0
            dut.addr_add.value = 0

class add_one_output_monitor(BaseMonitor):
    def __init__(self, dut, act_queue, name="add_one_output_monitor"):
        super().__init__(dut, act_queue, name)

    async def run(self):
        while True:
            await RisingEdge(self.dut.clk)
            if self.dut.fifo_write_en.value == 1:
                ram_addr = []
                for i in range(self.dut.len_add.value):
                    ram_addr.append(int(self.dut.addr_add.value) + i)
                fifo_write_data = []
                for i in range(self.dut.len_add.value):
                    fifo_write_data.append(int(self.dut.fifo_write_data.value[i*32:(i+1)*32]))

class add_one_input_monitor(BaseMonitor):
    def __init__(self, dut, in_queue, name="add_one_input_monitor"):
        super().__init__(dut, in_queue, name)
    
    async def run(self):
        pass
                    
class add_one_scoreboard(BaseScoreboard):
    def __init__(self, act_queue, exp_queue, name="add_one_scoreboard"):
        super().__init__(act_queue, exp_queue, name)
        
    async def run(self):
        pass

class add_one_cosim(CoSimBase):
    def __init__(self, dut):
        super().__init__(dut, add_one_model, add_one_driver, add_one_input_monitor, add_one_output_monitor, add_one_scoreboard) 
    
    async def execute(self, inst, memory):
        pass
