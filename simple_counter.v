
module simple_counter(
    clk,
    rst,
    en,
    count
    );

// Port Declarations
input clk;
input rst;
input en;
output reg [7:0] count;

// Sequential Logic
always @(posedge clk or posedge rst)
begin
    if (rst)
        count <= 8'h00;
    else if (en)
        count <= count + 1'b1;
end

endmodule
