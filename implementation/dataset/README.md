# Dataset

## `test_peltier_20260620_095618.csv`

Raw telemetry logged from the physical testbench on 2026-06-20 by
`../Driver_FW/log_seriale.py`, reading the serial stream emitted by
`../Driver_FW/Driver_FW.ino` at 115200 baud. **No post-processing has been
applied**: this is the file the firmware produced.

- Sampling rate: 1 Hz (firmware super-loop period)
- Samples: 6598
- Duration: 6599.4 s (110.0 min)
- Ambient temperature at start: 24.0 degC

## Column dictionary

The header uses the original firmware identifiers. Two of them are Italian and
are kept as emitted, so that the file matches the firmware byte for byte.

| Column | Unit | Meaning | Symbol in paper |
|---|---|---|---|
| `t_ms` | ms | Milliseconds since firmware boot | t |
| `setpoint` | degC | Cold-side temperature setpoint commanded by the supervisory FSM | SP |
| `T_fredda` | degC | Cold-side PT100 reading (Callendar-Van Dusen linearised) | T_c |
| `T_calda` | degC | Hot-side PT100 reading (Callendar-Van Dusen linearised) | T_h |
| `output_pid` | % | PID output, applied as PWM duty cycle on the AOD4184A MOSFET | D |
| `stato` | - | Supervisory FSM state: `INIT`, `STANDBY`, `ACTIVE_CONTROL`, `DEAD_BAND`, `THERMAL_FAULT` | - |

`T_fredda` = cold side, `T_calda` = hot side.

## Mission profile as executed

| Phase | Setpoint | Samples | t_start [s] | t_end [s] |
|---|---|---|---|---|
| STANDBY | - | 240 | 0.2 | 239.3 |
| SP1 | 22 degC | 1800 | 240.3 | 2039.4 |
| REST 1 | - | 899 | 2040.4 | 2939.3 |
| SP2 | 20 degC | 1800 | 2940.3 | 4739.5 |
| REST 2 | - | 899 | 4740.5 | 5639.4 |
| SP3 | 18 degC | 960 | 5640.4 | 6599.4 |

The SP3 phase was stopped at 960 s instead of the nominal 1200 s, so the run
ends at 6599.4 s. Metrics in the paper are computed over the 4560
`ACTIVE_CONTROL` samples of SP1, SP2 and SP3 only; REST and STANDBY phases are
excluded.
