"""
Tema B - Generare grafice din datele CSV inregistrate de tema_b_logging.py.

Genereaza 3 imagini PNG:
  1. Traiectoria robotului in planul XY
  2. Vitezele v_left si v_right in functie de timp
  3. Heatmap activare senzori s0-s7 in timp
"""
import os
import csv
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np

LOG_FILE  = os.path.join(os.path.dirname(__file__), 'log_braitenberg.csv')
OUT_DIR   = os.path.dirname(__file__)


def load_csv(path):
    """Incarca datele din CSV si returneaza un dict cu coloane numpy array."""
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Fisierul '{path}' nu exista.\n"
            "Ruleaza mai intai 'python tema_b_logging.py' pentru a genera datele."
        )

    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        raise ValueError("Fisierul CSV este gol. Ruleaza tema_b_logging.py si lasa robotul sa se miste.")

    data = {}
    for key in rows[0]:
        data[key] = np.array([float(r[key]) for r in rows])
    return data


def plot_trajectory(data, out_dir):
    """Grafic 1: Traiectoria XY a robotului."""
    fig, ax = plt.subplots(figsize=(7, 7))

    # Coloreaza traiectoria dupa timp (gradient)
    x, y = data['pos_x'], data['pos_y']
    t    = data['timestamp']
    t_norm = (t - t.min()) / (t.max() - t.min() + 1e-9)

    for i in range(len(x) - 1):
        ax.plot(x[i:i+2], y[i:i+2],
                color=plt.cm.plasma(t_norm[i]), linewidth=1.5)

    # Marker start / stop
    ax.plot(x[0],  y[0],  'go', markersize=10, label='Start', zorder=5)
    ax.plot(x[-1], y[-1], 'rs', markersize=10, label='Stop',  zorder=5)

    # Colorbar
    sm = plt.cm.ScalarMappable(cmap='plasma',
                                norm=mcolors.Normalize(vmin=t.min(), vmax=t.max()))
    sm.set_array([])
    plt.colorbar(sm, ax=ax, label='Timp (s)')

    ax.set_xlabel('X (m)')
    ax.set_ylabel('Y (m)')
    ax.set_title('Traiectoria robotului Pioneer P3-DX\n(Braitenberg "Frica")')
    ax.legend()
    ax.set_aspect('equal')
    ax.grid(True, linestyle='--', alpha=0.5)

    path = os.path.join(out_dir, 'grafic_1_traiectorie.png')
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  Salvat: {path}")


def plot_velocities(data, out_dir):
    """Grafic 2: v_left si v_right in functie de timp."""
    fig, ax = plt.subplots(figsize=(10, 4))

    t = data['timestamp']
    ax.plot(t, data['v_left'],  label='v_stang (rad/s)',  color='tab:blue',   linewidth=1.2)
    ax.plot(t, data['v_right'], label='v_drept (rad/s)',  color='tab:orange', linewidth=1.2)

    ax.set_xlabel('Timp (s)')
    ax.set_ylabel('Viteza (rad/s)')
    ax.set_title('Vitezele motoarelor in timp\n(Braitenberg "Frica")')
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.axhline(0, color='black', linewidth=0.8, linestyle=':')

    path = os.path.join(out_dir, 'grafic_2_viteze.png')
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  Salvat: {path}")


def plot_sensor_heatmap(data, out_dir):
    """Grafic 3: Heatmap activare senzori s0-s7 in timp."""
    sensor_keys = [f's{i}' for i in range(8)]
    matrix = np.array([data[k] for k in sensor_keys])  # shape (8, N)

    t = data['timestamp']

    fig, ax = plt.subplots(figsize=(12, 4))
    im = ax.imshow(
        matrix,
        aspect='auto',
        origin='lower',
        extent=[t.min(), t.max(), -0.5, 7.5],
        cmap='YlOrRd',
        vmin=0.0,
        vmax=1.0
    )
    plt.colorbar(im, ax=ax, label='Proximitate normalizata')

    ax.set_yticks(range(8))
    ax.set_yticklabels([
        'S0 fata-stg-ext', 'S1 fata-stg', 'S2 fata-ctr-st', 'S3 fata-ctr-st',
        'S4 fata-ctr-dr', 'S5 fata-ctr-dr', 'S6 fata-dr', 'S7 fata-dr-ext'
    ], fontsize=8)
    ax.set_xlabel('Timp (s)')
    ax.set_title('Heatmap activare senzori frontali (s0-s7) in timp\n(Braitenberg "Frica")')
    ax.grid(False)

    path = os.path.join(out_dir, 'grafic_3_heatmap_senzori.png')
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  Salvat: {path}")


def main():
    print(f"Incarcare date din: {LOG_FILE}")
    data = load_csv(LOG_FILE)
    n = len(data['timestamp'])
    print(f"  {n} esantioane incarcate (durata: {data['timestamp'][-1]:.1f}s)\n")

    print("Generare grafice...")
    plot_trajectory(data, OUT_DIR)
    plot_velocities(data, OUT_DIR)
    plot_sensor_heatmap(data, OUT_DIR)

    print("\nToate graficele au fost generate in directorul tema/.")


if __name__ == '__main__':
    main()
