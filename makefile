# ============================== set verdi env========================= #
export LD_LIBRARY_PATH := ${LD_LIBRARY_PATH}:/app/synopsys/Verdi_O-2018.09-SP2/share/PLI/VCS/LINUX64
export NOVAS_HOME := /app/synopsys/Verdi_O-2018.09-SP2

PYTHON_DIR  := /home/public/eda_script/pyauto
SRC1        := NONE
SRC2        := NONE
DST         := NONE

SIM_DIR     := ${PWD}
RUN_DIR_DCT := ${PWD}/backend/syn/dct
RUN_DIR_FM  := ${PWD}/backend/formality

TOP := topfile
NAME_BP := topfile
DIR_BP  := ${PWD}/backend/syn/backup/${NAME_BP}

SOURCE = NONE
FSDB_NUM =
CORNER =
COV  = on
DUMP = on
SIMMODE = RTL
ST = 

# SIM_TOP ?= simfile_rtl
# SIM_TOOL ?= verilator
# EXTRA_ARGS += --coverage
# EXTRA_ARGS += --trace --trace-fst --trace-structs
# VERILOG_SOURCES += $(PWD)/my_design.sv $(PWD)/my_package.sv
# COCOTB_TOPLEVEL = my_design
# SIMMODE = RTL or PRESIM or POSTSIM

# ============================== initial VCS_option========================= #
VCS_OPT = -debug_pp -R -full64 +plusarg_save +v2k -sverilog +evalorder +no_notifier +vc -R

ifeq	($(DUMP),on)
VCS_OPT += +define+DUMP
VCS_OPT += +FSDB=fsdb/$(SIMMODE)$(FSDB_NUM).fsdb
VCS_OPT += +DUMP
endif

VCS_OPT += -P $(VERDI_HOME)/share/PLI/VCS/LINUX64/novas.tab \
$(VERDI_HOME)/share/PLI/VCS/LINUX64/pli.a

# ==========================VCS coverage collection option================= #
ifeq	($(COV),on)
VCS_OPT += -cm_name $(SIMMODE)
VCS_OPT += -cm_hier ./cfg/hier_file.conf
VCS_OPT += -cm line+cond+fsm
VCS_OPT += -cm_line contassign
VCS_OPT += -cm_cond allops+event+anywidth
VCS_OPT += -cm_ignorepragmas
VCS_OPT += -cm_noconst
endif

# ==========================select simfile================================ #
# ifeq	($(SIMMODE),PRESIM)
# SIMFILE = -f simfile/simfile_presim.f
# VCS_OPT += +define+PRESIM +notimingcheck
# LOG = log/sim/vcs_presim.log
# else
# ifeq	($(SIMMODE),POSTSIM)
# SIMFILE = -f simfile/simfile_postsim.f
# VCS_OPT += +define+POSTSIM +neg_tchk -negdelay +define+$(CORNER) +overlap
# LOG = log/sim/vcs_postsim.log
# else
# SIMFILE = -f simfile/$(SIM_TOP).f
# VCS_OPT += +notimingcheck
# LOG = log/sim/vcs_rtlsim.log
# endif
# endif

# ==========================Verilator lint option================================ #
VERILATOR_ARGS=-Wall -Wno-WIDTHEXPAND -Wno-WIDTHTRUNC -Wno-WIDTHXZEXPAND
VERILATOR_ARGS+=-Wno-EOFNEWLINE -Wno-DECLFILENAME -Wno-PINCONNECTEMPTY -Wno-GENUNNAMED -Wno-IMPORTSTAR -Wno-VARHIDDEN -Wno-UNUSEDPARAM -Wno-UNUSEDSIGNAL

# ==========================frontend script command============================== #

nlint-%:
	$(eval LINT_TOP := $*)
	@echo "======= nlint LINT_TOP = $(LINT_TOP) ======="
	nLint -95 -2001 -sv -rs ./nLint/my_nLint.rs -out ./log/nlint/nLint_$(LINT_TOP).log -f ./lintfile/$(LINT_TOP).list

vlint-%:
	$(eval LINT_TOP := $*)
	@echo "======= verilator LINT_TOP = $(LINT_TOP) ======="
	$(eval FILES=$(shell ./utils/expand_list.sh ./lintfile/$(LINT_TOP).list))
	verilator --lint-only --timing $(VERILATOR_ARGS) -sv $(FILES) --top-module $(LINT_TOP) 2>&1 | less

vcs-%:
	$(eval SIM_TOP := $*)
	@echo "========= vcs SIM_TOP = $(SIM_TOP) ======="
	$(eval SIMFILE := -f simfile/$(SIM_TOP).f)
	$(eval VCS_OPT += +notimingcheck)
	$(eval LOG := log/sim/vcs_$(SIM_TOP).log)
	vcs $(VCS_OPT) ./tsk/timescale.v $(SIMFILE) | tee $(LOG)

