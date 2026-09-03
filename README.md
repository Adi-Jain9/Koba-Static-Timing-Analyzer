# Koba Static Timing Analyzer

A Python static timing analyzer that parses structural Verilog, Liberty cell
models, and SDC clock constraints to determine circuit timing and identify the
critical path. All values are synthetic.

## Features

- Parses structural Verilog circuit connectivity
- Reads cell delays and capacitances from Liberty files
- Processes clock constraints from an SDC file
- Propagates arrival times through combinational logic
- Calculates setup time and slack
- Reconstructs the circuit's critical path using predecessor tracking

## Technologies

- Python
- Verilog
- Liberty
- SDC

## Project Files

- `koba.py` — timing-analysis implementation
- `koba.v` — structural Verilog circuit
- `cells.lib` — cell timing and capacitance definitions
- `koba.sdc` — clock constraints

## Running the Project

Keep the provided input files in the same directory, then run:

```bash
python3 koba.py
