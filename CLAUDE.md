# CoCo CoSim - 软硬件协同验证框架

## 项目概述

CoCo CoSim 是一个基于 cocotb 的软硬件协同验证验证框架，支持硬件 (RTL) 与软件模型 (Python) 的联合仿真验证。

## 目录结构

```
coco_cosim/
├── rtl/                           # 硬件设计 (SystemVerilog)
│   ├── cosim_test.sv              # 顶层模块
│   ├── add_one.sv                 # 加一运算模块
│   ├── sub_one.sv                 # 减一运算模块
│   ├── sy_fifo.sv                 # 同步FIFO
│   ├── simple_dual_ram.sv         # 简单双端口RAM
│   └── single_port_ram.sv         # 单端口RAM
│
├── testbench/cocotb/cosim_test/   # Cocotb 验证环境
│   ├── base.py                    # 抽象基类定义
│   ├── add_one_cosim.py           # add_one 模块的协同验证类
│   ├── sub_one_cosim.py           # sub_one 模块的协同验证类
│   ├── cosim_test_wrapper.py      # 验证环境封装
│   ├── sys_ctrl.py                # 系统控制器
│   ├── memory.py                  # 内存模型 (RAM, FIFO)
│   ├── test_cosim_test.py         # 测试用例
│   └── ctb.mk                     # Cocotb makefile
│
├── makefile                       # 项目构建文件
└── synopsys_sim.setup             # Synopsys 仿真配置
```

## 验证框架架构

### 1. 抽象基类 (`base.py`)

框架定义了以下核心抽象基类：

- **BaseTransaction**: Monitor、ReferenceModel、Scoreboard 之间传输的事务
- **BaseModel**: 软件模型基类，根据输入计算期望结果
- **BaseDriver**: 硬件驱动基类，负责驱动 DUT 信号
- **BaseMonitor**: 硬件监测基类，监测 DUT 输入/输出
- **BaseScoreboard**: 计分板基类，比对软硬件结果
- **CoSimBase**: 软硬件协同验证基类，协调各组件交互
- **CoSimWrapperBase**: 验证环境封装基类

### 2. 内存模型 (`memory.py`)

- **FIFO**: 基于 numpy 数组的 FIFO 队列
- **RAM**: 随机存取存储器模型
- **AccuMem**: 累加器内存模型（多块 FIFO 组成）
- **WeightMem**: 权重内存（用于 GEMM/FA 模式）
- **SharedMem**: 共享内存（用于 SA 间共享数据）

### 3. 验证组件

以 `add_one_cosim` 为例：
- **add_one_input_trans**: 输入事务定义
- **add_one_output_trans**: 输出事务定义
- **add_one_model**: 软件参考模型
- **add_one_driver**: 硬件驱动器
- **add_one_input_monitor**: 输入监测器
- **add_one_output_monitor**: 输出监测器
- **add_one_scoreboard**: 计分板
- **add_one_cosim**: 协同验证主类

### 4. 系统控制

- **cosim_test_wrapper**: 验证环境顶层封装，集成 RAM、FIFO 和各模块的 cosim 实例
- **sys_ctrl**: 系统控制器，执行固件指令序列

## 运行仿真

```bash
# 运行 cocotb 仿真
make ctb-<TOP_MODULE>

# 示例：运行 cosim_test 模块的仿真
make ctb-cosim_test
```

## 固件指令格式

固件指令定义在 `test_cosim_test.py` 中：

```python
firmware = [
    {"op": "add_one", "addr": 0, "len": 5}
]
```

## 验证模式

框架支持两种验证模式：
- **UT (Unit Test)**: 单元测试模式，实例化 Driver
- **ST (System Test)**: 系统测试模式，不实例化 Driver（被动模式）
