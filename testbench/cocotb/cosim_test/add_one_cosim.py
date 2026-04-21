from .base import *
import cocotb
import numpy as np
from cocotb.triggers import RisingEdge, ValueChange, Timer, Event, ReadOnly
from cocotb.clock import Clock
from cocotb.handle import Force, Release, Freeze

@dataclass
class add_one_input_trans(BaseTransaction):
    addr:int
    len:int
    ram_rdata:np.ndarray
    
    def clear(self):
        self.addr = 0
        self.len = 0
        self.ram_rdata = np.array([])

    @classmethod
    def empty(cls):
        return cls(addr=0, len=0, ram_rdata=np.array([]))

    def __eq__(self, other):
        if not isinstance(other, add_one_input_trans):
            return False
        if self.addr != other.addr or self.len != other.len:
            return False
        return np.array_equal(self.ram_rdata, other.ram_rdata)
    
@dataclass
class add_one_output_trans(BaseTransaction):
    ram_addr:list
    fifo_write_data:np.ndarray

    def clear(self):
        self.ram_addr = []
        self.fifo_write_data = np.array([])

    @classmethod
    def empty(cls):
        return cls(ram_addr=[], fifo_write_data=np.array([]))

    def __eq__(self, other):
        if not isinstance(other, add_one_output_trans):
            return False
        if self.ram_addr != other.ram_addr:
            return False
        return np.array_equal(self.fifo_write_data, other.fifo_write_data)
    
class add_one_model(BaseModel):
    def __init__(self, in_queue, exp_queue, name="add_one_sw_model"):
        super().__init__(in_queue, exp_queue, name)

    async def run(self):
        while True:
            trans = await self.in_queue.get()
            self.log.info(f"[Model Input] addr={trans.addr}, len={trans.len}, ram_rdata={trans.ram_rdata}")
            exp_trans = self.compute(trans)
            self.log.info(f"[Model Output] exp_ram_addr={exp_trans.ram_addr}, exp_fifo_data={exp_trans.fifo_write_data}")
            self.exp_queue.put_nowait(exp_trans)
    
    def compute(self, input_trans: add_one_input_trans) -> add_one_output_trans:
        exp_ram_addr = []
        for i in range(input_trans.len):
            exp_ram_addr.append(input_trans.addr + i)
        exp_fifo_write_data = input_trans.ram_rdata + 1
        exp_trans = add_one_output_trans(ram_addr=exp_ram_addr, fifo_write_data=exp_fifo_write_data)
        return exp_trans 

class add_one_driver(BaseDriver):
    def __init__(self, dut, name="add_one_driver"):
        super().__init__(dut, name)

    async def run(self, inst):
        self.log.info(f"[Driver] inst={inst}")
        if inst["op"] == "add_one":
            dut = self.dut
            dut.en.value = 1
            dut.len.value = inst["len"]
            dut.addr.value = inst["addr"]
            await RisingEdge(dut.clk)
            dut.en.value = 0
            dut.len.value = 0
            dut.addr.value = 0

class add_one_output_monitor(BaseMonitor):
    def __init__(self, dut, act_queue, name="add_one_output_monitor"):
        super().__init__(dut, act_queue, name)
        self.output_trans = add_one_output_trans.empty()

    @always_sample_next()
    async def run(self):
        if self.dut.busy.value == 1:
            self.output_trans.ram_addr.append(int(self.dut.ram_addr.value))
        if self.dut.fifo_write_en.value == 1:
            data = int(self.dut.fifo_write_data.value)
            self.output_trans.fifo_write_data = np.append(self.output_trans.fifo_write_data, data)
        else:
            if len(self.output_trans.fifo_write_data) > 0:
                self.output_trans.clear()
                self.queue.put_nowait(self.output_trans)
                self.log.info(f"[Output Monitor PUT] ram_addr={self.output_trans.ram_addr}, fifo_write_data={self.output_trans.fifo_write_data}")

class add_one_input_monitor(BaseMonitor):
    def __init__(self, dut, in_queue, name="add_one_input_monitor"):
        super().__init__(dut, in_queue, name)
        self.input_trans = add_one_input_trans.empty()
    
    @always_sample_next()
    async def run(self):
        if self.dut.en.value == 1: 
            self.input_trans.addr = int(self.dut.addr.value)
            self.input_trans.len = int(self.dut.len.value)
        if self.dut.busy.value == 1:
            self.input_trans.ram_rdata = np.append(self.input_trans.ram_rdata, int(self.dut.ram_rdata.value))
        else:
            if len(self.input_trans.ram_rdata) > 0:
                self.input_trans.clear()
                self.queue.put_nowait(self.input_trans)
                self.log.info(f"[Input Monitor PUT] addr={self.input_trans.addr}, len={self.input_trans.len}, ram_rdata={self.input_trans.ram_rdata}")
                self.input_trans = add_one_input_trans.empty()

class add_one_scoreboard(BaseScoreboard):
    def __init__(self, act_queue, exp_queue, name="add_one_scoreboard"):
        super().__init__(act_queue, exp_queue, name)
        self.error = Event()
        self.backdoor_queue = Queue()

    async def run(self):
        while True:
            actual_trans = await self.act_queue.get()
            expected_trans = await self.exp_queue.get()

            self.log.info(f"[Compare] Actual ram_addr: {actual_trans.ram_addr}, len={len(actual_trans.ram_addr)}")
            self.log.info(f"[Compare] Expected ram_addr: {expected_trans.ram_addr}, len={len(expected_trans.ram_addr)}")
            self.log.info(f"[Compare] Actual fifo_data: {actual_trans.fifo_write_data}")
            self.log.info(f"[Compare] Expected fifo_data: {expected_trans.fifo_write_data}")

            if actual_trans == expected_trans:
                self.match_count += 1
                self.log.info(f"[Result] MATCH! match_count={self.match_count}")
            else:
                self.error_count += 1
                self.error.set()
                self.backdoor_queue.put_nowait(expected_trans)
                self.log.error(f"[Result] MISMATCH! error_count={self.error_count}")
                if actual_trans.ram_addr != expected_trans.ram_addr:
                    self.log.error(f"  -> ram_addr mismatch: actual={actual_trans.ram_addr}, expected={expected_trans.ram_addr}")
                if not np.array_equal(actual_trans.fifo_write_data, expected_trans.fifo_write_data):
                    self.log.error(f"  -> fifo_data mismatch")    

class add_one_cosim(CoSimBase):
    def __init__(self, dut, name="add_one_cosim"):
        super().__init__(dut, add_one_model, add_one_driver, add_one_input_monitor, add_one_output_monitor, add_one_scoreboard, name) 
    
    async def execute(self, inst, mode = "hw", input_trans = None):
        while True:
            await RisingEdge(self.dut.clk)
            if(self.dut.busy.value == 0):
                break
        if mode == "hw":
            await self.driver.run(inst)
            self.executed_inst_num = self.executed_inst_num+1
        if mode == "sw":
            self.executed_inst_num = self.executed_inst_num+1
            self.scoreboard.match_count += 1
            output_trans = self.model.compute(input_trans)
            self.log.info(f"[SW Execute] inst={inst}, input_trans={input_trans}, output_trans={output_trans}")
            return output_trans