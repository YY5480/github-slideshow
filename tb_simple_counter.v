
`timescale 1ns / 1ps

module tb_simple_counter;

// Parameters
parameter CLK_PERIOD = 10;

// Testbench Signals
reg clk;
reg rst;
reg en;
wire [7:0] count;

// Instantiate the DUT
simple_counter uut (
    .clk(clk),
    .rst(rst),
    .en(en),
    .count(count)
);

// Clock Generation
always #(CLK_PERIOD/2) clk = ~clk;

// Test Sequence
initial begin
    // Initial values
    clk = 0;
    rst = 1;
    en = 0;

    // Apply reset
    #10;
    rst = 0;

    // Enable the counter
    #10;
    en = 1;

    // Run for a few clock cycles
    #100;

    // Disable the counter
    en = 0;

    // Run for a few more cycles
    #50;

    // Stop the simulation
    $finish;
end

// Display Results
initial begin
    $monitor("Time = %0t, rst = %b, en = %b, count = %d", $time, rst, en, count);
end

endmodule
