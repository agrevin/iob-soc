`timescale 1 ns / 1 ps

`include "bsp.vh"
`include "iob_soc_conf.vh"
`include "iob_utils.vh"

//Peripherals _swreg_def.vh file includes.
`include "iob_soc_periphs_swreg_def.vs"

module iob_soc_mwrap #(

`ifdef IOB_SOC_INIT_MEM
    parameter HEXFILE  = "iob_soc_firmware",
`else
    parameter HEXFILE  = "none",
`endif
    parameter BOOT_HEXFILE = "iob_soc_boot",
    parameter MEM_NO_READ_ON_WRITE = 1,        //no simultaneous read/write
   `include "iob_soc_params.vs"
) (
   `include "iob_soc_io.vs"
);


//rom wires
wire rom_r_valid_i;
wire [BOOTROM_ADDR_W-3:0] rom_r_addr_i;
wire [DATA_W-1:0] rom_r_rdata_o;


//ram wires
wire                               i_valid_i;
wire          [SRAM_ADDR_W-3:0]    i_addr_i;
wire          [     DATA_W-1:0]    i_wdata_i;
wire          [   DATA_W/8-1:0]    i_wstrb_i;
wire          [     DATA_W-1:0]    i_rdata_o;
wire                               d_valid_i;
wire          [SRAM_ADDR_W-3:0]    d_addr_i;
wire          [     DATA_W-1:0]    d_wdata_i;
wire          [   DATA_W/8-1:0]    d_wstrb_i;
wire          [     DATA_W-1:0]    d_rdata_o;
//

`ifdef USE_SPRAM
    wire                       en_i;
    wire     [SRAM_ADDR_W-3:0] addr_i;
    wire     [DATA_W/8-1:0]    we_i;
    wire     [DATA_W-1:0]      d_i;
    wire     [DATA_W-1:0]      d_o;
`endif

