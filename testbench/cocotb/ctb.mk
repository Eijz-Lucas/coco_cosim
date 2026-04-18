# This file is public domain, it can be freely copied without restrictions.
# SPDX-License-Identifier: CC0-1.0

# Makefile

# default
SIM ?= verilator
TOPLEVEL_LANG ?= verilog
SIM_TOP ?= top
SIM_TOP_MAKEFILE ?= testbench/cocotb/$(SIM_TOP)/makefile

VERILOG_SOURCES += $(shell ./utils/expand_list.sh ./simfile/$(SIM_TOP).f)
# use VHDL_SOURCES for VHDL files

# default args
EXTRA_ARGS += --trace --trace-fst --trace-structs
ifeq ($(ST),1)
EXTRA_ARGS += +define+ST
endif

# COCOTB_TOPLEVEL is the name of the toplevel module in your Verilog or VHDL file
COCOTB_TOPLEVEL = $(SIM_TOP)

# COCOTB_TEST_MODULES is the basename of the Python test file(s)
COCOTB_TEST_MODULES = testbench.cocotb.$(SIM_TOP).test_$(SIM_TOP)
COCOTB_RESULTS_FILE = builds/results_$(SIM_TOP).xml
SIM_BUILD = builds/sim_build_$(SIM_TOP)

# ----------------------------------------------------------
# Include per-top Makefile (if exists) to override/extend vars
# IMPORTANT: must be included BEFORE cocotb Makefile.sim
# ----------------------------------------------------------
ifneq ("$(wildcard $(SIM_TOP_MAKEFILE))","")
  $(info [INFO] Including per-top makefile: $(SIM_TOP_MAKEFILE))
  include $(SIM_TOP_MAKEFILE)
else
  $(info [INFO] No per-top makefile found: $(SIM_TOP_MAKEFILE))
endif

# include cocotb's make rules to take care of the simulator setup
include $(shell cocotb-config --makefiles)/Makefile.sim