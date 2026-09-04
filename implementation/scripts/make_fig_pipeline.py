"""
Figure V3 per il paper LNEE Peltier — versione leggibile, 8 pagine.

STRATEGIA DEFINITIVA:
  Stesso figsize del paper 8-page precedente → stessa display height → 8 pagine.
  figW = larghezza di stampa effettiva → fontsize=X pt nel paper.
  Tutti i box ENTRO ylim [0,H] → nessun clipping → testo e box completamente visibili.

  Pipeline:  figsize=(4.56, 0.80 in)  @0.95\\textwidth → display 2.03 cm
  Artifact:  figsize=(3.84, 1.40 in)  @0.80\\textwidth → display 3.56 cm

  Con figW = print-width:
    fontsize=9   → 9 pt nel paper    (comps pipeline, repo header)
    fontsize=8.5 → 8.5 pt nel paper  (component labels)
    fontsize=7.5 → 7.5 pt nel paper  (purpose labels)
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'figures')
os.makedirs(OUT, exist_ok=True)
DPI = 300

C = {
    'blue':   '#AED6F1',
    'green':  '#A9DFBF',
    'orange': '#FAD7A0',
    'yellow': '#F9E79F',
    'purple': '#D2B4DE',
    'red':    '#F1948A',
    'grey':   '#BFC9CA',
    'repo':   '#D5E8D4',
}


# ─────────────────────────────────────────────────────────────────────────────
#  Fig. 1 – CPS Pipeline Overview
#  figsize=(4.56, 0.80 in) → display 2.03 cm   @0.95\textwidth
#  bh=0.72 in  (< H=0.80: margins 0.04 in top+bottom → nessun clipping)
#  fontsize=9 → 9 pt nel paper
# ─────────────────────────────────────────────────────────────────────────────
def make_pipeline():
    W, H = 4.58, 0.90
    fig, ax = plt.subplots(figsize=(W, H))
    ax.set_xlim(0, W)
    ax.set_ylim(0, H)
    ax.axis('off')
    fig.patch.set_facecolor('white')

    stages = [
        ("Physical\nBench",    C['blue']),
        ("Sensors &\nActuator", C['green']),
        ("Embedded\nFirmware",  C['orange']),
        ("Telemetry\n& Logs",   C['yellow']),
        ("Digital\nTwin",       C['purple']),
        ("UPPAAL\nModel",       C['red']),
        ("Artifact\nRepo",      C['grey']),
    ]

    n      = len(stages)
    margin = 0.04
    arr_w  = 0.150
    bw     = (W - 2*margin - (n-1)*arr_w) / n    # ~0.582 in
    bh     = 0.46     # fontsize=7 → testo 0.225", padding 0.16" per lato
    cy     = H / 2    # 0.40

    for i, (label, color) in enumerate(stages):
        x = margin + i * (bw + arr_w)
        ax.add_patch(FancyBboxPatch(
            (x, cy - bh/2), bw, bh,
            boxstyle="round,pad=0.020",
            facecolor=color, edgecolor='#333', linewidth=0.7))
        ax.text(x + bw/2, cy, label,
                ha='center', va='center',
                fontsize=7, fontweight='bold', color='#111',
                linespacing=1.30)
        if i < n - 1:
            ax.annotate('', xy=(x + bw + arr_w, cy), xytext=(x + bw, cy),
                        arrowprops=dict(arrowstyle='->', color='#333',
                                        lw=0.9, mutation_scale=8))

    # co-design link: embedded firmware <-> UPPAAL formal model
    x_fw   = margin + 2 * (bw + arr_w) + bw / 2
    x_upp  = margin + 5 * (bw + arr_w) + bw / 2
    y_box  = cy - bh / 2
    rad = 0.17
    ax.add_patch(FancyArrowPatch(
        (x_fw, y_box), (x_upp, y_box),
        connectionstyle=f"arc3,rad={rad}", arrowstyle='<->',
        mutation_scale=8, lw=0.9, color='#C0392B',
        linestyle=(0, (2.2, 1.6)), shrinkA=1.0, shrinkB=1.0, zorder=5))
    ax.text((x_fw + x_upp) / 2, y_box - rad * (x_upp - x_fw) / 2,
            'co-design', ha='center', va='center', fontsize=6,
            style='italic', color='#C0392B', zorder=6,
            bbox=dict(boxstyle='square,pad=0.15', facecolor='white',
                      edgecolor='none'))

    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    path = os.path.join(OUT, 'fig_pipeline_cps.png')
    plt.savefig(path, dpi=DPI, bbox_inches='tight', pad_inches=0.010,
                facecolor='white')
    plt.close()
    print(f"Saved  {path}")


# ─────────────────────────────────────────────────────────────────────────────
#  Fig. 3 – Artifact Structure + Reproduction Workflow
#  figsize=(3.84, 1.40 in) → display 3.56 cm   @0.80\textwidth
#  3 righe completamente entro ylim [0, 1.40]:
#    purpose:  y=0.040 … 0.390  (ph=0.35)
#    frecce:   0.390 … 0.470  (gap 0.08)
#    comp:     y=0.470 … 0.940  (ch=0.47, ccy=0.705)
#    frecce:   0.940 … 1.010  (gap 0.07)
#    repo:     y=1.010 … 1.230  (rh=0.22)
# ─────────────────────────────────────────────────────────────────────────────
def make_artifact_workflow():
    W, H = 3.84, 1.40
    fig, ax = plt.subplots(figsize=(W, H))
    ax.set_xlim(0, W)
    ax.set_ylim(0, H)
    ax.axis('off')
    fig.patch.set_facecolor('white')

    margin = 0.05
    n      = 6
    gap    = 0.04
    cw     = (W - 2*margin - (n-1)*gap) / n    # ~0.573 in

    # posizioni (dal basso, tutte entro [0, 1.40])
    ph   = 0.35;  pcy = 0.04 + ph/2           # pcy = 0.215
    ch   = 0.47;  ccy = 0.470 + ch/2          # ccy = 0.705
    rh   = 0.22;  rhy = 1.010                 # repo bordo inferiore

    # ── Repository header ─────────────────────────────────────────────────
    ax.add_patch(FancyBboxPatch(
        (margin, rhy), W - 2*margin, rh,
        boxstyle="round,pad=0.030",
        facecolor=C['repo'], edgecolor='#2E7D32', linewidth=1.1))
    ax.text(W/2, rhy + rh/2,
            'Open-Source Repository  (GitHub)',
            ha='center', va='center',
            fontsize=8, fontweight='bold', color='#111')

    # ── Component boxes ───────────────────────────────────────────────────
    comps = [
        ("Hardware",      C['blue']),
        ("Firmware",      C['orange']),
        ("Digital\nTwin", C['purple']),
        ("Formal\nModel", C['red']),
        ("Dataset",       C['yellow']),
        ("Scripts",       C['green']),
    ]

    for i, (name, color) in enumerate(comps):
        x = margin + i * (cw + gap)
        ax.add_patch(FancyBboxPatch(
            (x, ccy - ch/2), cw, ch,
            boxstyle="round,pad=0.020",
            facecolor=color, edgecolor='#444', linewidth=0.7))
        ax.text(x + cw/2, ccy, name,
                ha='center', va='center',
                fontsize=7.5, fontweight='bold', color='#111',
                linespacing=1.25)
        # freccia: dal bordo inferiore del repo → bordo superiore del comp
        ax.annotate('', xy=(x + cw/2, ccy + ch/2),
                    xytext=(x + cw/2, rhy),
                    arrowprops=dict(arrowstyle='->', color='#555',
                                    lw=0.6, mutation_scale=7))

    # ── Purpose boxes ─────────────────────────────────────────────────────
    purposes = [
        ("Rebuild\nbenchmark",  C['blue']),
        ("Run PID\n& FSM",      C['orange']),
        ("Simulate\nplant",     C['purple']),
        ("Verify\nsafety",      C['red']),
        ("Reproduce\nmetrics",  C['yellow']),
        ("Recompute\nfigures",  C['green']),
    ]

    for i, (lbl, color) in enumerate(purposes):
        x = margin + i * (cw + gap)
        ax.add_patch(FancyBboxPatch(
            (x, pcy - ph/2), cw, ph,
            boxstyle="round,pad=0.020",
            facecolor=color, edgecolor='#444', linewidth=0.6, alpha=0.82))
        ax.text(x + cw/2, pcy, lbl,
                ha='center', va='center',
                fontsize=6.5, color='#111', linespacing=1.25)
        # freccia: dal bordo inferiore del comp → bordo superiore del purpose
        ax.annotate('', xy=(x + cw/2, pcy + ph/2),
                    xytext=(x + cw/2, ccy - ch/2),
                    arrowprops=dict(arrowstyle='->', color='#555',
                                    lw=0.6, mutation_scale=7))

    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    path = os.path.join(OUT, 'fig_artifact_workflow.png')
    plt.savefig(path, dpi=DPI, bbox_inches='tight', pad_inches=0.010,
                facecolor='white')
    plt.close()
    print(f"Saved  {path}")


if __name__ == '__main__':
    make_pipeline()
    make_artifact_workflow()
    print("Done.")