ctb-%:
	$(eval SIM_TOP := $*)
	@echo "======= cocotb SIM_TOP = $(SIM_TOP) ======="
	$(MAKE) -f testbench/cocotb/ctb.mk SIM_TOP=$(SIM_TOP) ST=$(ST)


uvm:
	vcs $(VCS_OPT) -ntb_opts uvm -timescale-1ns/1ps $(SIMFILE) | tee ./log/sim/uvm_report.log

cov:
	urg -dir simv.vdb

verdi-%:
	$(eval SIM_TOP := $*)
	@echo "======= SIM_TOP = $(SIM_TOP) ======="
	$(eval SIMFILE := -f simfile/$(SIM_TOP).f)
	verdi -sv -ssf ./fsdb/$(SIMMODE)$($FSDB_NUM).fsdb ./tsk/timescale.v $(SIMFILE) > ./log/sim/verdi.log
	@echo "(>.<)"

# ==========================backend script command============================== #

# Update sdc and netlist to inputs/ directory
update: ${RUN_DIR_DCT}
	make update TOP=${TOP} -C ${RUN_DIR_DCT}

backup: ${RUN_DIR_DCT}
	make backup DIR_BP=${DIR_BP} -C ${RUN_DIR_DCT}

# ==========================dc command============================== #
SCAN      			?= 0
SPG_PLACEMENT_DEF 	?=
SAIF_FILE 			?=

dc-%:
	$(eval DC_TOP := $*)
	@echo "========= dc DC_TOP = $(DC_TOP) ======="
	./utils/convert_to_absolute_path.sh ./backend/syn/dct/inputs/$(DC_TOP).f
	$(eval LIST := ./backend/syn/dct/inputs/$(DC_TOP)_temp.f)
	$(eval FUNC_SDC := ./backend/syn/dct/inputs/$(DC_TOP).func.sdc)
	$(eval CMD := -x "set FUNC_SDC $(FUNC_SDC); set TOP $(DC_TOP); set SCAN $(SCAN); set FILE_LIST $(LIST); set SAIF_FILE $(SAIF_FILE);")
	dc_shell-xg-t -no_gui $(CMD) -f ./backend/syn/dct/script/dc.tcl | tee ./backend/dc.log
	rm ./backend/syn/dct/inputs/$(DC_TOP)_temp.f

fm_dct: ${RUN_DIR_FM}
	make fm_dct TOP=${TOP} RUN_DIR_DCT=${RUN_DIR_DCT} -C ${RUN_DIR_FM}

fm_apr: ${RUN_DIR_FM}
	make fm_apr TOP=${TOP} -C ${RUN_DIR_FM}

dc_link:
	cp ./rtl/frontend_file.list ./backend/rel/rtl.lis
	cat `more ./backend/rel/rtl.lis` > ./backend/rel/$(TOP).v
	nLint -2001 -rs ./nLint/my_nLint.rs -out ./log/nlint/rel_nLint.log ./backend/rel/$(TOP).v

# ==========================auto script command============================== #

flstgen: ${PYTHON_DIR}
	python ${PYTHON_DIR}/autoeda.py flstgen ${SRC1} ${DST}

cpfile: ${PYTHON_DIR}
	python ${PYTHON_DIR}/autoeda.py cpfile ${SRC1} ${DST}

simfilegen: ${PYTHON_DIR}
	python ${PYTHON_DIR}/autoeda.py simfilegen ${SRC1} ${SRC2} ${DST}

tbgen: ${PYTHON_DIR}
	python ${PYTHON_DIR}/autoeda.py tbgen ${SRC1} ${DST}

spramtbgen: ${PYTHON_DIR}
	python ${PYTHON_DIR}/autoeda.py spramtbgen ${SRC1} ${DST}

dpramtbgen: ${PYTHON_DIR}
	python ${PYTHON_DIR}/autoeda.py dpramtbgen ${SRC1} ${DST}

ramgen: ${PYTHON_DIR}
	python ${PYTHON_DIR}/autoeda.py ramgen ${SRC1} ${DST}

link: ${PYTHON_DIR}
	python ${PYTHON_DIR}/autoeda.py link ${SRC1} ${DST}

# ==========================system command============================== #