iob_soc #(
    .BOOTROM_ADDR_W(           BOOTROM_ADDR_W),
    .SRAM_ADDR_W(                 SRAM_ADDR_W),
    .MEM_ADDR_W(                   MEM_ADDR_W),
    .ADDR_W(                           ADDR_W),
    .DATA_W(                           DATA_W),
    .AXI_ID_W(                       AXI_ID_W),
    .AXI_ADDR_W(                   AXI_ADDR_W),
    .AXI_DATA_W(                   AXI_DATA_W),
    .AXI_LEN_W(                     AXI_LEN_W),
    .MEM_ADDR_OFFSET(         MEM_ADDR_OFFSET),
    .UART0_DATA_W(               UART0_DATA_W),
    .UART0_ADDR_W(               UART0_ADDR_W),
    .UART0_UART_DATA_W(     UART0_UART_DATA_W),
    .TIMER0_DATA_W(             TIMER0_DATA_W),
    .TIMER0_ADDR_W(             TIMER0_ADDR_W),
    .TIMER0_WDATA_W(           TIMER0_WDATA_W)
)iob_soc(
    .clk_i(                             clk_i),
    .cke_i(                             cke_i),
    .arst_i(                           arst_i),
    .trap_o(                           trap_o),
    `ifdef IOB_SOC_USE_EXTMEM
    .axi_awid_o(                   axi_awid_o),
    .axi_awaddr_o(               axi_awaddr_o),
    .axi_awlen_o(                 axi_awlen_o),
    .axi_awsize_o(               axi_awsize_o),
    .axi_awburst_o(             axi_awburst_o),
    .axi_awlock_o(               axi_awlock_o),
    .axi_awcache_o(             axi_awcache_o),
    .axi_awprot_o(               axi_awprot_o),
    .axi_awqos_o(                 axi_awqos_o),
    .axi_awvalid_o(             axi_awvalid_o),
    .axi_awready_i(             axi_awready_i),
    .axi_wdata_o(                 axi_wdata_o),
    .axi_wstrb_o(                 axi_wstrb_o),
    .axi_wlast_o(                 axi_wlast_o),
    .axi_wvalid_o(               axi_wvalid_o),
    .axi_wready_i(               axi_wready_i),
    .axi_bid_i(                     axi_bid_i),
    .axi_bresp_i(                 axi_bresp_i),
    .axi_bvalid_i(               axi_bvalid_i),
    .axi_bready_o(               axi_bready_o),
    .axi_arid_o(                   axi_arid_o),
    .axi_araddr_o(               axi_araddr_o),
    .axi_arlen_o(                 axi_arlen_o),
    .axi_arsize_o(               axi_arsize_o),
    .axi_arburst_o(             axi_arburst_o),
    .axi_arlock_o(               axi_arlock_o),
    .axi_arcache_o(             axi_arcache_o),
    .axi_arprot_o(               axi_arprot_o),
    .axi_arqos_o(                 axi_arqos_o),
    .axi_arvalid_o(             axi_arvalid_o),
    .axi_arready_i(             axi_arready_i),
    .axi_rid_i(                     axi_rid_i),
    .axi_rdata_i(                 axi_rdata_i),
    .axi_rresp_i(                 axi_rresp_i),
    .axi_rlast_i(                 axi_rlast_i),
    .axi_rvalid_i(               axi_rvalid_i),
    .axi_rready_o(               axi_rready_o),
    `endif
    .uart_txd_o(                   uart_txd_o),
    .uart_rxd_i(                   uart_rxd_i),
    .uart_cts_i(                   uart_cts_i),
    .uart_rts_o(                   uart_rts_o),
        //SPRAM  
`ifdef USE_SPRAM
    .valid_SPRAM_i(en_i),
    .addr_SPRAM_i(addr_i),
    .wstrb_SPRAM_i(we_i),
    .wdata_SPRAM_i(d_i),
    .rdata_SPRAM_o(d_o),
`endif

    //rom
    .rom_r_valid_i(rom_r_valid_i),
    .rom_r_addr_i(rom_r_addr_i),
    .rom_r_rdata_o(rom_r_rdata_o),
    //

    //ram
    .i_valid_i(i_valid_i),
    .i_addr_i(i_addr_i),
    .i_wdata_i(i_wdata_i),
    .i_wstrb_i(i_wstrb_i),
    .i_rdata_o(i_rdata_o),
    .d_valid_i(d_valid_i),
    .d_addr_i(d_addr_i),
    .d_wdata_i(d_wdata_i),
    .d_wstrb_i(d_wstrb_i),
    .d_rdata_o(d_rdata_o)
   //

);


    `ifdef USE_SPRAM
        iob_ram_sp_be #(
            .HEXFILE(HEXFILE),
            .ADDR_W (SRAM_ADDR_W - 2),
            .DATA_W (DATA_W)
        ) main_mem_byte (
            .clk_i(clk_i),
            // data port
            .en_i  (valid),
            .addr_i(addr),
            .we_i  (wstrb),
            .d_i   (wdata),
            .dt_o  (rdata)
        );
    `else
        `ifdef IOB_MEM_NO_READ_ON_WRITE
            iob_ram_dp_be #(
            .HEXFILE             (HEXFILE),
            .ADDR_W              (SRAM_ADDR_W - 2),
            .DATA_W              (DATA_W),
            .MEM_NO_READ_ON_WRITE(1)
            ) main_mem_byte (
            .clk_i(clk_i),
            // data port
            .enA_i  (d_valid_i),
            .addrA_i(d_addr_i),
            .weA_i  (d_wstrb_i),
            .dA_i   (d_wdata_i),
            .dA_o   (d_rdata_o),

            // instruction port
            .enB_i  (i_valid_i),
            .addrB_i(i_addr_i),
            .weB_i  (i_wstrb_i),
            .dB_i   (i_wdata_i),
            .dB_o   (i_rdata_o)
        );
        `else  // !`ifdef IOB_MEM_NO_READ_ON_WRITE
            iob_ram_dp_be_xil #(
                .HEXFILE(HEXFILE),
                .ADDR_W (SRAM_ADDR_W - 2),
                .DATA_W (DATA_W)
            ) main_mem_byte (
                .clk_i(clk_i),

                // data port
                .enA_i  (d_valid_i),
                .addrA_i(d_addr_i),
                .weA_i  (d_wstrb_i),
                .dA_i   (d_wdata_i),
                .dA_o   (d_rdata_o),
                // instruction port
                .enB_i  (i_valid_i),
                .addrB_i(i_addr_i),
                .weB_i  (i_wstrb_i),
                .dB_i   (i_wdata_i),
                .dB_o   (i_rdata_o)
            );
        `endif
    `endif 


    //rom instatiation
    iob_rom_sp #(
        .DATA_W (DATA_W),
        .ADDR_W (BOOTROM_ADDR_W - 2),
        .HEXFILE({BOOT_HEXFILE, ".hex"})
    ) sp_rom0 (
        .clk_i   (clk_i),
        .r_en_i  (rom_r_valid_i),
        .addr_i  (rom_r_addr_i),
        .r_data_o(rom_r_rdata_o)
    );
endmodule