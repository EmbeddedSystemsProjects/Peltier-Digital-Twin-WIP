# Formal model

## `Peltier_UPPAAL.xml`

UPPAAL timed-automata model of the firmware supervisory logic. Open it with
UPPAAL 5.x and run the four queries stored in the file.

Two templates:

| Template | Role |
|---|---|
| `Peltier_FSM` | The five-state supervisory FSM implemented in `../implementation/Driver_FW/Driver_FW.ino`: `INIT`, `STANDBY`, `ACTIVE_CONTROL`, `DEAD_BAND`, `THERMAL_FAULT` |
| `Environment` | Non-deterministic environment: operator commands and temperature evolution |

The safety threshold `T_hot > 60` appears here exactly as it appears in the
firmware guard, which is what makes the two levels semantically consistent.
The `urgent chan overheat` forces the fault transition to be taken before any
other action once the guard holds.

## Verified properties

| # | CTL formula | Meaning |
|---|---|---|
| 1 | `A[] not deadlock` | No deadlock |
| 2 | `E<> Process_1.THERMAL_FAULT` | The fault state is reachable, so property 3 is not vacuous |
| 3 | `(Process_1.ACTIVE_CONTROL and T_hot > 60) --> Process_1.THERMAL_FAULT` | Overtemperature always leads to the safety state |
| 4 | `(Process_1.INIT and pt100_ok == false) --> Process_1.THERMAL_FAULT` | A sensor fault at boot always leads to the safety state |

All four are satisfied, each in under 1 s on a desktop machine.

## Scope of the guarantee

The model abstracts the **supervisory logic**, not the thermal physics. It
proves that the state machine reacts correctly to an overtemperature condition;
it does not prove that the hardware stays below `T_h,max`. That depends on the
PT100 sensing chain and on the calibrated thermal model, and is outside the
scope of the formal verification.
