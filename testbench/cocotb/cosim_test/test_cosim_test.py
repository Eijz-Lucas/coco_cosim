import cocotb
import logging
from .add_one_cosim import *
from .base import *
from .cosim_test_wrapper import *
from .sys_ctrl import *
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Combine
import os

if "ST" in os.environ:
    level = "st" if os.environ["ST"] == "1" else "ut"
else:
    level = "ut"

if level == "st":
    cocotb.log.info("Running in ST mode")
else:
    cocotb.log.info("Running in UT mode")

firmware = [
    {"op": "add_one", "addr": 0, "len": 5},
    {"op": "sub_one", "len": 3},
    {"op": "sub_one", "len": 2},
    {"op": "add_one", "addr": 0, "len": 5},
    {"op": "sub_one", "len": 3},
    {"op": "sub_one", "len": 2}
]

simlogger = SimLogger()
stream_filter = SimLogger.create_filter(
    level=logging.INFO, message='REPORT', reverse=True)
simlogger.set_stream(stream_filter)
sequence_filter = SimLogger.create_filter(name="BaseSequencer")
SimLogger.add_file_handler("sim.log", filters=[sequence_filter])


class cosim_test_sequencer(BaseSequencer):
    def __init__(self, max_size=10, *args, **kwargs):
        super().__init__(max_size=max_size, *args, **kwargs)


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

    if level == "st":
        # backdoor write success
        dut.u_single_port_ram.mem[0].value = 10
        dut.u_single_port_ram.mem[1].value = 20
        dut.u_single_port_ram.mem[2].value = 30
        dut.u_single_port_ram.mem[3].value = 40
        dut.u_single_port_ram.mem[4].value = 50
        cocotb.log.info(f"Initial RAM[0]: {dut.u_single_port_ram.mem[0].value}")
        await RisingEdge(dut.clk)
        cocotb.log.info(f"After one cycle RAM[0]: {dut.u_single_port_ram.mem[0].value}")

    # class init
    if level == "ut":
        cosim_test_wrapper_modules = [
            ("add_one_cosim", add_one_cosim, {
             "dut": dut.u_add_one, "mode": "hw", "level": "ut"}),
            ("sub_one_cosim", sub_one_cosim,  {
             "dut": dut.u_sub_one, "mode": "hw", "level": "ut"})
        ]
    else:
        cosim_test_wrapper_modules = [
            ("add_one_cosim", add_one_cosim, {
             "dut": dut.u_add_one, "mode": "hw", "level": "st"}),
            ("sub_one_cosim", sub_one_cosim, {
             "dut": dut.u_sub_one, "mode": "hw", "level": "st"})
        ]
    cosim_test_wrapper_instance = cosim_test_wrapper(
        dut, cosim_test_wrapper_modules, level=level)
    firmware_iterator = iter(firmware)
    cosim_test_sequencer_instance = cosim_test_sequencer()

    # sim
    await cosim_test_sequencer_instance.run(cosim_test_wrapper_instance, firmware_iterator)
    await cosim_test_wrapper_instance.wait_compare()

    # report
    cosim_test_wrapper_instance.report()
    assert cosim_test_wrapper_instance.success
