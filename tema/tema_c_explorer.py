"""
Tema C - Robot Explorer: explorare autonoma a arenei (nivel avansat).

Combina wall-following (cerinta 3.6) cu recuperare la blocaj (Tema A).
Robotul exploreaza o arena dreptunghiulara cu obstacole minim 60 secunde.

Arhitectura comportamentala:
  Prioritate 1 (maxima): RECOVERY  - daca e blocat prea mult timp in acelasi loc
  Prioritate 2:          AVOID     - obstacol frontal foarte aproape (< FRONT_STOP)
  Prioritate 3:          WALL_FOLLOW - urmarire perete drept
  Prioritate 4 (minima): EXPLORE   - explorare libera (fara perete)

Traiectoria (X, Y) este salvata in tema/log_explorer.csv si graficata la final.
"""
import time
import random
import csv
import os
from enum import Enum
from coppeliasim_zmqremoteapi_client import RemoteAPIClient

# --- Parametri ---
V_BASE       = 2.0    # rad/s
V_MAX        = 3.5    # rad/s
V_TURN       = 2.0    # rad/s
TARGET_DIST  = 0.4    # m - distanta tinta perete drept
K_P          = 3.0    # coeficient P-controller
FRONT_STOP   = 0.35   # m - prag obstacol frontal urgent
FRONT_CAUTION = 0.6   # m - prag detectie obstacol moderat
SENSOR_MAX   = 1.0    # m

RIGHT_SENSORS = [8, 9]
FRONT_SENSORS = [2, 3, 4, 5]

T_BACK        = 0.8   # s - durata mers inapoi la recuperare
T_TURN_RECOV  = 1.5   # s - durata viraj la recuperare
STUCK_TIME    = 3.0   # s - timp maxim fara progres inainte de recuperare
STUCK_DIST    = 0.05  # m - distanta minima de progres in STUCK_TIME secunde

TOTAL_DURATION = 75.0  # secunde - durata totala explorare
LOG_FILE = os.path.join(os.path.dirname(__file__), 'log_explorer.csv')


class ExplorerState(Enum):
    EXPLORE     = "EXPLORE"
    WALL_FOLLOW = "WALL_FOLLOW"
    AVOID       = "AVOID"
    BACKWARD    = "BACKWARD"
    TURN_RECOV  = "TURN_RECOV"


def read_min_dist(sim, sensors, indices):
    min_dist = SENSOR_MAX
    for idx in indices:
        result, dist, *_ = sim.readProximitySensor(sensors[idx])
        if result and dist < min_dist:
            min_dist = dist
    return min_dist


