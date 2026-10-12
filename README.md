# Static Timing Analyzer (STA)

**A custom Python static timing analyzer for gate-level digital circuits, featuring Liberty-based delay calculations, register-to-register timing analysis, critical-path reconstruction, and integration with a C++ VLSI router.**

## Overview

Static Timing Analysis (STA) evaluates the timing performance of digital circuits without requiring functional simulation. It determines whether signals can propagate between sequential elements within the timing constraints imposed by the clock.

This project implements a custom STA engine in Python to explore the algorithms and data structures underlying digital timing analysis.

The analyzer reads structural Verilog, Liberty timing libraries, and SDC clock constraints to construct a circuit connectivity model, calculate cell delays using capacitive loads, propagate signal arrival times, and identify critical register-to-register paths.

The project also integrates with a separate [C++ Timing-Driven VLSI Router](https://github.com/Adi-Jain9/timing-driven-vlsi-router), providing timing-critical net information for future physical routing optimization.

## Key Features

### 1. Custom Verilog, Liberty, and SDC Parsing

Implements parsers that extract circuit structure and timing information from three input formats.

**Structural Verilog (`.v`)**
- Standard-cell instances and cell types
- Primary inputs and outputs
- Internal signal nets
- Named pin connections
- Connectivity between gates and sequential elements

**Liberty (`.lib`)**
- Standard-cell definitions
- Pin directions and input capacitances
- Combinational timing arcs
- Rising and falling cell delays
- Clock-to-Q propagation delays
- Flip-flop setup constraints
- Timing lookup tables and interpolation indices

**Synopsys Design Constraints (`.sdc`)**
- Clock name
- Clock input port
- Clock period

These inputs are combined to construct an internal representation of the circuit and its timing characteristics.

### 2. Circuit Connectivity and Load Capacitance

Builds a net-level connectivity representation using Python dictionaries.

Each net stores information about its driving pin, connected load pins, and total capacitive load.

The total load capacitance is calculated from the input capacitances of connected cell pins:

$$
C_{\text{load}}=\sum_{i=1}^{N}C_{\text{pin},i}
$$

This allows cell delays to vary based on fanout and the capacitance of connected gates.

### 3. Liberty-Based Delay Calculation

Calculates propagation delays using timing arcs extracted from Liberty.

For combinational cells, the analyzer:

1. Identifies the relevant input-to-output timing arc.
2. Determines the capacitive load on the output net.
3. Reads the corresponding rising and falling delay tables.
4. Uses linear interpolation between characterized capacitance values.
5. Selects the larger propagation delay for simplified worst-case analysis.

Linear interpolation is calculated using:

$$
d(C)=d_1+\frac{C-C_1}{C_2-C_1}(d_2-d_1)
$$

where \(C\) is the calculated load capacitance and \(d_1,d_2\) are the characterized delays at capacitances \(C_1,C_2\).

The current implementation uses a fixed input-transition row of the Liberty lookup tables. Full two-dimensional interpolation and slew propagation are not yet implemented.

### 4. Arrival-Time Propagation

Propagates signal arrival times through the circuit's combinational logic.

- Primary inputs are initialized with zero arrival time.
- Flip-flop outputs are initialized using their clock-to-Q delay.
- Combinational outputs are evaluated after their input arrival times become available.
- Each input-to-output timing arc contributes a candidate arrival time.
- The maximum candidate arrival time is retained for each output net.

For a combinational gate:

$$
AT_{\text{out}}=\max_i(AT_{\text{in},i}+d_i)
$$

The analyzer also tracks the predecessor responsible for each maximum arrival time, enabling critical-path reconstruction.

### 5. Multi-Endpoint Timing Analysis

Collects and compares timing paths terminating at multiple flip-flop data inputs.

For each capture register, the analyzer:

- Identifies the data input with a setup constraint.
- Retrieves the corresponding arrival time.
- Traces the maximum-arrival path backward through combinational logic.
- Identifies the launching flip-flop.
- Includes the capture flip-flop's setup requirement.
- Calculates total timing delay and setup slack.

The current implementation reports one maximum-arrival path per eligible endpoint rather than enumerating every possible path.

### 6. Critical-Path Identification

Compares register-to-register paths to determine the most timing-critical endpoint.

Total path delay is defined as:

$$
D_{\text{total}}=AT_{\text{capture data}}+T_{\text{setup}}
$$

For the project's simplified single-clock timing model:

$$
\text{Slack}=T_{\text{clock}}-D_{\text{total}}
$$

A positive setup slack indicates that the path meets the modeled clock constraint, while a negative slack indicates a setup timing violation.

Paths are ranked by total delay, with the longest path considered critical under the shared clock-period assumption.

## Example Results

The test circuit contains 15 standard-cell instances:

- 4 D flip-flops
- 7 inverters
- 3 two-input NAND gates
- 1 three-input NAND gate

The circuit contains multiple reconvergent combinational branches and three register-to-register capture endpoints.

**Clock Period: 730 ps**

| Priority | Launch → Capture | Total Delay | Setup Slack | Status |
|---|---|---:|---:|---|
| 1 | FF1 → FF4 | 720.2 ps | 9.8 ps | PASS |
| 2 | FF1 → FF2 | 710.6 ps | 19.4 ps | PASS |
| 3 | FF1 → FF3 | 700.0 ps | 30.0 ps | PASS |

### Identified Critical Path

```text
FF1
  |
  q1
  |
 INV1
  |
  n1
  |
 INV3
  |
  n3
  |
 NAND1
  |
  n4
  |
 NAND3
  |
  n8
  |
 NAND4
  |
e_internal
  |
 FF4
```

**Cell delay breakdown**

```text
FF1 clock-to-Q       250.0 ps
INV1                  84.0 ps
INV3                  75.6 ps
NAND1                125.2 ps
NAND3                 93.0 ps
NAND4                 82.4 ps
FF4 setup             10.0 ps
--------------------------------
Total delay          720.2 ps
Clock period         730.0 ps
Setup slack            9.8 ps

Timing: PASS
```

The critical path ends at FF4 and has the smallest setup slack among the three analyzed endpoints.

These results are based on the project's custom timing library and simplified delay model, not a production signoff analysis.

## Integration with Timing-Driven Physical Routing

The STA project serves as the timing-analysis component of a larger VLSI design automation workflow.

After identifying the critical path, the analyzer exports its signal nets to a text file:

**`critical_nets.txt`**

Example:

```text
q1
n1
n3
n4
n8
e_internal
```

The companion C++ router reads this file alongside structural Verilog, LEF geometry, and cell placement information.

This provides a foundation for routing timing-sensitive connections before less critical connections.

**Related repository:** [Timing-Driven VLSI Router](https://github.com/Adi-Jain9/timing-driven-vlsi-router)

The physical routing and optimization stages are being developed separately.

## Project Structure

Core project files:

```text
static-timing-analyzer/
├── koba.py             # Python STA implementation
├── koba.v              # Structural Verilog test circuit
├── cells.lib           # Custom Liberty timing library
├── koba.sdc            # Clock timing constraints
├── critical_nets.txt   # Generated critical-path net list
└── README.md           # Project documentation
```

## Getting Started

### Requirements

- Python 3
- Structural Verilog test circuit
- Compatible Liberty timing library
- SDC clock constraints

The implementation uses Python's standard library and does not require an external STA engine.

### Running the Analyzer

Clone the repository and navigate to the project directory.

Run:

```bash
python3 koba.py
```

The analyzer reads `koba.v`, `cells.lib`, and `koba.sdc` from the current working directory.

### Generated Output

The program reports:

- Register-to-register timing paths
- Launch and capture registers
- Cell and net sequences
- Total path delays
- Setup slack for each endpoint
- Overall critical path
- Individual delays along the critical path
- Clock period and timing pass/fail status

It also generates `critical_nets.txt` for use by the companion C++ router.

## Implementation

The STA engine is written in Python and implements its parsing, connectivity modeling, delay calculation, and timing propagation directly.

**Core components**

| Component | Responsibility |
|---|---|
| `parse_verilog()` | Extract circuit instances and connectivity |
| `parse_liberty()` | Extract cell definitions and timing data |
| `parse_sdc()` | Read clock constraints |
| `build_nets()` | Construct net connectivity and calculate load capacitances |
| `interpolate_delay()` | Estimate delay from capacitance lookup values |
| `get_cell_delay()` | Calculate combinational cell propagation delay |
| `get_clock_to_q_delay()` | Calculate flip-flop clock-to-Q delay |
| `get_setup_time()` | Determine capture-register setup requirement |
| `propagate_arrival_times()` | Propagate maximum arrival times and track predecessors |
| `collect_timing_paths()` | Reconstruct register-to-register timing paths |
| `find_critical_path()` | Identify the maximum-delay path |

## Scope and Limitations

This is an educational gate-level STA implementation intended to demonstrate fundamental timing-analysis concepts.

The following capabilities are currently outside its implemented scope:

- Full Verilog, Liberty, and SDC language support
- Full two-dimensional timing-table interpolation
- Input slew and output transition propagation
- Separate rising and falling timing-state propagation
- Extracted interconnect resistance and capacitance
- Clock skew, clock-tree latency, and uncertainty
- Hold-time analysis
- Generated clocks and advanced timing exceptions
- Complete timing-path enumeration
- Constrained primary-input-to-register and register-to-output timing analysis
- Production-level static timing signoff

The current timing engine focuses on simplified single-clock register-to-register setup analysis.

## Future Development

Planned improvements include:

- Input-slew-dependent delay calculations using two-dimensional Liberty interpolation
- Output slew propagation through the circuit
- Interconnect RC delay estimation
- Expanded timing constraint support
- Hold-time analysis
- Detailed critical-path and slack reporting
- Exporting timing-critical pin-to-pin branches rather than only net names
- Incorporating routed wire-length information into timing calculations
- Iterative timing analysis and physical routing optimization

## Motivation

Static Timing Analysis plays a central role in digital circuit design, helping engineers identify timing bottlenecks before fabrication.

This project was developed to gain a deeper understanding of the underlying timing algorithms, including graph-based connectivity, delay propagation, capacitive loading, timing constraints, and critical-path reconstruction.

By combining the STA engine with a separate C++ routing project, the broader objective is to investigate how software algorithms can use timing information to guide physical design decisions and improve circuit performance.

The project is an ongoing exploration of **electronic design automation (EDA), VLSI CAD, graph algorithms, and timing-driven design optimization**.
