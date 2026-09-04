# Scripts

All scripts resolve their input and output paths from their own location, so
they can be launched from any working directory. Figures and derived CSVs are
written to `figures/` at the repository root.

| Script | Produces | Requires |
|---|---|---|
| `run_validation.m` | Table 3 of the paper (per-phase MAPE, RMSE, match) plus the twin-vs-plant and PID comparison figures | MATLAB |
| `make_fig_results.py` | Fig. 2 of the paper and the system block diagram | Python 3, `matplotlib`, `numpy` |
| `make_fig_pipeline.py` | Fig. 1 of the paper (end-to-end pipeline) | Python 3, `matplotlib` |
| `baseline_check.py` | Quick sanity check of a Simulink `.mat` export | Python 3, `h5py`, `matplotlib`, `numpy` |

```
matlab -batch "run('implementation/scripts/run_validation.m')"
python3 implementation/scripts/make_fig_results.py
python3 implementation/scripts/make_fig_pipeline.py
```

## Two notes on `run_validation.m`

**It does not call Simulink.** The script integrates the same lumped-parameter
equations as `../Peltier_DigitalTwin.slx` with a forward-Euler step of 1 s,
matching the firmware sampling period, so that the simulated trace can be
compared sample by sample with the telemetry. The `.slx` model is the reference
implementation of those equations; the script is the reproducible path to the
published numbers.

**Simulation horizon and metric windows differ on purpose.** The simulation runs
over the nominal 6840 s mission profile, while the metric windows for SP3 close
at 6600 s because the recorded dataset stops at 6599.4 s. Samples outside the
dataset simply do not exist, so the mask selects the 960 SP3 samples that were
actually logged. This is why Table 3 reports N = 960 for SP3 and N = 4560 in
total.

## Model parameters

The lumped-parameter values used by the scripts and by the Simulink model are:

| Parameter | Value |
|---|---|
| Seebeck coefficient, alpha | 0.0152 V/K |
| Electrical resistance, R | 2.04 ohm |
| Thermal conductance, K | 0.52 W/K |
| Hot-side thermal capacitance, C_h | 1419 J/K |
| Cold-side thermal capacitance, C_c | 587 J/K |
| PID gains | Kp = 0.5, Ki = 0.01, Kd = 0 |
| Safety threshold, T_h,max | 60 degC |

C_h and C_c are effective lumped capacitances calibrated on the cool-down
transients. They represent the whole thermal mass seen by each side, which
includes the heat sink, the cell, the clamping hardware and the thermal
interface, not the bare heat-sink geometry.
