# NEXIS-4 electronic simulation

This repository hosts reproducible electrical simulations for the proposed four-level (0, 1.1, 2.2, 3.3 V) NEXIS-4 processor.

## Current scope
M26 checks a voltage-source driver and RC load in ngspice. **This is not a transistor-level four-level logic gate, adder, or fabricated SHA-256d processor.** It cannot establish power/performance advantages.

## Running
The GitHub Actions workflow installs ngspice on Ubuntu and runs `spice/levels.cir`, then uploads a voltage trace and log. Inspect the workflow's actual status before interpreting any results.

## Next engineering stages
1. Design and simulate transistor-level four-level sensing and regeneration.
2. Build and validate the 32-case four-level full-adder truth table with electrical settling/noise.
3. Characterize delay, energy, fan-out and margins versus a binary reference under comparable process assumptions.
4. Connect characterized cells to an exact SHA-256d RTL architecture.
