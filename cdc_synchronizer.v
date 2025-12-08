
// cdc_synchronizer.v
//
// A simple module to demonstrate Clock Domain Crossing (CDC) for a single bit.
// It uses a two-flop synchronizer to pass a signal from a fast clock domain
// to a slow clock domain.

module cdc_synchronizer (
    // Fast Clock Domain Inputs
    input clk_fast,
    input rst_fast,
    input data_in_fast,

    // Slow Clock Domain Inputs & Outputs
    input clk_slow,
    input rst_slow,
    output data_out_slow
);

// Internal signals for the two-flop synchronizer.
// These are in the destination (slow) clock domain.
reg sync_ff1;
reg sync_ff2;

// The first flip-flop captures the asynchronous input signal.
// Its output may be metastable.
always @(posedge clk_slow or posedge rst_slow) begin
    if (rst_slow)
        sync_ff1 <= 1'b0;
    else
        sync_ff1 <= data_in_fast;
end

// The second flip-flop samples the output of the first.
// This significantly reduces the probability of metastability
// propagating into the rest of the slow clock domain logic.
always @(posedge clk_slow or posedge rst_slow) begin
    if (rst_slow)
        sync_ff2 <= 1'b0;
    else
        sync_ff2 <= sync_ff1;
end

// Assign the synchronized signal to the output.
assign data_out_slow = sync_ff2;

endmodule
