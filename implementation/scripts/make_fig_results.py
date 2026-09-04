"""
make_fig_results.py
Regenerates Fig. 2 of the paper (digital twin vs real plant) and the system
block diagram, from the released telemetry dataset.

    python3 make_fig_results.py

Output: figures/fig_risultati_sim.png, figures/fig_schema_sistema.png
Runs from any working directory; paths are resolved from the script location.
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import numpy as np
import csv, math, os

# --- repository paths (resolved from this script's location) -----------------
import os as _os
_HERE    = _os.path.dirname(_os.path.abspath(__file__))
_DATASET = _os.path.join(_HERE, '..', 'dataset')
_FIGURES = _os.path.join(_HERE, '..', '..', 'figures')
_os.makedirs(_FIGURES, exist_ok=True)
# ---------------------------------------------------------------------------


plt.rcParams.update({
    'font.family': 'DejaVu Sans',
    'font.size': 14,
    'axes.labelsize': 15,
    'axes.titlesize': 16,
    'xtick.labelsize': 13,
    'ytick.labelsize': 13,
    'legend.fontsize': 12,
    'figure.dpi': 100,
    'axes.grid': True,
    'grid.alpha': 0.35,
})
DPI_OUT = 200

def draw_box(ax, cx, cy, w, h, text, color='#E8F4FD', edgecolor='#2E86AB',
             fontsize=12, bold=False, radius=0.05):
    box = FancyBboxPatch((cx-w/2, cy-h/2), w, h,
                         boxstyle=f'round,pad={radius}',
                         facecolor=color, edgecolor=edgecolor, linewidth=2.0, zorder=3)
    ax.add_patch(box)
    weight = 'bold' if bold else 'normal'
    ax.text(cx, cy, text, ha='center', va='center', fontsize=fontsize,
            fontweight=weight, zorder=4, multialignment='center')

def draw_arrow(ax, x0, y0, x1, y1, label='', color='#333333', lw=1.8, offset=0.22, fontsize=11):
    ax.annotate('', xy=(x1, y1), xytext=(x0, y0),
                arrowprops=dict(arrowstyle='->', color=color, lw=lw), zorder=2)
    if label:
        mx, my = (x0+x1)/2, (y0+y1)/2
        dx, dy = x1-x0, y1-y0
        length = max(0.001, math.sqrt(dx**2 + dy**2))
        px, py = -dy/length, dx/length
        ax.text(mx + px*offset, my + py*offset, label,
                ha='center', va='center', fontsize=fontsize,
                color='#222222', style='italic', zorder=5,
                bbox=dict(boxstyle='round,pad=0.18', facecolor='white',
                          edgecolor='none', alpha=0.92))


# ═══════════════════════════════════════════════════════════════════
# FIGURE 1 – System block diagram (English)
# ═══════════════════════════════════════════════════════════════════
fig1, ax = plt.subplots(figsize=(10, 6))
ax.set_xlim(-0.3, 10.3); ax.set_ylim(0.1, 6.5)
ax.axis('off')
ax.set_facecolor('white'); fig1.patch.set_facecolor('white')
ax.set_title('Control System Block Diagram – Digital Twin Peltier',
             fontsize=15, fontweight='bold', pad=12)

C_HW  = '#E8F4FD'
C_FW  = '#FFF3CD'
C_PHY = '#D4EDDA'
C_SEN = '#F8D7DA'
C_PS  = '#E2E3E5'

y_main = 2.8
y_pid  = 4.6
y_hot  = 1.0

# Main chain
draw_box(ax, 0.9,  y_main, 1.2, 1.0, 'Power Supply\n6V / 3A',              color=C_PS,  fontsize=11)
draw_box(ax, 2.8,  y_main, 1.4, 1.0, 'MOSFET Driver\nPWM→V_cell',          color=C_HW,  fontsize=11)
draw_box(ax, 5.0,  y_main, 1.4, 1.2, 'Peltier Cell\n(Bi₂Te₃, 16mm)\nα=0.0152 V/K\nR=2.04 Ω',
                                                                              color=C_PHY, fontsize=10)
draw_box(ax, 7.2,  y_main, 1.4, 1.0, 'Cold side\nCf = 587 J/K',             color=C_PHY, fontsize=11)

# Hot side heat sink
draw_box(ax, 5.0,  y_hot,  1.4, 0.75, 'Hot side\nCh = 1419 J/K',            color=C_PHY, fontsize=10)

# Control chain
draw_box(ax, 2.8,  y_pid,  1.6, 0.85, 'Arduino UNO Q\nPID REVERSE\n1 Hz',   color=C_FW,  fontsize=11, bold=True)
draw_box(ax, 7.2,  y_pid,  1.4, 0.85, 'PT100 Sensor\n(T_cold)',              color=C_SEN, fontsize=11)

# Main chain arrows
draw_arrow(ax, 1.5, y_main, 2.1, y_main, '6V',              offset=0.18, fontsize=12)
draw_arrow(ax, 3.5, y_main, 4.3, y_main, 'V_cell\n[0–6V]',  offset=0.18, fontsize=12)
draw_arrow(ax, 5.7, y_main, 6.5, y_main, 'Q_c',             offset=0.18, fontsize=12)
draw_arrow(ax, 5.0, 2.2,   5.0, 1.375,  'Q_h',             offset=0.18, fontsize=12)

# Control arrows
draw_arrow(ax, 2.8, 4.175, 2.8, 3.3, 'PWM\n[0–100%]', offset=0.2, fontsize=12)
draw_arrow(ax, 7.2, 4.175, 7.2, 3.3, 'T_f [°C]',      offset=0.2, fontsize=12)

# Feedback arrow PT100 → Arduino
ax.annotate('', xy=(3.6, y_pid), xytext=(6.5, y_pid),
            arrowprops=dict(arrowstyle='<-', color='#333333', lw=2.0), zorder=2)
ax.text(5.05, y_pid + 0.18, 'T_cold  →  error = T_f − SP',
        ha='center', va='bottom', fontsize=11, style='italic', color='#555555',
        bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='none', alpha=0.9))

# Setpoint input
ax.text(1.0, y_pid, 'SP [°C]', ha='center', va='center', fontsize=12, fontweight='bold',
        color='#155724',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#D4EDDA', edgecolor='#28A745'))
ax.annotate('', xy=(2.0, y_pid), xytext=(1.45, y_pid),
            arrowprops=dict(arrowstyle='->', color='#333333', lw=1.8), zorder=2)

# Legend
leg_x, leg_y = 8.1, 5.8
for i, (col, lab) in enumerate([(C_HW,  'Electronic HW'),
                                  (C_FW,  'Firmware'),
                                  (C_PHY, 'Physical System'),
                                  (C_SEN, 'Sensor')]):
    rect = FancyBboxPatch((leg_x, leg_y - i*0.52), 0.3, 0.33,
                          boxstyle='round,pad=0.04', facecolor=col, edgecolor='#555555', linewidth=1.2)
    ax.add_patch(rect)
    ax.text(leg_x + 0.45, leg_y - i*0.52 + 0.165, lab, va='center', fontsize=11)

plt.tight_layout()
plt.savefig(_os.path.join(_FIGURES, 'fig_schema_sistema.png'),
            dpi=250, bbox_inches='tight', facecolor='white')
plt.close(fig1)
print('[OK] figures/fig_schema_sistema.png')


# ═══════════════════════════════════════════════════════════════════
# Simulation (identical physics, needed for Figure 2)
# ═══════════════════════════════════════════════════════════════════
alpha_p = 0.0152; R_p = 2.04; K_p = 0.52
V_sup = 6.0; I_mx = 4.0
Cf = 587.0; Ch = 1419.0; Kif = 0.1; Kih = 0.1; Tamb = 24.0
Kp_pid = 0.5; Ki_pid = 0.01
T_ST = [0, 240, 2040, 2940, 4740, 5640]
T_EN = [240, 2040, 2940, 4740, 5640, 6600]
SP_V = [None, 22, None, 20, None, 18]
N_SIM = 6600

fasi = [
    (0,    240,  25,  True,  'STANDBY'),
    (240,  2040, 22,  False, 'SP1 = 22 °C'),
    (2040, 2940, 22,  True,  'REST 1'),
    (4740, 5640, 20,  True,  'REST 2'),
    (2940, 4740, 20,  False, 'SP2 = 20 °C'),
    (5640, 6600, 18,  False, 'SP3 = 18 °C'),
]

def get_fase(t):
    for i in range(6):
        if T_ST[i] <= t < T_EN[i]:
            return i
    return 5

Tf_s = [Tamb] * (N_SIM+1)
Tc_s = [Tamb] * (N_SIM+1)
pid_s = [0.0] * (N_SIM+1)
sp_s = [None] * (N_SIM+1)
ITm = 0.0; pout = 0.0; fp_cur = -1

for k in range(N_SIM):
    fi = get_fase(k); sp = SP_V[fi]; sp_s[k] = sp
    if fi != fp_cur:
        ITm = 0.0; fp_cur = fi
    if sp is None:
        pout = 0.0; ITm = 0.0
    else:
        err = Tf_s[k] - sp
        ITm = max(0, min(100, ITm + Ki_pid * err))
        pout = max(0, min(100, Kp_pid * err + ITm))
    Vc = (pout/100) * V_sup
    Ic = min(I_mx, max(0, Vc / R_p))
    TfK = Tf_s[k] + 273.15; TcK = Tc_s[k] + 273.15; dT = Tc_s[k] - Tf_s[k]
    Qc = alpha_p*Ic*TfK - 0.5*R_p*Ic**2 - K_p*dT
    Qh = alpha_p*Ic*TcK + 0.5*R_p*Ic**2 - K_p*dT
    Tf_s[k+1] = Tf_s[k] + (-Qc + Kif*(Tamb - Tf_s[k])) / Cf
    Tc_s[k+1] = Tc_s[k] + ( Qh - Kih*(Tc_s[k] - Tamb)) / Ch
    pid_s[k+1] = pout
sp_s[N_SIM] = SP_V[get_fase(N_SIM-1)]

t_arr  = np.arange(N_SIM+1) / 60.0
Tf_arr = np.array(Tf_s); Tc_arr = np.array(Tc_s)
sp_arr = np.array([s if s is not None else float('nan') for s in sp_s])

# Load real CSV
csv_path_r = _os.path.join(_DATASET, 'test_peltier_20260620_095618.csv')
has_r = False; t_r = []; Tf_r = []; Tc_r = []
if os.path.isfile(csv_path_r):
    try:
        with open(csv_path_r, 'r') as f:
            rdr = csv.reader(f)
            next(rdr)
            for row in rdr:
                try:
                    t_r.append(float(row[0])/1000/60)
                    Tf_r.append(float(row[2]))
                    Tc_r.append(float(row[3]))
                except Exception:
                    pass
        has_r = len(t_r) > 0
    except Exception as e:
        print(f'[!] CSV error: {e}')
if has_r:
    print(f'    Real CSV: {len(t_r)} samples, t=[{t_r[0]:.1f}..{t_r[-1]:.1f}] min')

xL_m = [t/60 for t in [240, 2040, 2940, 4740, 5640]]

def add_phase_bands(ax, y_text=None, fontsize=10):
    rest_intervals = [(0, 240), (2040, 2940), (4740, 5640)]
    for t0, t1 in rest_intervals:
        ax.axvspan(t0/60, t1/60, alpha=0.07, color='gray', zorder=0)
    for xv in xL_m:
        ax.axvline(xv, color='#CCCCCC', lw=0.5, ls=':', zorder=1)
    if y_text is not None:
        phase_labels = [
            (0,    240,  True,  'STANDBY'),
            (240,  2040, False, 'SP1 = 22 °C'),
            (2040, 2940, True,  'REST 1'),
            (2940, 4740, False, 'SP2 = 20 °C'),
            (4740, 5640, True,  'REST 2'),
            (5640, 6600, False, 'SP3 = 18 °C'),
        ]
        for t0, t1, is_rest, nm in phase_labels:
            col = '#999999' if is_rest else '#222222'
            ax.text((t0+t1)/2/60, y_text, nm, ha='center', fontsize=fontsize,
                    color=col, style='italic' if is_rest else 'normal',
                    bbox=dict(boxstyle='round,pad=0.1', facecolor='white',
                              edgecolor='none', alpha=0.8))


# ═══════════════════════════════════════════════════════════════════
# FIGURE 2 – Validation results: Digital Twin vs Real Plant (English)
# ═══════════════════════════════════════════════════════════════════
fig6, ax6 = plt.subplots(figsize=(4.56, 2.5))
fig6.patch.set_facecolor('white')

add_phase_bands(ax6)  # phase bands without labels (caption describes them)
ax6.step(t_arr, sp_arr, where='post', color='k', lw=0.9, ls='--',
         label='Setpoint', zorder=3)
ax6.plot(t_arr, Tf_arr, '-', color='#2E86AB', lw=1.2,
         label='$T_c$ – Simulation')
ax6.plot(t_arr, Tc_arr, '-', color='#C0392B', lw=1.2,
         label='$T_h$ – Simulation')
if has_r:
    ax6.plot(t_r, Tf_r, '--', color='#27AE60', lw=1.0,
             label='$T_c$ – Real plant', alpha=0.9)
    ax6.plot(t_r, Tc_r, '--', color='#E67E22', lw=1.0,
             label='$T_h$ – Real plant', alpha=0.9)

# Setpoint labels — centred on each active phase, positioned below the dashed lines
ax6.text((240+2040)/2/60,  19.3, 'SP1 = 22 °C', fontsize=6, color='#2E86AB', ha='center')
ax6.text((2940+4740)/2/60, 17.3, 'SP2 = 20 °C', fontsize=6, color='#2E86AB', ha='center')
ax6.text((5640+6600)/2/60, 15.3, 'SP3 = 18 °C', fontsize=6, color='#2E86AB', ha='center')

ax6.set_xlabel('Time [min]', fontsize=9)
ax6.set_ylabel('Temperature [°C]', fontsize=9)
# title removed — redundant with caption
ax6.legend(loc='upper left', ncol=2, fontsize=6,
           handlelength=1.4, handletextpad=0.3, borderpad=0.3,
           labelspacing=0.15, borderaxespad=0.3)
ax6.set_ylim(13, 48); ax6.grid(True, alpha=0.3)
ax6.set_xlim(0, N_SIM/60)
ax6.set_xticks([t/60 for t in [0, 240, 2040, 2940, 4740, 5640, 6600]])
ax6.set_xticklabels(['0', '4', '34', '49', '79', '94', '110'], fontsize=7)
ax6.tick_params(axis='both', which='major', labelsize=7)

plt.tight_layout()
plt.savefig(_os.path.join(_FIGURES, 'fig_risultati_sim.png'),
            dpi=300, bbox_inches='tight', pad_inches=0.010, facecolor='white')
plt.close(fig6)
print('[OK] figures/fig_risultati_sim.png')

print('\nDone.')
