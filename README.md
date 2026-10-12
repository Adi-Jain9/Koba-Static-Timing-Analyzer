# Python Static Timing Analyzer (STA)

A custom static timing analysis tool written in Python that parses structural Verilog, Liberty timing libraries, and SDC clock constraints to evaluate circuit timing, identify critical paths, and calculate setup slack.

The project explores how timing information propagates through digital circuits and how cell delays, fanout capacitance, and setup constraints affect circuit performance.

The analyzer also exports timing-critical nets for integration with a separate **C++ timing-driven VLSI router**.

## Overview

Static Timing Analysis (STA) determines whether signals can propagate through a digital circuit within specified timing constraints without requiring functional simulation.

This project implements a simplified gate-level STA flow that:

1. Parses circuit connectivity from structural Verilog.
2. Extracts cell timing information from Liberty.
3. Reads clock-period constraints from SDC.
4. Constructs net connectivity and calculates capacitive loads.
5. Propagates signal arrival times through combinational logic.
6. Reconstructs register-to-register timing paths.
7. Calculates setup slack and identifies the critical path.
8. Exports critical nets for timing-driven physical routing.

## Features

### Structural Verilog Parsing

Implements a custom parser to extract:

- Standard-cell instances and cell types
- Named pin-to-net connections
- Primary inputs and outputs
- Internal wires and signal connectivity

The parsed circuit representation is used to determine how signals travel between cells.

### Liberty Timing Analysis

Parses Liberty (`.lib`) files to extract:

- Cell and pin definitions
- Pin direction and input capacitance
- Input-to-output timing arcs
- Rising and falling propagation delays
- Clock-to-Q delays
- Setup-time constraints
- Timing lookup tables

Cell delays are calculated using output load capacitance and linear interpolation between characterized capacitance points.

The current implementation uses the first input-transition row of each delay table and selects the larger of the rise and fall delays for a simplified worst-case analysis.

### Arrival-Time Propagation

Constructs a net-level connectivity representation and propagates signal arrival times through combinational gates.

For each combinational output, the analyzer evaluates the available input-to-output timing arcs and retains the maximum arrival time.

The propagation model includes:

- Primary inputs initialized with zero arrival time
- Flip-flop outputs initialized using clock-to-Q delay
- Output load capacitance calculated from connected input pins
- Maximum-delay propagation through combinational logic
- Predecessor tracking for critical-path reconstruction

### Critical-Path Analysis

Traces the worst-arriving signal path backward from each register's setup-constrained data input.

For each path, the analyzer reports:

- Launch and capture flip-flops
- Sequence of cells and nets
- Individual cell delays
- Data arrival time
- Capture-register setup time
- Total timing delay
- Setup slack

Setup slack is calculated using:

**Slack = Clock Period − (Data Arrival Time + Setup Time)**

A path with negative setup slack violates the simplified timing constraint.

### Multi-Endpoint Timing Comparison

Analyzes paths terminating at multiple capture flip-flops and ranks them from largest total delay to smallest.

This makes it possible to identify the most timing-critical register-to-register path in a circuit containing multiple logic branches.

### Timing-Driven Router Integration

Exports the critical path's net names to `critical_nets.txt`.

This output is used by a companion C++ VLSI routing project to identify timing-sensitive connections.

**Companion project:** [Timing-Driven VLSI Router](https://github.com/Adi-Jain9/timing-driven-vlsi-router)

The router currently parses placement, LEF, and Verilog data, builds a routing grid, and imports STA-generated critical nets. Timing-priority path routing is under development.

## Example Timing Results

The current test circuit contains four flip-flops and multiple branching combinational paths.

Clock period: **730 ps**

| Priority | Timing path | Total delay | Setup slack |
|---|---|---:|---:|
| 1 | FF1 → FF4 | 720.2 ps | 9.8 ps |
| 2 | FF1 → FF2 | 710.6 ps | 19.4 ps |
| 3 | FF1 → FF3 | 700.0 ps | 30.0 ps |

### Critical Path

```text
FF1 -> q1 -> INV1 -> n1 -> INV3 -> n3
    -> NAND1 -> n4 -> NAND3 -> n8
    -> NAND4 -> e_internal -> FF4
```

**Critical-path timing breakdown:**

```text
FF1 clock-to-Q:    250.0 ps
INV1:               84.0 ps
INV3:               75.6 ps
NAND1:             125.2 ps
NAND3:              93.0 ps
NAND4:              82.4 ps
FF4 setup:          10.0 ps
---------------------------
Total delay:       720.2 ps
Clock period:      730.0 ps
Setup slack:         9.8 ps

Timing: PASS
```

These results are generated using the project's simplified timing model and custom timing library; they are not signoff timing measurements.

## Project Files

The primary analysis files are:

| File | Purpose |
|---|---|
| `koba.py` | Python STA implementation |
| `koba.v` | Structural Verilog test circuit |
| `cells.lib` | Cell timing and capacitance information |
| `koba.sdc` | Clock-period constraints |
| `critical_nets.txt` | Generated list of critical-path nets |

## Running the Analyzer

**Requirements:** Python 3 and the circuit input files.

Run the analyzer from the directory containing the input files:

```bash
python3 koba.py
```

The program parses the circuit and timing constraints, calculates register-to-register timing paths, and prints the timing report.

It also generates `critical_nets.txt`, containing the critical path's net names:

```text
q1
n1
n3
n4
n8
e_internal
```

## Implementation Details

The analyzer is implemented in Python using custom parsing and timing-analysis logic rather than an external STA engine.

**Important implementation choices:**

- Net-level connectivity is represented with Python dictionaries.
- Total load capacitance is computed from connected input pins.
- Timing arcs are selected using Liberty `related_pin` information.
- Cell delays are interpolated from timing lookup tables.
- Arrival times are propagated through combinational logic.
- A predecessor record tracks the input responsible for the maximum arrival time at each net.
- Timing paths are reconstructed by tracing predecessors backward from capture-register data pins.
- Paths are ranked by total delay for the single-clock test circuit.

## Current Limitations

This project is an educational STA implementation and does not replace a production timing engine.

Current limitations include:

- Simplified structural Verilog support
- No full Liberty or SDC language support
- No physical wire resistance/capacitance extraction
- No detailed interconnect delay modeling
- No propagated input slew between cells
- Only one input-transition row used for cell-delay interpolation
- Rise/fall propagation simplified to the larger delay
- No clock-tree latency, skew, or uncertainty modeling
- No hold-time analysis
- No full path enumeration; the analyzer retains the maximum-arrival predecessor for each net
- Primary-input-to-register paths are not included in the register-to-register report

## Future Improvements

- Implement two-dimensional Liberty lookup-table interpolation using both input slew and output capacitance.
- Propagate rise/fall transition times through the timing graph.
- Add interconnect RC delay estimates.
- Extend setup/hold analysis and clock constraints.
- Report multiple paths per endpoint.
- Export critical-path branches and slack information for more precise routing priorities.
- Reevaluate timing after physical routing to study how wire length and congestion affect critical paths.

## Project Goal

The objective is to understand and implement the fundamentals of static timing analysis while building toward a combined timing-analysis and physical-routing workflow.

By integrating the Python STA with a C++ router, the project aims to explore how timing violations and critical-path information can influence routing decisions and how physical interconnect affects overall circuit performance.