def set_velocity(sim, lm, rm, vl, vr):
    sim.setJointTargetVelocity(lm, vl)
    sim.setJointTargetVelocity(rm, vr)


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def main():
    client = RemoteAPIClient()
    sim = client.require('sim')

    robot       = sim.getObject('/PioneerP3DX')
    left_motor  = sim.getObject('/PioneerP3DX/leftMotor')
    right_motor = sim.getObject('/PioneerP3DX/rightMotor')
    sensors     = [sim.getObject(f'/PioneerP3DX/ultrasonicSensor[{i}]') for i in range(16)]

    sim.startSimulation()
    t0 = time.time()

    print(f"Tema C - Robot Explorer pornit. Durata: {TOTAL_DURATION}s. Ctrl+C pt oprire.\n")

    state       = ExplorerState.EXPLORE
    state_start = t0
    turn_dir    = 'stanga'

    # Monitorizare blocaj
    last_pos     = sim.getObjectPosition(robot, sim.handle_world)
    last_prog_t  = t0

    trajectory = []  # lista de (timestamp, pos_x, pos_y)

    try:
        while True:
            now     = time.time()
            elapsed = now - state_start
            total   = now - t0

            if total >= TOTAL_DURATION:
                print(f"\nDurata de {TOTAL_DURATION}s atinsa. Oprire.")
                break

            pos         = sim.getObjectPosition(robot, sim.handle_world)
            dist_front  = read_min_dist(sim, sensors, FRONT_SENSORS)
            dist_right  = read_min_dist(sim, sensors, RIGHT_SENSORS)

            # Inregistrare traiectorie
            trajectory.append((round(total, 3), round(pos[0], 4), round(pos[1], 4)))

            # --- Detectie blocaj ---
            dx = pos[0] - last_pos[0]
            dy = pos[1] - last_pos[1]
            progress = (dx**2 + dy**2) ** 0.5

            if progress > STUCK_DIST:
                last_pos    = pos
                last_prog_t = now

            stuck = (now - last_prog_t) > STUCK_TIME and state not in (
                ExplorerState.BACKWARD, ExplorerState.TURN_RECOV
            )

            # --- Masina de stari ---
            if stuck:
                state       = ExplorerState.BACKWARD
                state_start = now
                turn_dir    = random.choice(['stanga', 'dreapta'])
                last_prog_t = now
                print(f"\n[STUCK -> BACKWARD] {total:.1f}s")

            elif state == ExplorerState.EXPLORE:
                if dist_front < FRONT_STOP:
                    state, state_start = ExplorerState.AVOID, now
                elif dist_right < SENSOR_MAX * 0.95:
                    state, state_start = ExplorerState.WALL_FOLLOW, now
                else:
                    set_velocity(sim, left_motor, right_motor, V_BASE, V_BASE * 0.85)

            elif state == ExplorerState.WALL_FOLLOW:
                if dist_front < FRONT_STOP:
                    state, state_start = ExplorerState.AVOID, now
                elif dist_right >= SENSOR_MAX * 0.95:
                    state, state_start = ExplorerState.EXPLORE, now
                else:
                    error   = dist_right - TARGET_DIST
                    v_left  = clamp(V_BASE + K_P * error, -V_MAX, V_MAX)
                    v_right = clamp(V_BASE - K_P * error, -V_MAX, V_MAX)
                    set_velocity(sim, left_motor, right_motor, v_left, v_right)

            elif state == ExplorerState.AVOID:
                # Viraj la stanga pentru a ocoli obstacolul frontal
                set_velocity(sim, left_motor, right_motor, -V_TURN, +V_TURN)
                if dist_front >= FRONT_CAUTION:
                    state, state_start = ExplorerState.EXPLORE, now

            elif state == ExplorerState.BACKWARD:
                set_velocity(sim, left_motor, right_motor, -V_BASE, -V_BASE)
                if elapsed >= T_BACK:
                    state, state_start = ExplorerState.TURN_RECOV, now

            elif state == ExplorerState.TURN_RECOV:
                if turn_dir == 'stanga':
                    set_velocity(sim, left_motor, right_motor, -V_TURN, +V_TURN)
                else:
                    set_velocity(sim, left_motor, right_motor, +V_TURN, -V_TURN)
                if elapsed >= T_TURN_RECOV:
                    state, state_start = ExplorerState.EXPLORE, now
                    print(f"[EXPLORE] Reluare explorare {total:.1f}s")

            print(f"[{state.value:<12}] t={total:5.1f}s  front={dist_front:.3f}m  "
                  f"right={dist_right:.3f}m  pos=({pos[0]:.2f},{pos[1]:.2f})", end='\r')

            time.sleep(0.05)  # 20 Hz

    except KeyboardInterrupt:
        print("\nOprire manuala.")
    finally:
        set_velocity(sim, left_motor, right_motor, 0.0, 0.0)
        sim.stopSimulation()

        # Salvare traiectorie
        with open(LOG_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'pos_x', 'pos_y'])
            writer.writerows(trajectory)
        print(f"\nTraiectorie salvata in {LOG_FILE} ({len(trajectory)} puncte).")

        # Generare grafic traiectorie
        try:
            import matplotlib.pyplot as plt
            import numpy as np

            ts = np.array([r[0] for r in trajectory])
            xs = np.array([r[1] for r in trajectory])
            ys = np.array([r[2] for r in trajectory])
            t_norm = (ts - ts.min()) / (ts.max() - ts.min() + 1e-9)

            fig, ax = plt.subplots(figsize=(8, 8))
            for i in range(len(xs) - 1):
                ax.plot(xs[i:i+2], ys[i:i+2],
                        color=plt.cm.viridis(t_norm[i]), linewidth=1.5)
            ax.plot(xs[0],  ys[0],  'go', markersize=10, label='Start')
            ax.plot(xs[-1], ys[-1], 'rs', markersize=10, label='Stop')

            sm = plt.cm.ScalarMappable(cmap='viridis',
                                        norm=plt.Normalize(ts.min(), ts.max()))
            sm.set_array([])
            plt.colorbar(sm, ax=ax, label='Timp (s)')

            ax.set_xlabel('X (m)')
            ax.set_ylabel('Y (m)')
            ax.set_title(f'Traiectoria Explorer ({ts.max():.0f}s)')
            ax.legend()
            ax.set_aspect('equal')
            ax.grid(True, linestyle='--', alpha=0.5)

            out = os.path.join(os.path.dirname(__file__), 'grafic_explorer_traiectorie.png')
            fig.savefig(out, dpi=150, bbox_inches='tight')
            plt.close(fig)
            print(f"Grafic salvat: {out}")
        except ImportError:
            print("Matplotlib nu este instalat - graficul nu a putut fi generat.")

        print("Simulare oprita.")


if __name__ == '__main__':
    main()
