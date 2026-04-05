"""
Tema A - Evitare cu recuperare (mașină de stări).
IA Lab #06 - Inteligență Artificială 2025-2026

Mașina de stări:
  FORWARD  → merge drept înainte; dacă obstacol frontal < STOP_DISTANCE → BACKWARD
  BACKWARD → dă înapoi T_BACK secunde → TURNING
  TURNING  → virează aleatoriu stânga sau dreapta ~90° → FORWARD
"""
import time
import random
from enum import Enum
from coppeliasim_zmqremoteapi_client import RemoteAPIClient

# --- Parametri ---
V_FORWARD     = 2.0    # rad/s - viteza inainte
V_BACK        = -1.5   # rad/s - viteza inapoi
V_TURN        = 2.0    # rad/s - viteza viraj
STOP_DISTANCE = 0.45   # metri - prag oprire obstacol frontal
T_BACK        = 1.0    # secunde - durata mers inapoi
T_TURN        = 1.6    # secunde - durata viraj ~90 grade
FRONT_SENSORS = [2, 3, 4, 5]  # senzori frontali
SENSOR_MAX    = 1.0    # metri


class RobotState(Enum):
    """Starile posibile ale robotului."""
    FORWARD  = "FORWARD"
    BACKWARD = "BACKWARD"
    TURNING  = "TURNING"


def get_min_front_distance(sim, sensors):
    """Returneaza distanta minima detectata de senzorii frontali."""
    min_dist = SENSOR_MAX
    for idx in FRONT_SENSORS:
        result, dist, *_ = sim.readProximitySensor(sensors[idx])
        if result and dist < min_dist:
            min_dist = dist
    return min_dist


def set_velocity(sim, left_motor, right_motor, v_left, v_right):
    sim.setJointTargetVelocity(left_motor,  v_left)
    sim.setJointTargetVelocity(right_motor, v_right)


def next_state(current_state, dist_front):
    """
    Calculeaza starea urmatoare pe baza starii curente si a distantei frontale.

    Args:
        current_state: starea curenta (RobotState).
        dist_front: distanta minima frontala (float, metri).

    Returns:
        RobotState: noua stare (poate fi identica cu cea curenta).
    """
    if current_state == RobotState.FORWARD and dist_front < STOP_DISTANCE:
        return RobotState.BACKWARD
    return current_state


def main():
    client = RemoteAPIClient()
    sim = client.require('sim')

    left_motor  = sim.getObject('/PioneerP3DX/leftMotor')
    right_motor = sim.getObject('/PioneerP3DX/rightMotor')
    sensors     = [sim.getObject(f'/PioneerP3DX/ultrasonicSensor[{i}]') for i in range(16)]

    sim.startSimulation()
    print("Tema A - Masina de stari cu recuperare. Ctrl+C pentru oprire.\n")

    state = RobotState.FORWARD
    state_start = time.time()
    turn_dir = 'stanga'  # directia de viraj aleasa la recuperare

    try:
        while True:
            dist_front = get_min_front_distance(sim, sensors)
            now = time.time()
            elapsed = now - state_start

            if state == RobotState.FORWARD:
                new_state = next_state(state, dist_front)
                if new_state != state:
                    state = new_state
                    state_start = now
                    print(f"\n[{state.value}] Obstacol la {dist_front:.3f} m - dau inapoi")
                else:
                    set_velocity(sim, left_motor, right_motor, V_FORWARD, V_FORWARD)
                    print(f"[{state.value}] Distanta frontala: {dist_front:.3f} m", end='\r')

            elif state == RobotState.BACKWARD:
                set_velocity(sim, left_motor, right_motor, V_BACK, V_BACK)
                if elapsed >= T_BACK:
                    turn_dir = random.choice(['stanga', 'dreapta'])
                    state = RobotState.TURNING
                    state_start = now
                    print(f"\n[{state.value}] Viraj {turn_dir} ~90 grade")

            elif state == RobotState.TURNING:
                if turn_dir == 'stanga':
                    set_velocity(sim, left_motor, right_motor, -V_TURN, +V_TURN)
                else:
                    set_velocity(sim, left_motor, right_motor, +V_TURN, -V_TURN)

                if elapsed >= T_TURN:
                    state = RobotState.FORWARD
                    state_start = now
                    print(f"[{state.value}] Reluare mers inainte")

            time.sleep(0.05)  # 20 Hz

    except KeyboardInterrupt:
        print("\nOprire manuala.")
    finally:
        set_velocity(sim, left_motor, right_motor, 0.0, 0.0)
        sim.stopSimulation()
        print("Simulare oprita.")


if __name__ == '__main__':
    main()
