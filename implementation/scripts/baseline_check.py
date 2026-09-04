"""
analisi_baseline.py
Analisi rapida del .mat di baseline (guadagni originali [0.5,0.01,0]).
Stampa statistiche chiave e genera figura di confronto.
"""

import h5py
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

MAT_FILE = 'Risultati_Simulazione.mat'
OUT_FIG  = 'Baseline_check.png'

# ── leggi il .mat ────────────────────────────────────────────────────────────
with h5py.File(MAT_FILE, 'r') as f:
    raw_z = np.array(f['#refs#']['z'])
    raw_p = np.array(f['#refs#']['p'])

time = raw_p.flatten()
N    = len(time)

# orienta data -> (N, 8): la dimensione lunga deve essere N
if raw_z.shape[0] == N:
    data = raw_z          # già (N, 8)
elif raw_z.shape[1] == N:
    data = raw_z.T        # trasponi -> (N, 8)
else:
    raise ValueError(f"Forma inattesa z: {raw_z.shape}, N={N}")
dur  = time[-1]

# colonne: 0=T_fredda, 1=Setpoint, 2=V_cella, 3=Corrente,
#          4=Potenza, 5=DeltaT, 6=T_fredda(dup), 7=T_calda
T_fredda = data[:, 0]
Setpoint = data[:, 1]
V_cella  = data[:, 2]
Corrente = data[:, 3]
T_calda  = data[:, 7]

print(f"\n{'='*60}")
print(f"FILE: {MAT_FILE}")
print(f"Campioni: {N:,}   Durata: {dur:.0f} s   Step medio: {dur/(N-1)*1000:.2f} ms")
print(f"{'='*60}")
print(f"{'Grandezza':<20} {'Min':>8} {'Max':>8} {'Fine':>8}")
print(f"{'-'*48}")
for nome, sig in [('T_fredda [°C]', T_fredda),
                  ('T_calda  [°C]', T_calda),
                  ('Setpoint [°C]', Setpoint),
                  ('V_cella  [V]',  V_cella),
                  ('Corrente [A]',  Corrente)]:
    print(f"{nome:<20} {np.min(sig):>8.3f} {np.max(sig):>8.3f} {sig[-1]:>8.3f}")
print(f"{'='*60}")

# dead-time: campioni con T_fredda entro ±0.1°C dal valore iniziale
T0 = T_fredda[0]
mask_flat = np.abs(T_fredda - T0) < 0.1
if mask_flat.any():
    idx_end_flat = np.where(~mask_flat)[0]
    dead_time = time[idx_end_flat[0]] if len(idx_end_flat) else dur
else:
    dead_time = 0.0
print(f"\nDead-time stimato (T_fredda fermo entro ±0.1°C): {dead_time:.1f} s")

# RMSE post dead-time
mask_post = time > dead_time
if mask_post.sum() > 10:
    rmse_fredda = np.sqrt(np.mean((T_fredda[mask_post] - Setpoint[mask_post])**2))
    print(f"RMSE T_fredda post-startup:  {rmse_fredda:.3f} °C")

print()

# ── figura ────────────────────────────────────────────────────────────────────
fig, axes = plt.subplots(3, 1, figsize=(12, 9), sharex=True)
fig.suptitle(f'Baseline check — guadagni [0.5, 0.01, 0]  |  durata {dur:.0f} s', fontsize=13)

ax = axes[0]
ax.plot(time, T_fredda, 'b', lw=1.2, label='T_fredda sim')
ax.plot(time, Setpoint, 'k--', lw=1, label='Setpoint')
ax.axvline(dead_time, color='orange', ls=':', label=f'dead-time ≈{dead_time:.0f}s')
ax.set_ylabel('Temperatura [°C]')
ax.legend(fontsize=8); ax.grid(alpha=0.3)

ax = axes[1]
ax.plot(time, T_calda, 'r', lw=1.2, label='T_calda sim')
ax.set_ylabel('T_calda [°C]')
ax.legend(fontsize=8); ax.grid(alpha=0.3)

ax = axes[2]
ax.plot(time, V_cella, 'g', lw=1, label='V_cella [V]')
ax.plot(time, Corrente, 'm', lw=1, label='Corrente [A]')
ax.set_ylabel('V / I')
ax.set_xlabel('Tempo [s]')
ax.legend(fontsize=8); ax.grid(alpha=0.3)

plt.tight_layout()
plt.savefig(OUT_FIG, dpi=130)
print(f"Figura salvata: {OUT_FIG}\n")
