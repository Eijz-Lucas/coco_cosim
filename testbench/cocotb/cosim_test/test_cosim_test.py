import cocotb
import logging
from .add_one_cosim import *
from .base import *
from .cosim_test_wrapper import *
from .sys_ctrl import *
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
import os

if "ST" in os.environ:
    mode = "st" if os.environ["ST"] == "1" else "ut"
else:
    mode = "ut"

if mode == "st":
    cocotb.log.info("Running in ST mode")
else:       
    cocotb.log.info("Running in UT mode")

firmware = [
    {"op":"add_one","addr":0, "len":5},
    {"op":"sub_one","len":3},
    {"op":"sub_one","len":2}
]

logging.basicConfig(
    filename='cosim.log',          # 指定输出文件名
    filemode='w',                # 'a' 为追加模式，'w' 为覆盖模式
    level=logging.INFO,          # 设置最低捕获级别
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s' # 日志格式
)

@cocotb.test()
async def test(dut):
    # signal init
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    dut.rst_n.value = 1
    await Timer(20, unit="ns")
    await RisingEdge(dut.clk)
    dut.rst_n.value = 0
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1

    if mode == "st":
    # backdoor write success
        dut.u_single_port_ram.mem[0].value = 10
        dut.u_single_port_ram.mem[1].value = 20
        dut.u_single_port_ram.mem[2].value = 30
        dut.u_single_port_ram.mem[3].value = 40
        dut.u_single_port_ram.mem[4].value = 50
        cocotb.log.info(f"Initial RAM[0]: {dut.u_single_port_ram.mem[0].value}")
        await RisingEdge(dut.clk)
        cocotb.log.info(f"After reset RAM[0]: {dut.u_single_port_ram.mem[0].value}")

    # class init
    cosim_test_wrapper_modules = [("add_one_cosim", add_one_cosim, dut.u_add_one), ("sub_one_cosim", sub_one_cosim, dut.u_sub_one)]
    cosim_test_wrapper_instance = cosim_test_wrapper(dut, cosim_test_wrapper_modules, mode)
    sys_ctrl_instance = sys_ctrl(cosim_test_wrapper_instance, firmware)
    # sim
    await sys_ctrl_instance.execute()