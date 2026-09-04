# Peltier Digital Twin: an open-source CPS benchmark

Reference artefacts for the paper

> **An Open-Source CPS Benchmark Architecture with a Thermoelectric Digital-Twin Use Case**
> Lorenzo Raspaolo, Riccardo Berta, Luca Lazzaroni, Sandro Pastore, Francesco Bellotti
> ApplePies 2026, Bologna. Springer, Lecture Notes in Electrical Engineering.

The paper defines a seven-component benchmark architecture for open-source
cyber-physical systems and instantiates it on a Bi2Te3 Peltier thermoelectric
cooler. This repository is the reproducibility package `R` of that architecture:
every artefact the paper refers to is here.

## The seven components

| Symbol | Component | Where it lives |
|---|---|---|
| `P` | Physical plant | `materials/`, plus the bill of materials in `report/` |
| `S/A` | Sensors and actuators | `materials/`, `implementation/Driver_FW/` |
| `C` | Embedded controller | `implementation/Driver_FW/Driver_FW.ino` |
| `D` | Digital twin | `implementation/Peltier_DigitalTwin.slx` |
| `F` | Formal model | `modelling&verification/Peltier_UPPAAL.xml` |
| `L` | Logs and datasets | `implementation/dataset/` |
| `R` | Reproducibility package | this repository |

## Layout

```
implementation/
  Driver_FW/          firmware and serial logger
  Peltier_DigitalTwin.slx
  dataset/            released telemetry + column dictionary
  scripts/            regenerate the paper figures and metrics
modelling&verification/
  Peltier_UPPAAL.xml  timed automata + the four verified CTL queries
materials/            component datasheets
report/               full course report the paper derives from
figures/              created on first run of the scripts
```

Each directory has its own README with the details.

## Reproducing the published results

```
matlab -batch "run('implementation/scripts/run_validation.m')"   # Table 3
python3 implementation/scripts/make_fig_results.py               # Fig. 2
python3 implementation/scripts/make_fig_pipeline.py              # Fig. 1
```

Expected output, over the 4560 active-phase samples of the released dataset:

| Phase | MAPE | RMSE | N |
|---|---|---|---|
| SP1 = 22 degC | 1.4 % | 0.32 K | 1800 |
| SP2 = 20 degC | 2.8 % | 0.58 K | 1800 |
| SP3 = 18 degC | 7.2 % | 1.31 K | 960 |
| **Active total** | **3.2 %** | **1.38 K** | **4560** |

For the formal model, open `modelling&verification/Peltier_UPPAAL.xml` in
UPPAAL 5.x and run the four stored queries: all four are satisfied, each in
under 1 s.

## Testbench at a glance

- Bi2Te3 Peltier module, 16 mm side, characterised in situ: alpha = 0.0152 V/K, R = 2.04 ohm, K = 0.52 W/K
- 2x PT100 on MAX31865 SPI converters, Rref = 430 ohm
- AOD4184A MOSFET, software PWM at 100 Hz
- Arduino UNO Q (Cortex-M33, Zephyr RTOS), 1 Hz control and telemetry super-loop
- Passive aluminium heat sinks, no fan
- Safety threshold T_h,max = 60 degC, shared by firmware and formal model

## Tooling

MATLAB/Simulink R2024b or later, UPPAAL 5.x, Python 3.10 or later with
`matplotlib`, `numpy` and `h5py`, Arduino IDE 2.x with the Arduino UNO Q core
and the `Adafruit_MAX31865` and `PID_v1` libraries.

## Citing

Please cite the ApplePies 2026 paper above. A BibTeX entry will be added once
the volume DOI is assigned.
