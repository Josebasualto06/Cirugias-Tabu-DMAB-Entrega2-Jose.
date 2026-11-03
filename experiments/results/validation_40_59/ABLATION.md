# Ablación: D-MAB frente a UCB1 sin Page–Hinkley

Se emparejan 20 semillas nuevas por cada una de las 12 instancias; menor objetivo es mejor. La diferencia es `D-MAB − UCB1`.

| Instancia | Mediana D-MAB | Mediana UCB1 | Mediana diferencia pareada | D-MAB gana / empate / UCB1 gana |
|---|---:|---:|---:|---:|
| HOSP-STD-15-01 | 146.001 | 145.252 | +0.000 | 9 / 5 / 6 |
| HOSP-STD-15-02 | 168.752 | 170.752 | -1.750 | 11 / 0 / 9 |
| HOSP-STD-15-03 | 157.752 | 161.751 | -2.000 | 13 / 3 / 4 |
| HOSP-STD-20-01 | 182.003 | 181.003 | +0.250 | 3 / 7 / 10 |
| HOSP-STD-20-02 | 207.003 | 207.003 | +0.000 | 1 / 18 / 1 |
| HOSP-STD-20-03 | 201.253 | 201.003 | +0.000 | 9 / 1 / 10 |
| HOSP-STD-25-01 | 226.254 | 228.004 | -2.000 | 12 / 0 / 8 |
| HOSP-STD-25-02 | 253.504 | 254.505 | -2.300 | 13 / 3 / 4 |
| HOSP-STD-25-03 | 236.479 | 234.754 | +0.000 | 7 / 5 / 8 |
| HOSP-STD-30-01 | 257.755 | 261.505 | -5.050 | 14 / 0 / 6 |
| HOSP-STD-30-02 | 297.507 | 295.131 | +1.250 | 7 / 3 / 10 |
| HOSP-STD-30-03 | 263.507 | 263.507 | +0.000 | 4 / 16 / 0 |

En los 240 pares instancia-semilla, D-MAB gana 103, empata 61 y pierde 76 frente a UCB1 en objetivo. A nivel de 12 instancias (mediana pareada), gana en 5, empata en 4 y pierde en 3; la mediana de esas 12 diferencias es +0.000.

Mediana del tiempo por corrida (segundos): uniform=3.785, dmab=3.831, ucb=3.918.
 Mediana de reinicios Page–Hinkley por corrida D-MAB: 11.0.

Movimientos evaluados acumulados en las 240 corridas por política:

| Política | Swap | Insert | Sala anestesia | Sala cirugía | Ambas salas |
|---|---:|---:|---:|---:|---:|
| dmab | 127482 | 130547 | 194209 | 117014 | 150748 |
| ucb | 83728 | 100128 | 232126 | 99352 | 204666 |

La selección de brazos y los reinicios muestran que el controlador sí cambió sus preferencias. Una ventaja numérica en este catálogo no demuestra un beneficio general de Page–Hinkley; para interpretar el efecto también hay que comparar las métricas y el costo de ejecución.

La diferencia entre medianas de política puede no ser igual a la mediana de diferencias emparejadas; ambas se muestran explícitamente.
