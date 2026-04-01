###############################################################################
#clear and reset
###############################################################################
set date_start [sh date]
remove_design -all
set RESULTS_DIR ./backend/syn/outputs
set REPORTS_DIR ./backend/syn/reports
sh rm -rf ${RESULTS_DIR}
sh mkdir ${RESULTS_DIR}
sh rm -rf ${REPORTS_DIR}
sh mkdir ${REPORTS_DIR}


###############################################################################
# set multi core 1~16
###############################################################################
set_host_options -max_cores 16

###############################################################################
#    Set rules
###############################################################################
#set_app_var hdlin_vrlg_std 2005
#set_app_var hdlin_sverilog_std 2012
set_app_var template_naming_style %s
set_app_var uniquify_naming_style %s_%d


set enable_page_mode false

set enable_recovery_removal_arcs true
set power_perserve_rtl_hier_names true
set compile_preserve_subdesign_interfaces true
set bus_naming_style {%s[%d]}
set hdlin_enable_rtldrc_info true

set_app_var compile_disable_hierarchical_inverter_opt true
set_app_var verilogout_no_tri true
set_app_var compile_register_replication false

set_app_var timing_enable_multiple_clocks_per_reg  true
set_app_var timing_separate_clock_gating_group true
set_app_var power_opto_extra_high_dynamic_power_effort true
set_app_var compile_slack_driven_buffering true

set_app_var compile_state_reachability_high_effort_merge true

#set_app_var compile_seqmap_propagate_constants false
#set_app_var compile_seqmap_propagate_high_effort false
set_app_var html_log_enable true
set_app_var html_log_filename ${TOP}.html

set compile_timing_high_effort true
set_app_var compile_timing_high_effort_tns true


###############################################################################
#    source logic and physical libraries
###############################################################################

source -e -v backend/syn/dct/script/lib.tcl

###############################################################################
check_library > ${REPORTS_DIR}/check_library.rpt


###############################################################################
#    Set synopsys verification for formality
###############################################################################
set_svf  $RESULTS_DIR/$TOP.svf

###############################################################################
#    Read Verilog file
###############################################################################
#generate the HTML log file in dc_shell, before reading in the design


set RTL_FILE [subst [sh cat ${FILE_LIST}]]
analyze -format sverilog   ${RTL_FILE}

elaborate      ${TOP}
current_design ${TOP}
link
###############################################################################
# Set timing debrate
###############################################################################
#set_timing_derate -max -early 0.92
#set_timing_derate -max -late  1.08
set_structure true -boolean true -timing true
set_fix_multiple_port_nets -all -buffer_constants  [get_designs *]
set_cost_priority -delay
set_critical_range 0.3 [current_design]
set_dynamic_optimization true
set_leakage_optimization true

###############################################################################
# Set operating conditions
###############################################################################
#set_operating_conditions -max $MAX_COND\
                         -max_library $MAX_LIB\
                         -min $MIN_COND\
                         -min_library $MIN_LIB

###############################################################################
#    Unify
###############################################################################
uniquify -force
#set_max_dynamic_power 0
#set_max_leakage_power 0

###############################################################################
#    Instance SDC files
###############################################################################
source -e -v $FUNC_SDC
#source -e -v ./inputs/io_port.sdc
set_ideal_network [all_high_fanout -nets  -threshold 100] -no_propagate
#source -e -v dc_syn/dc_scr/set_dont_use.tcl
#
###############################################################################
#use verilog naming rules
###############################################################################
change_names -rules verilog -hierarchy

###############################################################################
#Define the working directory
###############################################################################
define_design_lib worklib -path ~/

#################################################################################
# Create Default Path Groups
#
# Separating these paths can help improve optimization.
# Remove these path group settings if user path groups have already been defined.
#################################################################################
set ports_clock_root [filter_collection [get_attribute [get_clocks] sources] object_class==port]
group_path -name in2out  -weight 0  -from [remove_from_collection [all_inputs] $ports_clock_root] -to [all_outputs]
group_path -name reg2out -weight 0  -from [all_registers -clock_pins] -to [all_outputs]
group_path -name in2reg  -weight 0  -from [remove_from_collection [all_inputs] $ports_clock_root] -to [all_registers -data_pins]
group_path -name reg2reg -weight 10  -from [all_registers -clock_pins] -to [all_registers -data_pins]


###############################################################################
if {[info exists SAIF_FILE]} {
#read_saif -input /home/zxt/backend/qua_lyh/syn/inputs/quantization_tst_11-12.fsdb.saif -instance quantization_tst/quantization_sim_top/quantization
#report_saif -hier -rtl_saif
}
#For  dynamic power optimization, use the
#       set_dynamic_optimization  true  in   non-MCMM   designs   or   set_sce-
#       nario_options  -dynamic  true  in  MCMM designs. In both cases, you can
#       also use set power_low_power_placement true to enable low power  place-
#       ment.
###############################################################################
#    Check design
###############################################################################
check_design -summary
check_design > $REPORTS_DIR/chkdesign_$TOP.rpt

# The analyze_datapath_extraction command can help you to analyze why certain data
# paths are no extracted, uncomment the following line to report analyisis.

