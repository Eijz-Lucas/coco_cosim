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
            exp_ram_addr = []
            for i in range(trans.len):
                exp_ram_addr.append(trans.addr + i)
            exp_fifo_write_data = trans.ram_rdata + 1
            exp_trans = add_one_output_trans(ram_addr=exp_ram_addr, fifo_write_data=exp_fifo_write_data)
            self.log.info(f"[Model Output] exp_ram_addr={exp_ram_addr}, exp_fifo_data={exp_fifo_write_data}")
            self.exp_queue.put_nowait(exp_trans)

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

    async def run(self):
        data_list = [] 
        ram_addr_list = [] 
        while True:
            await RisingEdge(self.dut.clk) 
            await ReadOnly()
            if self.dut.busy.value == 1:
                ram_addr_list.append(int(self.dut.ram_addr.value))
            if self.dut.fifo_write_en.value == 1:
                data = int(self.dut.fifo_write_data.value)
                data_list.append(data)
            else:
                if len(data_list) > 0:
                    ram_addr_list.pop()
                    fifo_write_data = np.array(data_list)
                    output_trans = add_one_output_trans(ram_addr = ram_addr_list.copy(), fifo_write_data=fifo_write_data)
                    self.queue.put_nowait(output_trans)
                    self.log.info(f"[Output Monitor PUT] ram_addr={ram_addr_list.copy()}, fifo_write_data={fifo_write_data}")
                    # import debugpy
                    # # 监听 5678 端口（你可以换成任意空闲端口）
                    # debugpy.listen(("0.0.0.0", 5679)) 
                    # # 程序会在这里完全冻结，直到你在 VS Code 里点击连接
                    # debugpy.wait_for_client() 
                    data_list.clear()
                    ram_addr_list.clear()

class add_one_input_monitor(BaseMonitor):
    def __init__(self, dut, in_queue, name="add_one_input_monitor"):
        super().__init__(dut, in_queue, name)
    
    async def run(self):
        data_list = []
        while True:
            await RisingEdge(self.dut.clk)
            await ReadOnly()
            if self.dut.en.value == 1: 
                addr = int(self.dut.addr.value)
                length = int(self.dut.len.value)
            if self.dut.busy.value == 1:
                data_list.append(int(self.dut.ram_rdata.value)) 
            else:
                if len(data_list) > 0:
                    data_list.pop()
                    ram_rdata=np.array(data_list)
                    trans = add_one_input_trans(addr=addr, len=length, ram_rdata=ram_rdata)
                    self.log.info(f"[Input Monitor PUT] addr={addr}, len={length}, ram_rdata={ram_rdata}")
                    self.queue.put_nowait(trans)
                    data_list.clear()

class add_one_scoreboard(BaseScoreboard):
    def __init__(self, act_queue, exp_queue, name="add_one_scoreboard"):
        super().__init__(act_queue, exp_queue, name)
        
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
                self.log.error(f"[Result] MISMATCH! error_count={self.error_count}")
                if actual_trans.ram_addr != expected_trans.ram_addr:
                    self.log.error(f"  -> ram_addr mismatch: actual={actual_trans.ram_addr}, expected={expected_trans.ram_addr}")
                if not np.array_equal(actual_trans.fifo_write_data, expected_trans.fifo_write_data):
                    self.log.error(f"  -> fifo_data mismatch")

class add_one_cosim(CoSimBase):
    def __init__(self, dut, name="add_one_cosim"):
        super().__init__(dut, add_one_model, add_one_driver, add_one_input_monitor, add_one_output_monitor, add_one_scoreboard, name) 
    
    async def execute(self, inst):
        while True:
            await RisingEdge(self.dut.clk)
            if(self.dut.busy.value == 0):
                break
        await self.driver.run(inst)
        self.executed_inst_num = self.executed_inst_num+1