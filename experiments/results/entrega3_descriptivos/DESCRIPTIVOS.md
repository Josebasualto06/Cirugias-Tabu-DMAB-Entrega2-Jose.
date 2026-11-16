# Descriptivos del estudio de congestión para el informe final

**No estaban pre-registrados.** No ejecutan búsquedas ni usan semillas nuevas: resumen columnas de `entrega2_congestion_90_109/runs.csv` (semillas 90–109). Son descriptivos y no integran la familia C1–C4.

## Reparación media por corrida

Candidatos evaluados que el decodificador reparó, sobre 3.000 candidatos por corrida.

| Método | Reparación media |
|---|---:|
| Tabu uniforme (3.030) | 46.6% |
| Tabu + D-MAB (3.030) | 44.0% |
| Tabu + UCB1 (3.030) | 40.1% |

## Reinicios Page–Hinkley de D-MAB

Mediana 24 reinicios por corrida de 3.030 evaluaciones (media 23.1; rango 0–53). Equivale a un reinicio cada 126 evaluaciones. UCB1 no reinicia por construcción (máximo 0).

## Tabu prolongado sin mejoras en su segunda mitad

En 546 de 960 corridas (56.9%), la última mejora del Tabu prolongado ocurrió dentro de sus primeras 3.030 evaluaciones. La última mejora se registra por bloques de 150 evaluaciones.

## Camino conservado por la cartera

La cartera conservó el camino D-MAB en 516 de 960 pares y el camino uniforme en 444. Un empate completo conserva Tabu uniforme.
