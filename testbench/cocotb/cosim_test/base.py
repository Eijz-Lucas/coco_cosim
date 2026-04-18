import cocotb
import logging
from abc import ABC, abstractmethod
from cocotb.queue import Queue
from cocotb.triggers import RisingEdge
from cocotb.handle import HierarchyObject, LogicObject
from dataclasses import dataclass
from typing import List, Tuple, Any, Type, Dict, Optional

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
    def __init__(self, in_queue:Queue, exp_queue:Queue, name:str="SwModel"):
        self.name = name
        self.log = logging.getLogger(f"cocotb.{name}")
        self.in_queue = in_queue
        self.exp_queue = exp_queue
        cocotb.start_soon(self.run())
        self.log.info(f"======== {self.name} Initiated ========")

    @abstractmethod
    async def run(self, *args:Any, **kwargs:Any):
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
    def __init__(self, dut:HierarchyObject, name:str="Driver"):
        self.name = name
        self.dut = dut
        self.log = logging.getLogger(f"cocotb.{name}")
        self.log.info(f"======== {self.name} Initiated ========")

    @abstractmethod
    async def run(self, *args, **kwargs):
        self.log.info(f"{self.name} start")
        pass

class BaseMonitor(ABC):
    """
    硬件监测基类
    检测dut的输入或输出，并压入queue
    仿真阶段持续运行
    """
    def __init__(self, dut:HierarchyObject, queue:Queue, name:str="Monitor"):
        self.name = name
        self.dut = dut
        self.log = logging.getLogger(f"cocotb.{name}")
        self.queue = queue
        cocotb.start_soon(self.run())
        self.log.info(f"======== {self.name} Initiated ========")

    @abstractmethod
    async def run(self, *args:Any, **kwargs:Any):
        pass

class BaseScoreboard(ABC):
    """计分板基类：比对软硬件结果，并根据设定返回特定的结果"""
    def __init__(self, act_queue:Queue, exp_queue:Queue, name:str="Scoreboard"):
        self.name = name
        self.log = logging.getLogger(f"cocotb.{name}")
        self.exp_queue = exp_queue
        self.act_queue = act_queue
        self.match_count = 0
        self.error_count = 0
        cocotb.start_soon(self.run())
        self.log.info(f"======== {self.name} Initiated ========")

    @abstractmethod
    async def run(self, *args:Any, **kwargs:Any):
        pass

# ==========================================
# 2. 核心协同验证基类 (CoSimBase)
# ==========================================

class CoSimBase(ABC):
    """软硬件协同验证基类：负责协调软件模型、硬件Driver和Monitor的交互"""
    def __init__(self, dut:HierarchyObject, model: BaseModel, driver: BaseDriver, 
                 input_moniter: BaseMonitor, output_monitor: BaseMonitor, scoreboard: BaseScoreboard, 
                 name:str="CoSimBase", *args:Any, **kwargs:Any):
        self.name = name
        self.dut = dut
        self.log = logging.getLogger(f"cocotb.{name}")
        self.in_queue = Queue()
        self.act_queue = Queue()
        self.exp_queue = Queue()
        self.model = model(self.in_queue, self.exp_queue)
        self.driver = driver(self.dut)
        self.input_moniter = input_moniter(self.dut, self.in_queue)
        self.output_monitor = output_monitor(self.dut, self.act_queue) 
        self.scoreboard = scoreboard(self.act_queue, self.exp_queue)
        self.executed_inst_num = 0
        self.log.info(f"======== {self.name} Initiated ========")
        
    @abstractmethod
    async def execute(self, *args:Any, **kwargs:Any):
        pass
    
    async def wait_compare(self):
        while True:
            if self.scoreboard.match_count + self.scoreboard.error_count == self.executed_inst_num:
                break
            else:
                await RisingEdge(self.dut.clk)

class CoSimWrapperBase(ABC):
    def __init__(self, dut:HierarchyObject, modules:List[Tuple[str, Type, HierarchyObject, Optional[Tuple], Optional[Dict]]], 
                 mode:str, name:str="CosimWrapperBase", *args:Any, **kwargs:Any):
        self.dut = dut
        self.mode = mode
        self.name = name
        self.modules: Dict[str, Any] = {}
        for module in modules:
            name, cls, handle = module[0], module[1], module[2]
            mod_args = module[3] if len(module) > 3 else ()
            mod_kwargs = module[4] if len(module) > 4 else {}
            self.modules[name] = cls(handle, *mod_args, **mod_kwargs)
        
    @abstractmethod
    async def execute(self, inst:dict, *args, **kwargs):
        pass

    async def wait_compare(self):
        for module in self.modules.values():
            await module.wait_compare()
