import cocotb
import logging
from abc import ABC, abstractmethod
from cocotb.queue import Queue
from dataclasses import dataclass

# ==========================================
# 1. 组件抽象基类定义 (软件模型, Driver, Monitor)
# ==========================================
@dataclass
class BaseTransaction(ABC):
    """
    Moniter, ReferenceModel, ScoreBoard之间传输Transaction
    Driver不驱动Transaction(因为数据由memory被动给出)
    """
    pass

class BaseModel(ABC):
    """
    软件模型基类
    根据input_moniter捕获的输入计算期望结果
    仿真阶段持续运行
    """
    def __init__(self, in_queue, exp_queue, name="SwModel"):
        self.log = logging.getLogger(f"cocotb.{name}")
        self.in_queue = in_queue
        self.exp_queue = exp_queue
        cocotb.start_soon(self.run())

    @abstractmethod
    async def run(self, *args, **kwargs):
        """
        将in_queue的值作为输入，计算期望结果并压入exp_queue  
        """
        pass

class BaseDriver(ABC):
    """
    硬件驱动基类
    只负责将指令和数据转换为物理信号发给DUT
    在UT模式下工作，在ST模式下不实例化
    """
    def __init__(self, dut, name="Driver"):
        self.dut = dut
        self.log = logging.getLogger(f"cocotb.{name}")

    @abstractmethod
    async def run(self, *args, **kwargs):
        pass

class BaseMonitor(ABC):
    """
    硬件监测基类
    检测dut的输入或输出，并压入queue
    仿真阶段持续运行
    """
    def __init__(self, dut, queue, name="Monitor"):
        self.dut = dut
        self.log = logging.getLogger(f"cocotb.{name}")
        self.queue = queue
        cocotb.start_soon(self.run())

    @abstractmethod
    async def run(self, *args, **kwargs):
        pass

class BaseScoreboard(ABC):
    """计分板基类：比对软硬件结果，并根据设定返回特定的结果"""
    def __init__(self, act_queue, exp_queue, name="Scoreboard"):
        self.log = logging.getLogger(f"cocotb.{name}")
        self.exp_queue = exp_queue
        self.act_queue = act_queue
        cocotb.start_soon(self.run())

    @abstractmethod
    async def run(self, *args, **kwargs):
        pass

# ==========================================
# 2. 核心协同验证基类 (CoSimBase)
# ==========================================

class CoSimBase(ABC):
    """软硬件协同验证基类：负责协调软件模型、硬件Driver和Monitor的交互"""
    def __init__(self, dut, model: BaseModel, driver: BaseDriver, input_moniter: BaseMonitor, output_monitor: BaseMonitor, scoreboard: BaseScoreboard, name="CoSimBase"):
        self.dut = dut
        self.log = logging.getLogger(f"cocotb.{name}")
        self.in_queue = Queue() #TODO:Queue能这样用吗，研究一下
        self.act_queue = Queue()
        self.exp_queue = Queue()
        self.model = model(self.in_queue, self.exp_queue)
        self.driver = driver(self.dut)
        self.input_moniter = input_moniter(self.in_queue)
        self.output_monitor = output_monitor(self.act_queue) 
        self.scoreboard = scoreboard(self.act_queue, self.exp_queue)
        
    @abstractmethod
    async def execute(self, *args, **kwargs):
        pass

class CoSimWrapperBase(ABC):
    def __init__(self, modules, mode, *args, **kwargs):
        self.modules = modules
        self.mode = mode
        
    @abstractmethod
    async def execute(self, inst, *args, **kwargs):
        pass
