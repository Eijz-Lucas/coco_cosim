set ulvt_stb_lib  "scc40nll_hdc40_ulvt_ttg_v1p1_25c_ccs"
set lvt_stb_lib   "scc40nll_hdc40_lvt_ttg_v1p1_25c_ccs"
set rvt_stb_lib   "scc40nll_hdc40_rvt_ttg_v1p1_25c_ccs"
set rvt_mb_stb_lib   "scc40nll_hdc40c50_mbff_tt_v1p1_25c_ccs"
set PROC_PATH    [concat /mnt/public/digital_lib/SMIC40LL/SCC40NLL_HDC40/SCC40NLL_HDC40_RVT_V0p2/liberty/1.1v \
                         /mnt/public/digital_lib/SMIC40LL/SCC40NLL_HDC40/SCC40NLL_HDC40_LVT_V0p2/liberty/1.1v \
                         /mnt/public/digital_lib/SMIC40LL/SCC40NLL_HDC40/SCC40NLL_HDC40_ULVT_V0p2/liberty/1.1v \
                         /mnt/public/digital_lib/SMIC40LL/SCC40NLL_HDC40C50/SCC40NLL_HDC40C50_MBFF_V0.1/SCC40NLL_HDC40C50_MBFF_V0p1/liberty/1.1v \
]
set SYNOPSYS_ROOT [concat /app/synopsys/syn_vO-2018.06-SP1/libraries/syn]
set SYMBOL_LIBRARY_PATH [concat /mnt/public/digital_lib/SMIC40LL/SCC40NLL_HDC40/SCC40NLL_HDC40_RVT_V0.1/SCC40NLL_HDC40_RVT_V0p1/symbol]
set IO_PATH [concat /mnt/public/digital_lib/SMIC40LL/IO/SPC40NLLD2RNP_OV3_V1p1c/syn/1p8v \
	            /mnt/public/digital_lib/SMIC40LL/SMIC40LL/IO/SP40NLLD2RNP_OV3_V1p1a/syn/1p8v]
set MEM_PATH [concat /home/zxt/backend/IC_Debugger/lib/db /home/zxt/backend/IC_Debugger/IC_Debugger/analog/lib]
set PARA_PATH [concat /home/zxt/backend/IC_Debugger/IC_Debugger/rtl]
set_app_var search_path   [concat $PROC_PATH \
                          ${SYNOPSYS_ROOT}/sdb \
                          $SYMBOL_LIBRARY_PATH \
                          $PARA_PATH \
                          $IO_PATH \
			              $MEM_PATH]
#############################################################################################################################################################
#set_app_var target_library [concat ${rvt_stb_lib}.db ${lvt_stb_lib}.db ${hvt_stb_lib}.db ${ulvt_stb_lib}.db]
set_app_var target_library [concat ${rvt_stb_lib}.db ${lvt_stb_lib}.db ${ulvt_stb_lib}.db ${rvt_mb_stb_lib}.db]
set_app_var synthetic_library "dw_foundation.sldb"
set_app_var symbol_library "scc28nhkcp_hdc35p140_ulvt.sdb"

set std_libs [join "
scc40nll_hdc40_ulvt_ttg_v1p1_25c_ccs.db
scc40nll_hdc40_lvt_ttg_v1p1_25c_ccs.db
scc40nll_hdc40_rvt_ttg_v1p1_25c_ccs.db
"]
set io_libs  [join "
SPC40NLLD2RNP_OV3_V1p1_ss_V0p99_-40C.db
SP40NLLD2RNP_OV3_V1p1_ss_V0p99_-40C.db
"]

set mem_libs [join "
ic_debugger_sram_ss0p99vn40c.db
picosoc_sram.db
analog_ip_lyt.db
analog_ip_por.db
analog_ip_wy.db
analog_ip_wzq.db
analog_ip_ysq_2.db
analog_ip_ysq.db
analog_ip_zyh.db
" ]

set MIN_LIBRARY_FILES             "$std_libs $io_libs $mem_libs"  ;#  List of max min library pairs "max1 min1 max2 min2 max3 min3"...

set_app_var link_library  [concat "*" $target_library $synthetic_library $MIN_LIBRARY_FILES]


#foreach {max_library min_library} $MIN_LIBRARY_FILES {
#set_min_library $max_library -min_version $min_library
#}

#remove_attribute [get_cell scc40nll_vhsc40_hvt_ss_v0p99_-40c_ccs/*] dont_use
#remove_attribute [get_cell scc40nll_vhsc40_hvt_ss_v0p99_-40c_ccs/*] dont_touch

set_dont_use [get_lib_cell */*8TUL40]
set_dont_use [get_lib_cell */*CLK*]
set_dont_use [get_lib_cell */*DEL*]
set_dont_use [get_lib_cell */*TBUF*]
#set_dont_use [get_lib_cell */*TINV*]
set_dont_use [get_lib_cell */ED*]
set_dont_use [get_lib_cell */SD*]
set_dont_use [get_lib_cell */SED*]
set_dont_use [get_lib_cell */*PULL*]
set_dont_use [get_lib_cell */*V0_*]
set_dont_use [get_lib_cell */*V0P5_*]
set_dont_use [get_lib_cell */*OR*V12*_*]
set_dont_use [get_lib_cell */*AN*V12*_*]
set_dont_use [get_lib_cell */*OR*V16*_*]
set_dont_use [get_lib_cell */*AN*V16*_*]
#set_dont_use [get_lib_cell */*AO*V12*_*]
#set_dont_use [get_lib_cell */*OA*V12*_*]
#set_dont_use [get_lib_cell */*V16*_*]
set_dont_use [get_lib_cell */*V20*_*]
set_dont_use [get_lib_cell */*V24*_*]
set_dont_use [get_lib_cell */*V32*_*]
set_dont_use [get_lib_cell */*V40*_*]
set_dont_use [get_lib_cell */*V48*_*]
set_dont_use [get_lib_cell */*V64*_*]
set_dont_use [get_lib_cell */*LAL*]
set_dont_use [get_lib_cell */*LAH*]

