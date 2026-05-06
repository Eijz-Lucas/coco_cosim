"""
CoCo CoSim Base Classes Module

This module defines the core abstract base classes for the CoCo CoSim framework,
which enables hardware-software co-verification using cocotb.

Classes:
    BaseTransaction: Abstract base for transaction data types
    BaseModel: Abstract base for software reference models
    BaseDriver: Abstract base for hardware drivers
    BaseMonitor: Abstract base for hardware monitors
    BaseScoreboard: Abstract base for result comparison
    CoSimBase: Main co-simulation coordinator
    CoSimWrapperBase: Verification environment wrapper

Decorators:
    always_sample_next: Continuously sample signals on each next clock edge

Usage Example:
    class MyCosim(CoSimBase):
        async def execute(self, data):
            await self.driver.send(data)
"""

import cocotb
import logging
from abc import ABC, abstractmethod
from cocotb.queue import Queue
from cocotb.triggers import RisingEdge, Timer
from cocotb.handle import HierarchyObject
from dataclasses import dataclass
from typing import List, Tuple, Any, Type, Dict, Optional
from functools import wraps


@dataclass
class BaseTransaction(ABC):
    """
    Abstract base class for transaction data.

    Transactions are data structures that carry information between
    Monitor, ReferenceModel, and Scoreboard components.

    Attributes:
        Subclasses should define their own fields for specific transaction types.

    Example:
        @dataclass
        class MyTransaction(BaseTransaction):
            data: int
            addr: int
            valid: bool
    """
    pass


class BaseModel(ABC):
    """
    Abstract base class for software reference models. Must impletment compute() method in subclass.

    A reference model emulates the DUT's behavior in software, computing
    expected results from input transactions for scoreboard comparison.

    Attributes:
        name (str): Instance name for logging identification
        log (Logger): Logger instance for debug messages
        in_queue (Queue): Input queue receiving transactions from input monitor
        exp_queue (Queue): Output queue sending expected results to scoreboard

    Type Args:
        in_queue: Queue for input transactions
        exp_queue: Queue for expected output transactions

    Usage:
        class MyModel(BaseModel):
            async def run(self):
                while True:
                    trans = await self.in_queue.get()
                    result = self.compute(trans)
                    await self.exp_queue.put(result)

            def compute(self, trans):
                return trans.data + 1
    """

    def __init__(
        self,
        in_queue: Queue,
        exp_queue: Queue,
        name: str = "SwModel",
        *args: Any,
        **kwargs: Any
    ) -> None:
        """
        Initialize the reference model.

        Args:
            in_queue: Queue to receive input transactions from input monitor
            exp_queue: Queue to send expected results to scoreboard
            name: Instance name for logging (default: "SwModel")
        """
        self.name: str = name
        self.log: logging.Logger = logging.getLogger(f"cocotb.{name}")
        self.in_queue: Queue = in_queue
        self.exp_queue: Queue = exp_queue
        cocotb.start_soon(self.run(*args, **kwargs))
        self.log.info(f"======== {self.name} Initiated ========")

    async def run(self, *args: Any, **kwargs: Any) -> None:
        """
        Main coroutine for the model.

        Continuously processes transactions from in_queue, computes expected
        results, and places them in exp_queue. Must be implemented by subclass.

        Example:
            async def run(self):
                while True:
                    trans = await self.in_queue.get()
                    result = self.compute(trans)
                    await self.exp_queue.put(result)
        """
        while True:
            in_trans = await self.in_queue.get()
            self.log.info(f"[{self.name} Input] {in_trans}")
            exp_trans = self.compute(in_trans, *args, **kwargs)
            self.log.info(f"[{self.name} Output] {exp_trans}")
            self.exp_queue.put_nowait(exp_trans)

    @abstractmethod
    def compute(self, *args: Any, **kwargs: Any) -> BaseTransaction:
        """
        Compute expected result from input transaction.

        Must be implemented by subclass to define the reference behavior.

        Returns:
            Expected transaction or result data

        Example:
            def compute(self, trans: InputTrans) -> OutputTrans:
                return OutputTrans(data=trans.data + 1)
        """
        pass


