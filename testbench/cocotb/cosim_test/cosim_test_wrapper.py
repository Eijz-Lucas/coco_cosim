from .base import *
from .memory import *
from .add_one_cosim import *
from .sub_one_cosim import *

class ram_model(RAM):
    def __init__(self, size, depth, block_num, addr_sig, rdata_sig):
        super().__init__(size, depth, block_num)
        self.addr_sig = addr_sig
        self.rdata_sig = rdata_sig
        cocotb.start_soon(self.run())
        
    async def run(self):
        if 'X' in str(self.addr_sig.value):
            self.rdata_sig.value = 0
        else:
            # data = self.read(0,int(self.addr_sig.value),1)
            self.rdata_sig.value = int(self.read(0,int(self.addr_sig.value),1)[0][0])
        while True:
            await ValueChange(self.addr_sig)
            self.rdata_sig.value = int(self.read(0,int(self.addr_sig.value),1)[0][0])

class fifo_model(FIFO):
    def __init__(self, size, depth, clk_sig, fifo_read_en_sig, fifo_read_data_sig, fifo_write_en_sig_0, fifo_write_data_sig_0,
                 fifo_write_en_sig_1, fifo_write_data_sig_1):
        super().__init__(size, depth)
        self.fifo_read_en_sig = fifo_read_en_sig
        self.fifo_read_data_sig = fifo_read_data_sig
        self.fifo_write_en_sig_0 = fifo_write_en_sig_0
        self.fifo_write_data_sig_0 = fifo_write_data_sig_0
        self.fifo_write_en_sig_1 = fifo_write_en_sig_1
        self.fifo_write_data_sig_1 = fifo_write_data_sig_1
        self.clk_sig = clk_sig
        cocotb.start_soon(self.run())
        
    async def run(self):
        async def read_coroutine():
            while True:
                await ValueChange(self.fifo_read_en_sig)
                if 'X' in str(self.fifo_read_en_sig.value):
                    self.fifo_read_data_sig.value = 0
                if self.fifo_read_en_sig.value == 1:
                    self.fifo_read_data_sig.value = int(self.pop(1)[0][0])
        
        async def write_coroutine():
            while True:
                await RisingEdge(self.clk_sig)
                if self.fifo_write_en_sig_0.value == 1:
                    self.push(np.array([[int(self.fifo_write_data_sig_0.value)]]))
                if self.fifo_write_en_sig_1.value == 1:
                    self.push(np.array([[int(self.fifo_write_data_sig_1.value)]]))
        cocotb.start_soon(read_coroutine())
        cocotb.start_soon(write_coroutine())
   
class cosim_test_wrapper(CoSimWrapperBase):
    def __init__(self, dut, modules, mode, name="cosim_test_wrapper"):
        super().__init__(dut, modules, mode, name)
        self.ram = ram_model(1,16,1,dut.u_add_one.ram_addr,dut.u_add_one.ram_rdata)
        self.fifo = fifo_model(1,16,dut.clk,dut.u_sub_one.fifo_read_en, dut.u_sub_one.fifo_read_data, dut.u_add_one.fifo_write_en, dut.u_add_one.fifo_write_data, dut.u_sub_one.fifo_write_en, dut.u_sub_one.fifo_write_data)

    async def execute(self, inst):
        if(self.mode == "ut"):
            await self.wait_compare()
            if(inst["op"] == "add_one"):
                await self.modules["add_one_cosim"].execute(inst)
            if(inst["op"] == "sub_one"):
                await self.modules["sub_one_cosim"].execute(inst)
        elif(self.mode == "st"):
            pass