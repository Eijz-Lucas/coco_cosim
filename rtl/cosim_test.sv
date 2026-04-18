module cosim_test #(
    parameter ADDR_WIDTH = 8,
    parameter DATA_WIDTH = 8
) (
    input  logic       clk,
    rst_n
);
    // add_one
    // logic       en_add;
    // logic [7:0] addr_add;
    // logic [7:0] len_add;
    // logic [7:0] ram_addr_add;
    // logic [7:0] ram_rdata_add;
    // logic       fifo_write_en_add;
    // logic [7:0] fifo_write_data_add;
    // // sub_one
    // logic       en_sub;
    // logic [7:0] len_sub;
    // logic       fifo_read_en_sub;
    // logic [7:0] fifo_read_data_sub;
    // logic       fifo_write_en_sub;
    // logic [7:0] fifo_write_data_sub;

    add_one u_add_one (
        .clk            (clk),
        .rst_n          (rst_n),
        .en             (),
        .addr           (),
        .len            (),
        .ram_addr       (),
        .ram_rdata      (),
        .fifo_write_en  (),
        .fifo_write_data()
    );

    sub_one u_sub_one (
        .clk            (clk),
        .rst_n          (rst_n),
        .en             (),
        .len            (),
        .fifo_read_en   (),
        .fifo_read_data (),
        .fifo_write_en  (),
        .fifo_write_data()
    );


endmodule