class BaseDriver(ABC):
    """
    Abstract base class for hardware drivers. Must impletment run() method in subclass.

    A driver controls DUT input signals to stimulate the design according
    to test scenarios.

    Attributes:
        name (str): Instance name for logging identification
        dut (HierarchyObject): Reference to the DUT hierarchy
        log (Logger): Logger instance for debug messages

    Type Args:
        dut: The DUT handle from cocotb

    Usage:
        class MyDriver(BaseDriver):
            async def run(self, data):
                self.dut.data.value = data
                self.dut.valid.value = 1
                await RisingEdge(self.dut.clk)
                self.dut.valid.value = 0
    """

    def __init__(
        self,
        dut: HierarchyObject,
        name: str = "Driver",
        *args: Any,
        **kwargs: Any
    ) -> None:
        """
        Initialize the driver.

        Args:
            dut: Reference to the DUT hierarchy
            name: Instance name for logging (default: "Driver")
        """
        self.name: str = name
        self.dut: HierarchyObject = dut
        self.log: logging.Logger = logging.getLogger(f"cocotb.{name}")
        self.log.info(f"======== {self.name} Initiated ========")

    @abstractmethod
    async def run(self, *args: Any, **kwargs: Any) -> None:
        """
        Main driver execution method.

        Drives signals to the DUT based on test inputs. Must be implemented
        by subclass.

        Example:
            async def run(self, data: int):
                self.dut.data.value = data
                self.dut.valid.value = 1
                await RisingEdge(self.dut.clk)
        """
        pass


