module cosim_test #(
    parameter ADDR_WIDTH = 8,
    parameter DATA_WIDTH = 8
) (
    input  logic       clk,
    rst_n,
    // add_one
    input logic en_add,
    input logic [7:0] addr_add,
    input logic [7:0] len_add,
    output logic [7:0] ram_addr_add,
    input logic [7:0] ram_rdata_add,
    output logic fifo_write_en_add,
    output logic [7:0] fifo_write_data_add,
    // sub_one
    input logic en_sub,
    input logic [7:0] len_sub,
    output logic fifo_read_en_sub,
    input logic [7:0] fifo_read_data_sub,
    output logic fifo_write_en_sub,
    output logic [7:0] fifo_write_data_sub
);

    add_one u_add_one (
        .clk            (clk),
        .rst_n          (rst_n),
        .en             (en_add),
        .addr           (addr_add),
        .len            (len_add),
        .ram_addr       (ram_addr_add),
        .ram_rdata      (ram_rdata_add),
        .fifo_write_en  (fifo_write_en_add),
        .fifo_write_data(fifo_write_data_add)
    );

    sub_one u_sub_one (
        .clk            (clk),
        .rst_n          (rst_n),
        .en             (en_sub),
        .len            (len_sub),
        .fifo_read_en   (fifo_read_en_sub),
        .fifo_read_data (fifo_read_data_sub),
        .fifo_write_en  (fifo_write_en_sub),
        .fifo_write_data(fifo_write_data_sub)
    );


endmodule
