
# Static Timing Analyzer (STA)

**A custom Python static timing analyzer for gate-level digital circuits, featuring Liberty-based delay calculations, register-to-register timing analysis, critical-path reconstruction, and integration with a C++ VLSI router.**

## Overview

Static Timing Analysis (STA) evaluates timing in digital circuits without requiring functional simulation. It determines whether data can propagate between sequential elements within the timing constraints imposed by a clock.

This project implements a simplified STA engine in Python. It parses structural Verilog, Liberty timing libraries, and SDC clock constraints; builds a net-level connectivity model; calculates load-dependent cell delays; propagates arrival times; and identifies critical register-to-register paths.

The analyzer also exports critical-path nets for use by a companion [C++ Timing-Driven VLSI Router](https://github.com/Adi-Jain9/timing-driven-vlsi-router).

## Key Features

### 1. Custom Verilog, Liberty, and SDC Parsing

The analyzer extracts information from three input formats:

- **Structural Verilog (`.v`):** standard-cell instances, cell types, primary inputs and outputs, internal wires, and named pin connections.
- **Liberty (`.lib`):** cell and pin definitions, pin capacitances, combinational timing arcs, rise/fall propagation delays, clock-to-Q delays, setup constraints, and timing lookup tables.
- **SDC (`.sdc`):** clock name, clock port, and clock period.

These inputs form the circuit connectivity and timing model.

### 2. Circuit Connectivity and Load Capacitance

The tool builds a net-level connectivity representation using Python dictionaries. Each net stores its driver, connected load pins, and total load capacitance.

The simplified load calculation sums the input capacitances of all connected cell pins:

$$
C_{\text{load}} = \sum_{i=1}^{N} C_{\text{pin},i}
$$

This lets cell delays vary with fanout and the capacitance of connected gates. **Extracted wire capacitance is not yet included.**

### 3. Liberty-Based Delay Calculation

For a combinational cell, the analyzer identifies the input-to-output timing arc, reads its rising and falling delay tables, and interpolates using the output net's load capacitance.

For load capacitance $C$ between characterized capacitance points $C_1$ and $C_2$, linear interpolation is:

$$
d(C) = d_1 + \frac{C-C_1}{C_2-C_1}(d_2-d_1)
$$

Here, $d_1$ and $d_2$ are the characterized delays at $C_1$ and $C_2$, respectively.

The current implementation uses **the first input-transition row** of the Liberty tables and chooses the larger of the rise and fall delays as a simplified worst-case delay. It does not yet perform full two-dimensional interpolation using propagated slew.

### 4. Arrival-Time Propagation

The analyzer propagates signal arrival times through combinational logic:

- Primary inputs begin with an arrival time of zero in the current model.
- Flip-flop outputs begin with their clock-to-Q delay.
- Combinational outputs are evaluated after the arrival times of their input nets are known.
- Each input-to-output arc produces a candidate arrival time; the maximum is retained.
- A predecessor record identifies the arc responsible for that maximum, supporting path reconstruction.

For a combinational output:

$$
AT_{\text{out}} = \max_i \left(AT_{\text{in},i} + d_i\right)
$$

Here, $AT$ denotes arrival time and $d_i$ is the propagation delay from input $i$ to the output.

### 5. Register-to-Register Timing Analysis

For each setup-constrained flip-flop data input, the analyzer reads the arriving signal's timing information and traces backward to its launching flip-flop.

The report includes the launch and capture registers, the intervening cells and nets, the total delay, and the setup slack. It reports the **maximum-arrival path to each eligible capture endpoint**, not every logically possible path.

### 6. Critical-Path Identification

The tool computes total setup-path delay as:

$$
D_{\text{total}} = AT_{\text{capture data}} + T_{\text{setup}}
$$

For the current simplified single-clock model:

$$
\text{Slack} = T_{\text{clock}} - D_{\text{total}}
$$

Positive setup slack means the path meets the modeled timing requirement. Negative setup slack means the modeled setup requirement is violated.

With one shared clock period and no modeled skew or uncertainty, the longest total-delay path also has the smallest setup slack.

## Example Results

The sample test circuit contains **15 standard-cell instances**: four D flip-flops, seven inverters, three two-input NAND gates, and one three-input NAND gate.

**Clock period: 730 ps**

| Priority | Launch → Capture | Total Delay | Setup Slack | Status |
|---|---|---:|---:|---|
| 1 | FF1 → FF4 | 720.2 ps | 9.8 ps | PASS |
| 2 | FF1 → FF2 | 710.6 ps | 19.4 ps | PASS |
| 3 | FF1 → FF3 | 700.0 ps | 30.0 ps | PASS |

### Critical Path

```text
FF1 -> q1 -> INV1 -> n1 -> INV3 -> n3 -> NAND1 -> n4
    -> NAND3 -> n8 -> NAND4 -> e_internal -> FF4
```

### Critical-Path Timing Breakdown

```text
FF1 clock-to-Q       250.0 ps
INV1                  84.0 ps
INV3                  75.6 ps
NAND1                125.2 ps
NAND3                 93.0 ps
NAND4                 82.4 ps
FF4 setup             10.0 ps
-----------------------------
Total delay          720.2 ps
Clock period         730.0 ps
Setup slack            9.8 ps

Timing: PASS
```

These figures come from the project's custom test library and simplified timing model. They are **not signoff timing measurements**.

## Integration with Timing-Driven Routing

The STA writes the nets along the selected critical path into `critical_nets.txt`:

```text
q1
n1
n3
n4
n8
e_internal
```

The companion [Timing-Driven VLSI Router](https://github.com/Adi-Jain9/timing-driven-vlsi-router) reads this file together with structural Verilog, LEF cell geometry, and cell placement data. Its current implementation builds a simplified placement/routing grid and identifies critical nets; shortest-path routing and timing-priority scheduling are under development.

A future improvement is to export **specific critical pin-to-pin branches**. A multi-terminal net can contain both critical and noncritical branches, so net names alone are not sufficient for precise branch prioritization.

## Project Files

```text
static-timing-analyzer/
├── koba.py             # Python STA implementation
├── koba.v              # Structural Verilog test circuit
├── cells.lib           # Custom Liberty timing library
├── koba.sdc            # Clock constraints
├── critical_nets.txt   # Generated critical-path nets
└── README.md           # Documentation
```

`critical_nets.txt` is generated when the analyzer runs; it does not need to be edited manually.

## Running the Analyzer

### Requirements

- Python 3
- Compatible structural Verilog, Liberty, and SDC input files

The implementation uses the Python standard library and does not require a third-party STA engine.

From the directory containing `koba.py`, `koba.v`, `cells.lib`, and `koba.sdc`, run:

```bash
python3 koba.py
```

The program prints the register-to-register path reports, identifies the critical path, checks its setup slack against the clock period, and generates `critical_nets.txt` for routing integration.

## Implementation Details

| Function | Purpose |
|---|---|
| `parse_verilog()` | Extract instances, nets, and named connections |
| `parse_liberty()` | Read cell pins, capacitance, timing arcs, and tables |
| `parse_sdc()` | Read basic clock constraints |
| `build_nets()` | Record drivers and loads; sum input capacitances |
| `interpolate_delay()` | Interpolate cell delay from load capacitance |
| `get_cell_delay()` | Calculate combinational propagation delay |
| `get_clock_to_q_delay()` | Determine flip-flop clock-to-Q delay |
| `get_setup_time()` | Read setup-time requirements |
| `propagate_arrival_times()` | Propagate worst-case arrival times and predecessors |
| `collect_timing_paths()` | Reconstruct paths to register data inputs |
| `find_critical_path()` | Select the maximum-delay path |

## Scope and Limitations

This is an educational implementation of a simplified **single-clock, register-to-register setup analysis**. It does not currently support:

- Full Verilog, Liberty, or SDC syntax
- Full two-dimensional delay interpolation or propagated input slew
- Separate rise/fall arrival-time propagation
- Extracted interconnect resistance and capacitance
- Clock-tree latency, clock skew, or clock uncertainty
- Hold-time analysis
- Generated clocks and advanced timing exceptions
- Enumeration of every possible timing path
- Constrained input-to-register or register-to-output timing reports
- Production-level signoff timing analysis

## Future Work

- Use both input slew and load capacitance in Liberty table interpolation.
- Propagate output transition times between gates.
- Model routed wire resistance, capacitance, and delay.
- Extend clock constraints and add hold-time checks.
- Export exact timing-critical net branches and timing priorities.
- Re-run STA after physical routing to evaluate changes in path delay and slack.

## Motivation

This project was built to understand how timing engines reconstruct and analyze signal paths through digital circuits. It combines graph-based connectivity, timing lookup tables, capacitance-dependent delays, and critical-path analysis in a custom Python implementation.

Together with the companion C++ router, it provides a foundation for exploring **timing-driven electronic design automation (EDA), VLSI CAD, and physical-design optimization**.