.PHONY: new
new: __docs __mkdirs __touchs __gitkeeps
	@echo '`timescale 1ns/1ps' > ./tsk/timescale.v
	cp ./docs/dc.makefile ${RUN_DIR_DCT}/makefile
	cp ./docs/fm.makefile ${RUN_DIR_FM}/makefile
	cp ./docs/*.rs nLint/
	cp ./docs/dc*.tcl ${RUN_DIR_DCT}/script
	cp ./docs/sc*.tcl ${RUN_DIR_DCT}/script
	cp ./docs/path*.tcl ${RUN_DIR_DCT}/script
	cp ./docs/fm*.tcl ${RUN_DIR_FM}/script
	cp ./docs/*.sdc backend/sdc/
	cp ./docs/synopsys_sim.setup .

.PHONY: __docs
__docs:
	@echo "hello,designer"
	-mkdir docs && mv *.* docs/

.PHONY: __mkdirs
__mkdirs:
	mkdir -p testbench
	mkdir -p rtl
	mkdir -p log/nlint/rtl
	mkdir -p log/sim
	mkdir -p fsdb
	mkdir -p tsk
	mkdir -p simfile
	mkdir -p nLint
	mkdir -p backend/rel
	mkdir -p backend/sdc
	mkdir -p backend/formality/script
	mkdir -p backend/syn/backup
	mkdir -p backend/syn/dct/inputs
	mkdir -p backend/syn/dct/script

.PHONY: __touchs
__touchs: __mkdirs
	touch ./simfile/simfile_rtl.f
	touch ./simfile/simfile_presim.f
	touch ./simfile/simfile_postsim.f
	touch ./backend/rel/rtl.lis
	touch ./backend/syn/dct/inputs/backend_file.list
	touch ./rtl/frontend_file.list
	touch ./tsk/timescale.v

.PHONY: __touchs
__gitkeeps: __mkdirs
	touch testbench/.gitkeep
#	touch rtl/.gitkeep
	touch log/nlint/rtl/.gitkeep
	touch log/sim/.gitkeep
	touch fsdb/.gitkeep
#	touch tsk/.gitkeep
#	touch simfile/.gitkeep
#	touch nLint/.gitkeep
#	touch backend/rel/.gitkeep
#	touch backend/sdc/.gitkeep
	touch backend/formality/script/.gitkeep
	touch backend/syn/backup/.gitkeep
#	touch backend/syn/dct/inputs/.gitkeep
#	touch backend/syn/dct/script/.gitkeep


.PHONY: clean_dct
clean_dct: ${RUN_DIR_DCT}
	make clean TOP=${TOP} -C ${RUN_DIR_DCT}

.PHONY: clean_fm
clean_fm: ${RUN_DIR_FM}
	make clean TOP=${TOP} -C ${RUN_DIR_FM}

.PHONY: clean_sim
clean_sim:
	-rm -f ./*.log
	-rm -f ./*.rc
	-rm -f ./*.conf
	-rm -f ./smiv*
	-rm -f ./*.key
	-rm -f ./log/sim/*.log
	-rm -f ./fsdb/*.fsdb
	-rm -rf ./csrc
	-rm -rf ./simv*
	-rm -f *.dat
	-rm -f *.fst
	-rm -f *.vcd

.PHONY: clean_dc
clean_dc:
	-rm -f ./*.pvl
	-rm -f ./*.syn
	-rm -f ./*.mr
	-rm -f ./*.html
	-rm -f ./*.csh
	-rm -f ./*.pvk
	-rm -rf ./.DC_log*
	-rm -rf alib-52
	
.PHONY: clean_nlint
clean_nlint:
	-rm -rf ./nLintDB
	-rm -rf ./nLintLog

.PHONY: clean_all
clean_all: clean_dc clean_nlint clean_sim

clean_build-%:
	$(eval BUILD := $*)
	@echo "======= clean BUILD = $(BUILD) ======="
	-rm -rf ./builds/sim_build_$(BUILD)
	-rm -rf ./builds/results_$(BUILD).xml

.PHONY: clearprj
clearprj:
	mkdir ../makefile_save
	mv ./makefile ../makefile_save/
	mv ./docs/* ../makefile_save/
	-rm -rf ./*
	mv ../makefile_save/* ./
	-rm -rf ../makefile_save
	@echo "good bye,designer"

# ==========================help============================== #
help:
	@echo "================ makefile help ================"
	@echo "make new       : create a new workspace"
	@echo -e "\n"
	@echo "================ frontend script command ================"
	@echo "make nlint     : start nlint to check the code in simfile"
	@echo "make vcs       : start simulation"
	@echo "make cov       : create the report of cover"
	@echo "make verdi     : start verdi to observe the wave"
	@echo -e "\n"
	@echo "================ backend script command ================"
	@echo "make dc_link   : link the rtl in a file for dc synthesis"
	@echo "make update    : update rtl and sdc file"
	@echo "make backup    : backup rtl and sdc file"
	@echo "make dc        : run dc synthesis scripts"
	@echo "make fm_dct    : run dc netlist formality scripts"
	@echo "make fm_apr    : run apr netlist formality scripts"
	@echo -e "\n"
	@echo "================ clean command ================"
	@echo "make clean_dct : clean synthesis redundant files"
	@echo "make clean_sim : clean the simulation temp file"
	@echo "make clearprj  : remove all files except makefile"
	@echo -e "\n"
	@echo "================ autoeda command ================"
	@echo "make flstgen   : generate file list under the specified path"
	@echo "make cpfile    : copy file from filelist/folder to destination folder"
	@echo "make tbgen     : generate testbench"
	@echo "make spramtbgen: generate testbench for auto generating single port ram model"
	@echo "make dpramtbgen: generate testbench for auto generating double port ram model"
	@echo "make ramgen    : generate ram model"
	@echo "make link      : generate module top file "
	@echo "make simfilegen: generate simfile filelist according to rtl and testbench"
