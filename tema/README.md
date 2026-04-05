# Tema Lab #06 - Comportamente reactive Pioneer P3-DX

## Tema A - Evitare cu recuperare (`tema_a_recuperare.py`)

**Comportament implementat:** masina de stari cu 3 stari - FORWARD, BACKWARD, TURNING.

**Rulare:**
```bash
python tema/tema_a_recuperare.py
```

**Stari:**
- `FORWARD`: robotul merge drept; daca detecteaza obstacol frontal < 0.45 m trece in BACKWARD.
- `BACKWARD`: da inapoi 1 secunda, apoi alege aleatoriu stanga/dreapta si trece in TURNING.
- `TURNING`: vireaza ~90 grade (1.6s), apoi revine in FORWARD.

**Observatii:** robotul nu se blocheaza permanent. Virajul aleatoriu evita ciclurile repetitive.

---

## Tema B - Braitenberg cu inregistrare de date (`tema_b_logging.py` + `tema_b_grafice.py`)

**Rulare in 2 pasi:**
```bash
# Pasul 1: inregistreaza date (se ruleaza 30-60s, apoi Ctrl+C)
python tema/tema_b_logging.py

# Pasul 2: genereaza graficele din CSV
python tema/tema_b_grafice.py
```

**Date inregistrate:** `tema/log_braitenberg.csv` cu coloanele:
`timestamp, v_left, v_right, s0..s7, pos_x, pos_y`

**Grafice generate:**
1. `grafic_1_traiectorie.png` - traiectoria XY colorata dupa timp
2. `grafic_2_viteze.png` - v_left si v_right in functie de timp
3. `grafic_3_heatmap_senzori.png` - heatmap activare senzori s0-s7 in timp

**Observatii:** vitezele oscileaza puternic la detectia obstacolelor; heatmap-ul
arata ca senzorii 2-5 (frontali centrali) se activeaza cel mai frecvent.

---

## Tema C - Robot Explorer (`tema_c_explorer.py`)

**Rulare:**
```bash
python tema/tema_c_explorer.py
```

**Arhitectura:** prioritati comportamentale (subsumption-like):
1. **RECOVERY** (prioritate maxima): detectat blocaj > 3s -> da inapoi + vireaza aleatoriu
2. **AVOID**: obstacol frontal < 0.35 m -> viraj stanga pe loc
3. **WALL_FOLLOW**: perete la dreapta detectat -> P-controller (K_P=3.0, target=0.4m)
4. **EXPLORE** (prioritate minima): merge inainte cu viraj usor la dreapta (cauta perete)

**Date generate:** `tema/log_explorer.csv` si `tema/grafic_explorer_traiectorie.png`

**Parametri cheie:**
- `TARGET_DIST = 0.4 m` - distanta tinta fata de peretele drept
- `K_P = 3.0` - reactivitate P-controller (testat intre 2.0-5.0)
- `STUCK_TIME = 3.0 s` - timp de inactivitate inainte de declansarea recuperarii

**Observatii:** robotul exploreaza continuu; K_P < 2.0 da oscilatie lenta,
K_P > 6.0 da oscilatie rapida (instabilitate). Valoarea 3.0 ofera comportament fluid.

---

## Tema D - Braitenberg "Iubire" Bonus (`tema_d_bonus_iubire.py`)

**Rulare:**
```bash
python tema/tema_d_bonus_iubire.py
```

**Teoria vehiculului "Iubire" (Braitenberg nr. 3b):**

Conexiuni ipsilaterale INHIBITORII:
- Senzor stang-fata → REDUCE viteza motor stang → robotul vireaza SPRE obstacol
- Cand este aproape de obstacol → ambele motoare incetinesc → OPRIRE calma

**Diferenta fata de "Frica" (cerinta 3.5):**

| Vehicul  | Tip conexiune        | Comportament      |
|----------|----------------------|-------------------|
| "Frica"  | ipsilateral excitator | fuge de obstacol  |
| "Iubire" | ipsilateral inhibitor | se apropie, stop  |

**Observatii:** cu un obiect plasat in fata, robotul vireaza spre el si incetineste
progresiv pana se opreste. Comportamentul emergent seamana cu "atractia magnetica" -
robotul pare ca "iubeste" obiectul si vrea sa stea langa el.
Braitenberg descrie aceasta ca: vehiculul gaseste odihna langa sursa de stimul.
