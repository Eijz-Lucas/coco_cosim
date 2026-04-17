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
        while True:
            await RisingEdge(self.clk_sig)
            if 'X' in str(self.fifo_read_en_sig.value):
                self.rdata_sig.value = 0
            elif self.fifo_read_en_sig.value == 1:
                self.fifo_read_data_sig.value = int(self.pop(1)[0])
            if self.fifo_write_en_sig_0.value == 1:
                self.push(np.array([[int(self.fifo_write_data_sig_0.value)]]))
            if self.fifo_write_en_sig_1.value == 1:
                self.push(np.array([[int(self.fifo_write_data_sig_1.value)]]))
                
class cosim_test_wrapper:
    def __init__(self, dut, mode):
        self.dut = dut
        self.mode = mode
        self.ram = ram_model(1,16,1,dut.ram_addr_add,dut.ram_rdata_add)
        self.fifo = fifo_model(1,16,dut.clk,dut.fifo_read_en_sub, dut.fifo_read_data_sub, dut.fifo_write_en_add, dut.fifo_write_data_add, dut.fifo_write_en_sub, dut.fifo_write_data_sub)
        self.add_one_cosim = add_one_cosim(dut)
        self.sub_one_cosim = sub_one_cosim(dut)
        self.total_inst_num = [0,0]

    async def execute(self, inst):
        if(self.mode == "ut"):
            if(inst["op"] == "add_one"):
                await self.add_one_cosim.execute(inst)
                self.total_inst_num[0] = self.total_inst_num[0] + 1
        elif(self.mode == "st"):
            pass
    
    def set_drive_done(self):
        self.add_one_cosim.scoreboard.set_drive_done(self.total_inst_num[0])
        self.sub_one_cosim.set_drive_done()

    def clear_done(self):
        self.total_inst_num = [0,0]
        self.add_one_cosim.scoreboard.drive_done.clear()
        self.sub_one_cosim.scoreboard.drive_done.clear()

    async def wait_compare(self):
        await self.add_one_cosim.scoreboard.compare_done.wait()
        await self.sub_one_cosim.wait_compare()