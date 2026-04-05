"""
Tema D (Bonus) - Vehicul Braitenberg tip "Iubire".
IA Lab #06 - Inteligenta Artificiala 2025-2026

Vehiculul "Iubire" foloseste conexiuni ipsilaterale INHIBITORII:
  - Senzorul stang-fata REDUCE viteza motorului stang.
  - Senzorul drept-fata REDUCE viteza motorului drept.

Efect emergent:
  - Cand robotul nu detecteaza obstacole, merge drept inainte cu V_BASE.
  - Cand un obstacol apare la stanga, motorul stang incetineste → robotul
    vireaza SPRE obstacol (la stanga) - comportament de "atractie".
  - Cand ajunge aproape, AMBELE motoare incetinesc → robotul se opreste calm,
    "infascat" de sursa de stimul - asemanator atractiei magnetice ("iubire").

Comparatie cu "Frica" (cerinta 3.5):
  "Frica"  : conexiuni ipsilaterale EXCITATOARE → robot FUGE de obstacol.
  "Iubire" : conexiuni ipsilaterale INHIBITORII → robot SE APROPIE si se OPRESTE.

Referinta: Braitenberg, V. (1984). Vehicles: Experiments in Synthetic Psychology.
           MIT Press. Vehiculul nr. 3b ("Love").
"""
import time
from coppeliasim_zmqremoteapi_client import RemoteAPIClient

# --- Parametri ---
V_BASE     = 3.0    # rad/s - viteza de baza (fara obstacole)
V_MAX      = 5.0    # rad/s - viteza maxima
K_SENSOR   = 3.0    # factor de amplificare (mai mic decat "Frica" - oporit lent)
SENSOR_MAX = 1.0    # m

# Ponderile senzorilor pentru "Iubire":
# Conexiuni ipsilaterale INHIBITORII (semn negativ):
#   senzorul stang reduce motorul stang → robotul vireaza SPRE obstacol stang
#   senzorul drept reduce motorul drept → robotul vireaza SPRE obstacol drept
#
# Compara cu "Frica" (cerinta 3.5) unde ponderile sunt pozitive si robotul fuge:
#   "Frica":  S_stang → +w_stang (excitatie) → vireaza DREAPTA (fuga)
#   "Iubire": S_stang → -w_stang (inhibitie)  → vireaza STANGA  (atractie)
#
# Format: (w_motor_stang, w_motor_drept)
WEIGHTS_LOVE = [
    (-0.5, +0.0),   # S0  fata-stanga-ext   → inhiba stanga, neutral dreapta → vireaza stanga
    (-1.0, +0.0),   # S1  fata-stanga
    (-1.5, +0.0),   # S2  fata-centru-st
    (-2.0, +0.0),   # S3  fata-centru-st
    (+0.0, -2.0),   # S4  fata-centru-dr    → neutral stanga, inhiba dreapta → vireaza dreapta
    (+0.0, -1.5),   # S5  fata-centru-dr
    (+0.0, -1.0),   # S6  fata-dreapta
    (+0.0, -0.5),   # S7  fata-dreapta-ext
]

# Ponderile "Frica" (pentru comparatie - afisate la start)
WEIGHTS_FEAR = [
    (+0.5, -0.5),
    (+1.0, -1.0),
    (+1.5, -1.5),
    (+2.0, -2.0),
    (-2.0, +2.0),
    (-1.5, +1.5),
    (-1.0, +1.0),
    (-0.5, +0.5),
]


def compute_velocities(sim, sensors, weights):
    """
    Calculeaza vitezele motorului pe baza ponderilor Braitenberg.

    Args:
        sim: API CoppeliaSim.
        sensors: lista de handle-uri senzori.
        weights: lista de (w_left, w_right) pentru fiecare senzor.

    Returns:
        tuple (v_left, v_right) in rad/s.
    """
    v_left  = V_BASE
    v_right = V_BASE

    for i, (w_l, w_r) in enumerate(weights):
        result, distance, *_ = sim.readProximitySensor(sensors[i])
        if result:
            proximity = max(0.0, min(1.0, 1.0 - distance / SENSOR_MAX))
            v_left  += K_SENSOR * w_l * proximity
            v_right += K_SENSOR * w_r * proximity

    v_left  = max(-V_MAX, min(V_MAX, v_left))
    v_right = max(-V_MAX, min(V_MAX, v_right))

    return v_left, v_right


def main():
    client = RemoteAPIClient()
    sim = client.require('sim')

    left_motor  = sim.getObject('/PioneerP3DX/leftMotor')
    right_motor = sim.getObject('/PioneerP3DX/rightMotor')
    sensors     = [sim.getObject(f'/PioneerP3DX/ultrasonicSensor[{i}]') for i in range(16)]

    print("=" * 60)
    print("Vehicul Braitenberg - TIP 'IUBIRE' (Love)")
    print("=" * 60)
    print()
    print("Conexiuni INHIBITORII ipsilaterale:")
    print("  Obstacol la STANGA → motorul stang incetineste")
    print("                      → robotul vireaza SPRE obstacol")
    print("  Aproape de obstacol → ambele motoare incetinesc → OPRIRE")
    print()
    print("Diferenta fata de 'FRICA' (cerinta 3.5):")
    print("  'Frica'  → fuge de obstacol (pondere POZITIVA)")
    print("  'Iubire' → se apropie si se opreste (pondere NEGATIVA)")
    print()
    print("Plasati un obiect in fata robotului si observati comportamentul!")
    print("Ctrl+C pentru oprire.\n")

    sim.startSimulation()
    iteration = 0

    try:
        while True:
            v_left, v_right = compute_velocities(sim, sensors, WEIGHTS_LOVE)

            sim.setJointTargetVelocity(left_motor,  v_left)
            sim.setJointTargetVelocity(right_motor, v_right)

            # Clasificare stare pentru afisare
            if abs(v_left) < 0.3 and abs(v_right) < 0.3:
                stare = "OPRIT (aproape de tinta)"
            elif abs(v_left - v_right) < 0.2:
                stare = "mers inainte"
            elif v_left < v_right:
                stare = "vireaza STANGA (atras la stanga)"
            else:
                stare = "vireaza DREAPTA (atras la dreapta)"

            if iteration % 20 == 0:
                print(f"vS={v_left:+.2f} rad/s  |  vD={v_right:+.2f} rad/s  |  {stare}")

            iteration += 1
            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\nOprire vehicul Braitenberg 'Iubire'.")
    finally:
        sim.setJointTargetVelocity(left_motor,  0.0)
        sim.setJointTargetVelocity(right_motor, 0.0)
        sim.stopSimulation()
        print("Simulare oprita.")


if __name__ == '__main__':
    main()
