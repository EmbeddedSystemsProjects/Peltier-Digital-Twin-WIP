# Implementation

| Path | Content |
|---|---|
| `Driver_FW/Driver_FW.ino` | Embedded firmware: Arduino sketch running on the Zephyr RTOS kernel of the Arduino UNO Q. Implements the five-state supervisory FSM, the reverse-mode PID (`PID_v1`), the 100 Hz software PWM via a Zephyr `k_timer` ISR, and the CSV telemetry. |
| `Driver_FW/log_seriale.py` | Serial logger that records the telemetry stream to CSV. |
| `Peltier_DigitalTwin.slx` | MATLAB/Simulink lumped-parameter digital twin. |
| `dataset/` | Released telemetry, with its column dictionary. |
| `scripts/` | Scripts that regenerate the figures and the validation metrics of the paper. |

## Firmware

- MCU: Arduino UNO Q (ABX00162), ARM Cortex-M33, Zephyr RTOS. The Qualcomm Linux coprocessor is not used.
- Sensing: 2x PT100 on MAX31865 SPI converters, Rref = 430 ohm, Callendar-Van Dusen linearisation.
- Actuation: AOD4184A N-channel MOSFET, software PWM at 100 Hz, duty resolution 1 %.
- Control: reverse-mode PID, Ts = 1 s, Kp = 0.5, Ki = 0.01, Kd = 0.
- Safety: `T_h,max` = 60 degC, shared verbatim with the UPPAAL model.

The FSM has five states: `INIT` (PT100 self-test), `STANDBY` (actuator off),
`ACTIVE_CONTROL` (closed PID loop), `DEAD_BAND` (setpoint hysteresis, limits
actuator chattering) and `THERMAL_FAULT` (absorbing safety state).

## Digital twin

`Peltier_DigitalTwin.slx` models the cell through the Peltier, Joule and
conduction terms, with each heat sink as a lumped thermal mass. The subsystem
`Cella_di_Peltier` implements the coupled heat-flow equations; the heat-sink
capacitances are computed from geometry and material properties inside the
model.

To reproduce the published metrics use `scripts/run_validation.m`, which
integrates the same equations in MATLAB. See `scripts/README.md` for why the
two paths coexist.
