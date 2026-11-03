# Ablación: D-MAB frente a UCB1 sin Page–Hinkley

Se emparejan 20 semillas nuevas por cada una de las 12 instancias; menor objetivo es mejor. La diferencia es `D-MAB − UCB1`.

| Instancia | Mediana D-MAB | Mediana UCB1 | Mediana diferencia pareada | D-MAB gana / empate / UCB1 gana |
|---|---:|---:|---:|---:|
| HOSP-STD-15-01 | 145.002 | 143.752 | +1.000 | 7 / 2 / 11 |
| HOSP-STD-15-02 | 169.752 | 168.502 | +0.750 | 9 / 0 / 11 |
| HOSP-STD-15-03 | 155.101 | 156.252 | -1.250 | 11 / 3 / 6 |
| HOSP-STD-20-01 | 181.253 | 182.003 | +0.000 | 8 / 8 / 4 |
| HOSP-STD-20-02 | 207.003 | 207.003 | +0.000 | 0 / 14 / 6 |
| HOSP-STD-20-03 | 200.753 | 196.827 | +3.400 | 7 / 0 / 13 |
| HOSP-STD-25-01 | 225.004 | 222.254 | +4.750 | 8 / 0 / 12 |
| HOSP-STD-25-02 | 253.504 | 252.755 | +0.250 | 8 / 1 / 11 |
| HOSP-STD-25-03 | 234.754 | 235.504 | -2.500 | 12 / 0 / 8 |
| HOSP-STD-30-01 | 256.506 | 260.481 | -0.200 | 10 / 0 / 10 |
| HOSP-STD-30-02 | 296.757 | 297.256 | -1.725 | 11 / 0 / 9 |
| HOSP-STD-30-03 | 263.507 | 263.507 | +0.000 | 5 / 11 / 4 |

En los 240 pares instancia-semilla, D-MAB gana 96, empata 39 y pierde 105 frente a UCB1 en objetivo. A nivel de 12 instancias (mediana pareada), gana en 4, empata en 3 y pierde en 5; la mediana de esas 12 diferencias es +0.000.

Mediana del tiempo por corrida (segundos): uniform=0.913, dmab=0.901, ucb=0.895.
 Mediana de reinicios Page–Hinkley por corrida D-MAB: 18.0.

Movimientos evaluados acumulados en las 240 corridas por política:

| Política | Swap | Insert | Sala anestesia | Sala cirugía | Ambas salas |
|---|---:|---:|---:|---:|---:|
| dmab | 144233 | 144679 | 150251 | 135767 | 145070 |
| ucb | 139028 | 144332 | 163868 | 131089 | 141683 |

La selección de brazos y los reinicios muestran que el controlador sí cambió sus preferencias. Una ventaja numérica en este catálogo no demuestra un beneficio general de Page–Hinkley; para interpretar el efecto también hay que comparar las métricas y el costo de ejecución.

La diferencia entre medianas de política puede no ser igual a la mediana de diferencias emparejadas; ambas se muestran explícitamente.
