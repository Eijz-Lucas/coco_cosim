from .base import *
import cocotb
import numpy as np
from cocotb.triggers import RisingEdge, ValueChange, Event, ReadOnly
from cocotb.clock import Clock

@dataclass
class sub_one_input_trans(BaseTransaction):
    len:int
    fifo_read_data:np.array

    def __eq__(self, other):
        if not isinstance(other, sub_one_input_trans):
            return False
        if self.len != other.len:
            return False
        return np.array_equal(self.fifo_read_data, other.fifo_read_data)

@dataclass
class sub_one_output_trans(BaseTransaction):
    fifo_write_data:np.array

    def __eq__(self, other):
        if not isinstance(other, sub_one_output_trans):
            return False
        return np.array_equal(self.fifo_write_data, other.fifo_write_data)
   
class sub_one_model(BaseModel):
    def __init__(self, in_queue, exp_queue, name="sub_one_sw_model"):
        super().__init__(in_queue, exp_queue, name)

    async def run(self):
        while True:
            trans = await self.in_queue.get()
            self.log.info(f"[Model Input] len={trans.len}, fifo_read_data={trans.fifo_read_data}")
            exp_fifo_write_data = trans.fifo_read_data-1
            exp_trans = sub_one_output_trans(fifo_write_data=exp_fifo_write_data)
            self.log.info(f"[Model Output] exp_fifo_write_data={exp_fifo_write_data}")
            self.exp_queue.put_nowait(exp_trans)

class sub_one_driver(BaseDriver):
    def __init__(self, dut, name="sub_one_driver"):
        super().__init__(dut, name)

    async def run(self, inst):
        self.log.info(f"[Driver] inst={inst}")
        if inst["op"] == "sub_one":
            dut = self.dut
            await RisingEdge(dut.clk)
            dut.en.value = 1
            dut.len.value = inst["len"]
            await RisingEdge(dut.clk)
            dut.en.value = 0
            dut.len.value = 0
            
class sub_one_output_monitor(BaseMonitor):
    def __init__(self, dut, act_queue, name="sub_one_output_monitor"):
        super().__init__(dut, act_queue, name)

    async def run(self):
        data_list = []
        while True:
            await RisingEdge(self.dut.clk)
            if self.dut.fifo_write_en.value == 1:
                data = int(self.dut.fifo_write_data.value)
                data_list.append(data)
            else:
                if len(data_list) > 0:
                    fifo_write_data = np.array(data_list)
                    output_trans = sub_one_output_trans(fifo_write_data=fifo_write_data)
                    self.queue.put_nowait(output_trans)
                    self.log.info(f"[Output Monitor PUT] fifo_write_data={fifo_write_data}")
                    data_list.clear()
                    
class sub_one_input_monitor(BaseMonitor):
    def __init__(self, dut, in_queue, name="sub_one_input_monitor"):
        super().__init__(dut, in_queue, name)
    
    async def run(self):
        data_list = []
        while True:
            await RisingEdge(self.dut.clk)
            await ReadOnly() #TODO??????????
            if self.dut.en.value == 1: 
                length = int(self.dut.len.value)
                # cocotb.log.info(f"get en========")
            if self.dut.fifo_read_en.value == 1:
                # cocotb.log.info(f"busy {self.dut.busy.value}")
                data_list.append(int(self.dut.fifo_read_data.value)) 
                # cocotb.log.info(f"read data{data_list}")
            else:
                if len(data_list) > 0:
                    fifo_read_data=np.array(data_list)
                    trans = sub_one_input_trans(len=length, fifo_read_data=fifo_read_data)
                    self.log.info(f"[Input Monitor PUT] len={length}, ram_rdata={fifo_read_data}")
                    self.queue.put_nowait(trans)
                    data_list.clear()
                    
class sub_one_scoreboard(BaseScoreboard):
    def __init__(self, act_queue, exp_queue, name="sub_one_scoreboard"):
        super().__init__(act_queue, exp_queue, name)
        
    async def run(self):
        while True:
            actual_trans = await self.act_queue.get()
            expected_trans = await self.exp_queue.get()

            self.log.info(f"[Compare] Actual fifo_data: {actual_trans.fifo_write_data}")
            self.log.info(f"[Compare] Expected fifo_data: {expected_trans.fifo_write_data}")

            if actual_trans == expected_trans:
                self.match_count += 1
                self.log.info(f"[Result] MATCH! match_count={self.match_count}")
            else:
                self.error_count += 1
                self.log.error(f"[Result] MISMATCH! error_count={self.error_count}")
    
class sub_one_cosim(CoSimBase):
    def __init__(self, dut, name="sub_one_cosim"):
        super().__init__(dut, sub_one_model, sub_one_driver, sub_one_input_monitor, sub_one_output_monitor, sub_one_scoreboard, name) 
    
    async def execute(self, inst):
        while True:
            await RisingEdge(self.dut.clk)
            if(self.dut.busy.value == 0):
                break
        await self.driver.run(inst)
        self.executed_inst_num = self.executed_inst_num+1