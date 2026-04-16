from .base import *
from .memory import *
from .add_one_cosim import *
from .sub_one_cosim import *

class local_mem(RAM):
    def __init__(self, size, depth, block_num):
        super().__init__(size, depth, block_num)
        cocotb.start_soon(self.run()) 

    async def run(self):
        pass

class accu_mem(FIFO):
    def __init__(self, size, depth):
        super().__init__(size, depth)
        cocotb.start_soon(self.run())
    
    async def run(self):
        pass

class cosim_test_wrapper:
    def __init__(self, dut, mode):
        self.dut = dut
        self.mode = mode
        self.ram = local_mem(1, 16, 1)
        self.fifo = accu_mem(1, 16)
        self.add_one_cosim = add_one_cosim(dut)
        self.sub_one_cosim = sub_one_cosim(dut)

    async def execute(self, inst):
        if(self.mode == "ut"):
            pass
        elif(self.mode == "st"):
            pass