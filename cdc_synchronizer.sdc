
# cdc_synchronizer.sdc
#
# A conceptual SDC file for our cdc_synchronizer module.
# This demonstrates how timing constraints are applied to a design
# with multiple, asynchronous clock domains.

# --- Clock Definitions ---

# Define the fast clock: 100 MHz (10 ns period)
# We'll assume it's connected to the 'clk_fast' port of our module.
create_clock -name clk_fast -period 10.0 [get_ports clk_fast]

# Define the slow clock: 33.3 MHz (30 ns period)
# We'll assume it's connected to the 'clk_slow' port of our module.
create_clock -name clk_slow -period 30.0 [get_ports clk_slow]


# --- Clock Domain Crossing (CDC) Constraint ---

# By default, timing analysis tools will try to analyze all paths
# between flip-flops. However, the path from the fast domain to the
# slow domain is asynchronous and is handled by our synchronizer.
# We need to tell the tool not to analyze the timing of this path,
# as it will otherwise report a timing violation.

# We define the two clocks as being unrelated to each other.
set_clock_groups -asynchronous -group {clk_fast} -group {clk_slow}

# An alternative, more specific way to do this is to set a false path
# on the synchronizer flops. The 'set_clock_groups' command is generally
# preferred for entire domains, but a false path is useful for specific signals.
#
# The following is a commented-out example of a more specific constraint:
# set_false_path -from [get_pins data_in_fast] -to [get_pins sync_ff1/D]


# --- Input/Output Delays ---

# In a real design, you would also specify the delays of signals
# arriving at the inputs and required at the outputs. For this example,
# we'll omit them for simplicity.
#
# Example:
# set_input_delay -clock clk_fast 2.0 [get_ports data_in_fast]
# set_output_delay -clock clk_slow 5.0 [get_ports data_out_slow]
