"""
Tema B - Braitenberg cu inregistrare de date (logging).

Ruleaza vehiculul Braitenberg (evitare) si salveaza la fiecare iteratie:
  timestamp, v_left, v_right, s0..s7, pos_x, pos_y
intr-un fisier CSV: tema/log_braitenberg.csv

Dupa Ctrl+C, ruleaza tema_b_grafice.py pentru a genera graficele.
"""
import time
import csv
import os
from coppeliasim_zmqremoteapi_client import RemoteAPIClient

# --- Parametri Braitenberg ---
V_BASE     = 3.0
V_MAX      = 6.0
K_SENSOR   = 6.0
SENSOR_MAX = 1.0

WEIGHTS = [
    (+0.5, -0.5),
    (+1.0, -1.0),
    (+1.5, -1.5),
    (+2.0, -2.0),
    (-2.0, +2.0),
    (-1.5, +1.5),
    (-1.0, +1.0),
    (-0.5, +0.5),
]

LOG_FILE = os.path.join(os.path.dirname(__file__), 'log_braitenberg.csv')
CSV_HEADER = ['timestamp', 'v_left', 'v_right',
              's0', 's1', 's2', 's3', 's4', 's5', 's6', 's7',
              'pos_x', 'pos_y']


def braitenberg_step(sim, sensors):
    """
    Calculeaza vitezele Braitenberg si returneaza si valorile normalizate ale senzorilor.

    Returns:
        tuple: (v_left, v_right, [s0..s7])
    """
    v_left  = V_BASE
    v_right = V_BASE
    sensor_vals = []

    for i, (w_l, w_r) in enumerate(WEIGHTS):
        result, distance, *_ = sim.readProximitySensor(sensors[i])
        if result:
            proximity = max(0.0, min(1.0, 1.0 - distance / SENSOR_MAX))
        else:
            proximity = 0.0
        sensor_vals.append(proximity)
        v_left  += K_SENSOR * w_l * proximity
        v_right += K_SENSOR * w_r * proximity

    v_left  = max(-V_MAX, min(V_MAX, v_left))
    v_right = max(-V_MAX, min(V_MAX, v_right))

    return v_left, v_right, sensor_vals


def main():
    client = RemoteAPIClient()
    sim = client.require('sim')

    robot       = sim.getObject('/PioneerP3DX')
    left_motor  = sim.getObject('/PioneerP3DX/leftMotor')
    right_motor = sim.getObject('/PioneerP3DX/rightMotor')
    sensors     = [sim.getObject(f'/PioneerP3DX/ultrasonicSensor[{i}]') for i in range(16)]

    sim.startSimulation()
    t0 = time.time()

    print(f"Tema B - Braitenberg cu logging. Date salvate in: {LOG_FILE}")
    print("Ctrl+C pentru oprire si generare grafice.\n")

    rows = []
    iteration = 0

    try:
        while True:
            v_left, v_right, sensor_vals = braitenberg_step(sim, sensors)

            sim.setJointTargetVelocity(left_motor,  v_left)
            sim.setJointTargetVelocity(right_motor, v_right)

            pos = sim.getObjectPosition(robot, sim.handle_world)
            ts  = time.time() - t0

            row = [round(ts, 4), round(v_left, 4), round(v_right, 4)]
            row += [round(s, 4) for s in sensor_vals]
            row += [round(pos[0], 4), round(pos[1], 4)]
            rows.append(row)

            if iteration % 20 == 0:
                print(f"t={ts:6.2f}s  vS={v_left:+.2f}  vD={v_right:+.2f}  "
                      f"pos=({pos[0]:.2f}, {pos[1]:.2f})")

            iteration += 1
            time.sleep(0.05)

    except KeyboardInterrupt:
        print(f"\nOprire. {len(rows)} randuri inregistrate.")
    finally:
        sim.setJointTargetVelocity(left_motor,  0.0)
        sim.setJointTargetVelocity(right_motor, 0.0)
        sim.stopSimulation()

        # Scriere CSV
        with open(LOG_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADER)
            writer.writerows(rows)
        print(f"Date salvate in {LOG_FILE}.")
        print("Ruleaza 'python tema_b_grafice.py' pentru grafice.")


if __name__ == '__main__':
    main()
