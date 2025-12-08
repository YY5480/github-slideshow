
`timescale 1ns / 1ps

module tb_cdc_synchronizer;

// Parameters for the clock periods
parameter FAST_CLK_PERIOD = 10;  // 100 MHz
parameter SLOW_CLK_PERIOD = 30;  // 33.3 MHz

// Testbench Signals
reg clk_fast;
reg rst_fast;
reg data_in_fast;

reg clk_slow;
reg rst_slow;
wire data_out_slow;

// Instantiate the DUT (Device Under Test)
cdc_synchronizer uut (
    .clk_fast(clk_fast),
    .rst_fast(rst_fast),
    .data_in_fast(data_in_fast),

    .clk_slow(clk_slow),
    .rst_slow(rst_slow),
    .data_out_slow(data_out_slow)
);

// Fast Clock Generation
always #(FAST_CLK_PERIOD/2) clk_fast = ~clk_fast;

// Slow Clock Generation
always #(SLOW_CLK_PERIOD/2) clk_slow = ~clk_slow;

// Test Sequence
initial begin
    // Initial values
    clk_fast = 0;
    rst_fast = 1;
    data_in_fast = 0;

    clk_slow = 0;
    rst_slow = 1;

    // Apply reset
    #50;
    rst_fast = 0;
    rst_slow = 0;

    // Send a pulse on the fast domain
    #100;
    data_in_fast = 1;
    #(2 * FAST_CLK_PERIOD); // Hold for two fast clock cycles
    data_in_fast = 0;

    // Let the synchronizer work
    #200;

    // Send another pulse
    data_in_fast = 1;
    #(5 * FAST_CLK_PERIOD); // Hold for five fast clock cycles
    data_in_fast = 0;

    // Let the simulation run for a bit longer
    #300;

    // Stop the simulation
    $finish;
end

// Display Results
initial begin
    $monitor("Time = %0t | clk_f=%b, data_in=%b | clk_s=%b, data_out=%b",
             $time, clk_fast, data_in_fast, clk_slow, data_out_slow);
end

endmodule
