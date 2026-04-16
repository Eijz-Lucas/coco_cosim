import cocotb
from .add_one_cosim import *
from .base import *
from .cosim_test_wrapper import *
from .sys_ctrl import *
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge

firmware = [
    {"op":"add_one","addr":0, "len":5}
]

@cocotb.test()
async def test(dut):
    # class init
    cosim_test_wrapper_instance = cosim_test_wrapper(dut, 'ut')
    sys_ctrl_instance = sys_ctrl(cosim_test_wrapper_instance, firmware)
    # signal init
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.rst_n.value = 0
    dut.en_add.value = 0
    dut.en_sub.value = 0
    dut.len_add.value = 0
    dut.len_sub.value = 0
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    dut.rst_n.value = 0
    sys_ctrl_instance.execute()
    