def always_sample_next(time: int = 10, unit: str = "ns"):
    """
    Decorator to continuously sample signals on each next clock edge.

    This decorator creates an infinite loop that samples signals
    on every clock edge after a specified delay.

    Args:
        time (int): Delay time before sampling (default: 10)
        unit (str): Time unit (default: 'ns')

    Returns:
        Decorator function

    Usage:
        @always_sample_next(time=5, unit='ns')
        async def monitor_signals(self):
            self.log.info(f"Data: {self.dut.data.value}")
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            instance = getattr(func, "__self__", args[0] if args else None)
            if instance is None:
                raise ValueError("Cannot find the instance (self) to access dut.clk")
            while True:
                await Timer(time, unit=unit)
                await func(*args, **kwargs)
                await RisingEdge(instance.dut.clk)
        return wrapper
    return decorator


class BaseMonitor(ABC):
    """
    Abstract base class for hardware monitors. Must implement sample() method in subclass.

    A monitor observes DUT signals, captures transactions, and sends them
    to queues for model processing or scoreboard comparison.

    Attributes:
        name (str): Instance name for logging identification
        dut (HierarchyObject): Reference to the DUT hierarchy
        log (Logger): Logger instance for debug messages
        queue (Queue): Queue for sending captured transactions

    Type Args:
        dut: The DUT handle from cocotb
        queue: Queue to send monitored transactions

    Usage:
        class MyInputMonitor(BaseMonitor):
            async def run(self):
                while True:
                    await RisingEdge(self.dut.clk)
                    if self.dut.valid.value:
                        trans = InputTrans(data=self.dut.data.value)
                        await self.queue.put(trans)
    """

    def __init__(
        self,
        dut: HierarchyObject,
        queue: Queue,
        name: str = "Monitor",
        clk_period: int = 10,
        unit: str = "ns",
        *args: Any,
        **kwargs: Any
    ) -> None:
        """
        Initialize the monitor.

        Args:
            dut: Reference to the DUT hierarchy
            queue: Queue to send captured transactions
            name: Instance name for logging (default: "Monitor")
        """
        self.name: str = name
        self.dut: HierarchyObject = dut
        self.log: logging.Logger = logging.getLogger(f"cocotb.{name}")
        self.queue: Queue = queue
        self.clk_period: int = clk_period
        self.unit: str = unit
        cocotb.start_soon(self.run(*args, **kwargs))
        self.log.info(f"======== {self.name} Initiated ========")

    async def run(self, *args: Any, **kwargs: Any) -> None:
        decorator = always_sample_next(time=self.clk_period, unit=self.unit)
        always_sample = decorator(self.sample)
        await always_sample(*args, **kwargs)

    @abstractmethod
    async def sample(self, *args: Any, **kwargs: Any) -> None:
        pass


class BaseScoreboard(ABC):
    """
    Abstract base class for scoreboards.

    A scoreboard compares actual DUT outputs with expected results from
    the reference model, tracking matches and mismatches.

    Attributes:
        name (str): Instance name for logging identification
        log (Logger): Logger instance for debug messages
        exp_queue (Queue): Queue receiving expected results from model
        act_queue (Queue): Queue receiving actual results from output monitor
        match_count (int): Number of successful comparisons
        error_count (int): Number of mismatched comparisons

    Type Args:
        act_queue: Queue with actual DUT output transactions
        exp_queue: Queue with expected model output transactions

    Usage:
        class MyScoreboard(BaseScoreboard):
            async def run(self):
                while True:
                    act = await self.act_queue.get()
                    exp = await self.exp_queue.get()
                    if act.data == exp.data:
                        self.match_count += 1
                    else:
                        self.error_count += 1
    """

    def __init__(
        self,
        act_queue: Queue,
        exp_queue: Queue,
        name: str = "Scoreboard",
        *args: Any,
        **kwargs: Any
    ) -> None:
        """
        Initialize the scoreboard.

        Args:
            act_queue: Queue receiving actual DUT outputs
            exp_queue: Queue receiving expected model outputs
            name: Instance name for logging (default: "Scoreboard")
        """
        self.name: str = name
        self.log: logging.Logger = logging.getLogger(f"cocotb.{name}")
        self.exp_queue: Queue = exp_queue
        self.act_queue: Queue = act_queue
        self.match_count: int = 0
        self.error_count: int = 0
        cocotb.start_soon(self.run(*args, **kwargs))
        self.log.info(f"======== {self.name} Initiated ========")

    async def run(self, *args: Any, **kwargs: Any) -> None:
        """
        Main scoreboard comparison coroutine.

        Compares actual and expected transactions, updating match/error
        counts. Must be implemented by subclass.

        Example:
            async def run(self):
                while True:
                    act = await self.act_queue.get()
                    exp = await self.exp_queue.get()
                    if self.compare(act, exp):
                        self.match_count += 1
                    else:
                        self.error_count += 1
        """
        while True:
            act_trans = await self.act_queue.get()
            exp_trans = await self.exp_queue.get()

            self.log.info(f"[{self.name} get Actual Trans] {act_trans}")
            self.log.info(f"[{self.name} get Expected Trans] {exp_trans}")
            self.compare(act_trans, exp_trans, *args, **kwargs)

    def compare(self, act_trans, exp_trans, *args, **kwargs) -> bool:
        """
        Compare actual transaction with expected transaction.

        Args:
            act_trans (Any): Actual transaction from hardware.
            exp_trans (Any): Expected transaction from reference model.

        Returns:
            bool: True if matched, False if mismatched.
        """
        if act_trans == exp_trans:
            self.match_count += 1
            self.log.info(
                f"[{self.name}] MATCH! match_count={self.match_count}")
            return True
        else:
            self.error_count += 1
            self.log.error(
                f"[Result] MISMATCH! error_count={self.error_count}")
            return False


class CoSimBase(ABC):
    """
    Main hardware-software co-simulation coordinator base class.

    Integrates model, driver, monitors, and scoreboard for complete
    co-verification of a hardware module.

    Attributes:
        name (str): Instance name for logging identification
        dut (HierarchyObject): Reference to the DUT hierarchy
        log (Logger): Logger instance for debug messages
        in_queue (Queue): Queue for input transactions (input monitor -> model)
        act_queue (Queue): Queue for actual outputs (output monitor -> scoreboard)
        exp_queue (Queue): Queue for expected outputs (model -> scoreboard)
        model (BaseModel): Reference model instance
        driver (BaseDriver): Driver instance
        input_moniter (BaseMonitor): Input monitor instance
        output_monitor (BaseMonitor): Output monitor instance
        scoreboard (BaseScoreboard): Scoreboard instance
        executed_inst_num (int): Counter for executed instructions

    Type Args:
        dut: The DUT handle from cocotb
        model: Reference model class
        driver: Driver class
        input_moniter: Input monitor class
        output_monitor: Output monitor class
        scoreboard: Scoreboard class

    Usage:
        class MyCosim(CoSimBase):
            async def execute(self, data: int):
                self.executed_inst_num += 1
                await self.driver.run(data)

            async def wait_done(self):
                await self.wait_compare()
                self.log.info(f"Matches: {self.scoreboard.match_count}")
    """

    def __init__(
        self,
        dut: HierarchyObject,
        model: Type[BaseModel],
        driver: Type[BaseDriver],
        input_moniter: Type[BaseMonitor],
        output_monitor: Type[BaseMonitor],
        scoreboard: Type[BaseScoreboard],
        mode: str = "hw",
        level: str = "ut",
        name: str = "CoSimBase",
        *args: Any,
        **kwargs: Any
    ) -> None:
        """
        Initialize the co-simulation environment.

        Args:
            dut: Reference to the DUT hierarchy
            model: Reference model class (not instance)
            driver: Driver class (not instance)
            input_moniter: Input monitor class (not instance)
            output_monitor: Output monitor class (not instance)
            scoreboard: Scoreboard class (not instance)
            mode: Verification mode ("hw" or "sw")
            level: Verification level ("ut" or "st")
            name: Instance name for logging (default: "CoSimBase")
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
        """
        self.name: str = name
        if mode not in ("hw", "sw"):
            raise ValueError(
                f"Invalid mode: {mode} for {self.name}. Must be 'hw' or 'sw'."
            )
        else:
            self.mode: str = mode
        if level not in ("ut", "st"):
            raise ValueError(
                f"Invalid level: {level} for {
                    self.name}. Must be 'ut' or 'st'."
            )
        else:
            self.level: str = level
        self.dut: HierarchyObject = dut
        self.log: logging.Logger = logging.getLogger(f"cocotb.{name}")
        self.in_queue: Queue = Queue()
        self.act_queue: Queue = Queue()
        self.exp_queue: Queue = Queue()
        self.model: BaseModel = model(self.in_queue, self.exp_queue)
        self.driver: BaseDriver = driver(self.dut)
        self.input_moniter: BaseMonitor = input_moniter(self.dut, self.in_queue)
        self.output_monitor: BaseMonitor = output_monitor(self.dut, self.act_queue)
        self.scoreboard: BaseScoreboard = scoreboard(self.act_queue, self.exp_queue)
        self.executed_inst_num: int = 0
        self.log.info(f"******** {self.name} Initiated ********")

    async def execute(self, *args: Any, **
                      kwargs: Any) -> Optional[BaseTransaction]:
        """
        General entry point to execute an operation.
        Dispatches to `execute_unit_test` or `execute_system_test` based on `self.level`.
        """
        if self.level == "ut":
            await self.execute_unit_test(*args, **kwargs)
        elif self.level == "st":
            await self.execute_system_test(*args, **kwargs)

    @abstractmethod
    async def execute_unit_test(self, *args: Any, **kwargs: Any) -> Optional[BaseTransaction]:
        """
        Execute a unit test operation.

        Must be implemented by subclass to define how to drive inputs
        and increment `executed_inst_num`.
        """
        pass

    @abstractmethod
    async def execute_system_test(self, *args: Any, **kwargs: Any) -> Optional[BaseTransaction]:
        """
        Execute a system-level test operation.

        Must be implemented by subclass to define how to drive inputs
        for system-level verification.
        """
        pass

    async def wait_compare(self) -> None:
        """
        Wait for all comparisons to complete.

        Blocks until the total number of matches and errors equals
        the number of executed instructions.

        Usage:
            await cosim.wait_compare()
            print(f"Matches: {cosim.scoreboard.match_count}")
        """
        while True:
            if self.scoreboard.match_count + self.scoreboard.error_count == self.executed_inst_num:
                break
            else:
                await RisingEdge(self.dut.clk)


class CoSimWrapperBase(ABC):
    """
    Verification environment wrapper base class.

    Manages multiple CoSim instances and shared resources (RAM, FIFO)
    for system-level verification. Supports UT and ST modes.

    Attributes:
        dut (HierarchyObject): Reference to the DUT hierarchy
        level (str): Verification level ("UT" or "ST")
        name (str): Instance name for logging identification
        log (Logger): Logger instance for debug messages
        modules (List[tuple[str, Type, HierarchyObject, Dict]]): List of module instances

    Type Args:
        dut: The DUT handle from cocotb
        modules: List of module specifications as tuples:
            (name: str, class: Type, handle: HierarchyObject, config: Dict)
        level: Verification level - "UT" or "ST"

    Usage:
        class MyWrapper(CoSimWrapperBase):
            def __init__(self, dut, level):
                modules = [
                    ("add_one", AddOneCosim, dut.add_one_inst, (), {}),
                    ("sub_one", SubOneCosim, dut.sub_one_inst, (), {}),
                ]
                super().__init__(dut, modules, level)

            async def execute(self, inst: dict):
                op = inst["op"]
                if op == "add_one":
                    await self.modules["add_one"].execute(inst)
                elif op == "sub_one":
                    await self.modules["sub_one"].execute(inst)
    """

    def __init__(
        self,
        dut: HierarchyObject,
        modules: List[tuple[str, Type, HierarchyObject, Dict]],
        level: str = "ut",
        name: str = "CosimWrapperBase",
        *args: Any,
        **kwargs: Any
    ) -> None:
        """
        Initialize the verification environment wrapper, support nesting.

        Args:
            dut: Reference to the DUT hierarchy
            modules: List of module specifications, each tuple contains:
                - name (str): Module instance name
                - class (Type): Module class (not instance)
                - handle (HierarchyObject): DUT handle for the module
                - args (Optional[Tuple]): Positional args for module init
                - kwargs (Optional[Dict]): Keyword args for module init
            level: Verification level ("UT" or "ST")
            name: Instance name for logging (default: "CosimWrapperBase")
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
        """
        self.dut: HierarchyObject = dut
        self.name: str = name
        self.log: logging.Logger = logging.getLogger(f"cocotb.{name}")
        self.modules: Dict[str, Any] = {}
        if level not in ("ut", "st"):
            raise ValueError(
                f"Invalid level: {level} for {
                    self.name}. Must be 'ut' or 'st'."
            )
        else:
            self.level: str = level
        for module in modules:
            name, cls, handle, cfg = module[0], module[1], module[2], module[3]
            self.modules[name] = cls(handle, *args, **cfg, **kwargs)
        if self.level == "st":
            for module in self.modules.values():
                if isinstance(module, CoSimBase):
                    if module.mode == "sw":
                        raise RuntimeError(f"{module}'s mode is sw in {self.name} system test")

    async def execute(self, *args: Any, **kwargs: Any) -> None:
        """
        General entry point to execute firmware instruction.
        Dispatches to unit test or system test execution based on `self.level`.
        """
        if self.level == "ut":
            await self.execute_unit_test(*args, **kwargs)
        elif self.level == "st":
            await self.execute_system_test(*args, **kwargs)

    @abstractmethod
    async def execute_unit_test(self, *args: Any, **kwargs: Any) -> Optional[Any]:
        """
        Execute unit test routing. Needs to be implemented by subclass.
        """
        pass

    @abstractmethod
    async def execute_system_test(self, *args: Any, **kwargs: Any) -> Optional[Any]:
        """
        Execute system test routing. Needs to be implemented by subclass.
        """
        pass

    async def wait_compare(self) -> None:
        """
        Wait for all module comparisons to complete.

        Calls wait_compare() on each module instance.

        Usage:
            await wrapper.wait_compare()
            for name, module in wrapper.modules.items():
                print(f"{name}: {module.scoreboard.match_count} matches")
        """
        for module in self.modules.values():
            await module.wait_compare()