# analyze_datapath_extraction > ${REPORTS_DIR}/${DCRM_ANALYZE_DATAPATH_EXTRACTION_REPORT}

check_timing > $REPORTS_DIR/chktiming_$TOP.rpt

# set_dont_touch [get_cell * -hier -filter  "ref_name =~ PANA2*"]
# set_dont_touch [get_cell * -hier -filter  "ref_name =~ PIS*"]
# set_dont_touch [get_cell * -hier -filter  "ref_name =~ PBSD12*"]
# set_dont_touch [get_cell * -hier -filter  "ref_name =~ PB8"]

###############################################################################
#    Optimization Option
###############################################################################
set_timing_derate -data -late 1.05
#set_timing_derate -data -late 1.03 [get_cell -f "ref_name=~*sram*" -h]

###############################################################################
# Set for multi-threshold library
###############################################################################
# set_attribute [get_libs $rvt_stb_lib] default_threshold_voltage_group rvt
# set_attribute [get_libs $lvt_stb_lib] default_threshold_voltage_group lvt
# set_attribute [get_libs $ulvt_stb_lib] default_threshold_voltage_group ulvt
#set_multi_vth_constraint -lvth_groups { ulvt } -lvth_percentage 20
###############################################################################
# Set Clock gating style
###############################################################################
#set_clock_gating_style -sequential_cell latch -positive_edge_logic  {integrated} \
#                       -control_point before -control_signal test_mode
set_clock_gating_style -sequential_cell latch -minimum_bitwidth 16 \
    -control_signal test_mode -max_fanout 64 -positive_edge_logic {integrated:CLKLANQV4_8TUL40} -control_point before -negative_edge_logic {integrated:CLKLAHQV4_8TUL40}
###############################################################################
set_register_merging [current_design] true
#set_multibit_options  -mode timing_driven 
#set_app_var hdlin_infer_multibit default_all
###############################################################################
#compile_ultra -check_only
compile_ultra -gate_clock -no_boundary_optimization -no_seq_output_inversion -no_autoungroup 
optimize_netlist -area -no_boundary_optimization 


report_timing -delay max -sort_by slack -path full -group reg2reg  -nworst 1 -max_paths 100 >  $REPORTS_DIR/timing_1stcmp_$TOP.rpt

if {$synopsys_program_name == "dc_shell"}  {}
###############################################################################
#write the result
###############################################################################

#Write out verilog
change_names -rules verilog -verbose -hierarchy
write -f ddc -hierarchy     -output $RESULTS_DIR/${TOP}_mapped.ddc
write -f verilog -hierarchy -output $RESULTS_DIR/${TOP}.v
# Write parasitics data from Design Compiler Topographical placement for static timing analysis

# Write SDF backannotation data from Design Compiler Topographical placement for static timing analysis
write_sdf ${RESULTS_DIR}/${TOP}_mapped.sdf



write_sdc  -nosplit                 $RESULTS_DIR/${TOP}_mapped.func.sdc
# If SAIF is used, write out SAIF name mapping file for PrimeTime-PX
if {[info exists SAIF_FILE]} {
saif_map -type ptpx -write_map ${RESULTS_DIR}/${TOP}_mapped.SAIF.namemap
}
write_script -output                $RESULTS_DIR/${TOP}_mapped.tcl

###############################################################################
#Report analysis results
report_qor                        >  $REPORTS_DIR/${TOP}_qor.rpt
#create_qor_snapshot -name qor_snapshot_$TOP.rpt > ${REPORTS_DIR}/qor_snapshot_$TOP.rpt
# Create a QoR snapshot of timing, physical, constraints, clock, power data, and routing on
# active scenarios and stores it in the location  specified  by  the icc_snapshot_storage_location
# variable.
#report_constraint -all_violators  > $REPORTS_DIR/all_vios_$TOP.rpt
#report_timing -transition_time -nets -attributes -nosplit > ${REPORTS_DIR}/timing_$TOP.rpt
#report_timing -sort_by slack -path full -nworst 1 -max_paths 1000  -loops                         >> $REPORTS_DIR/timing_loops_$TOP.rpt
report_resource -hierarchy                                         > $RESULTS_DIR/$TOP.res
report_area -hier                                                  > $REPORTS_DIR/area_hier_$TOP.rpt
report_area -physical -nosplit                                     > $REPORTS_DIR/area_$TOP.rpt

report_clock                                                        > $REPORTS_DIR/clocks_$TOP.rpt
report_clock_gating -style                                          > $REPORTS_DIR/clocks_gating_style_$TOP.rpt
report_clock_gating -nosplit                                        > $REPORTS_DIR/clocks_gating_$TOP.rpt
report_threshold_voltage_group -nosplit -lvth_groups {lvt} -verbose  > $REPORTS_DIR/mvt_percent_$TOP.rpt
report_constraints -all_violators -max_delay -nosplit >  $REPORTS_DIR/$TOP.timing_sumary.rpt
# Use SAIF file for power analysis
report_power -hier -nosplit -hier_level 2 -verbose -analysis_effort medium > $REPORTS_DIR/power_$TOP.rpt
set_svf -off

set date_end [sh date]
echo "DC start from $date_start to $date_end"
exit
