# Validación emparejada (semillas nuevas)

Menor valor es mejor. Las celdas son medianas de 20 semillas por instancia. El objetivo incluye makespan y bloqueo; sus componentes se reportan por separado.

| Instancia | Mejor regla | Tabu mixto | Tabu + D-MAB | Tabu + UCB1 |
|---|---:|---:|---:|---:|
| HOSP-STD-15-01 | 147.502 | 144.751 | 146.001 | 145.252 |
| HOSP-STD-15-02 | 196.052 | 169.252 | 168.752 | 170.752 |
| HOSP-STD-15-03 | 173.001 | 156.501 | 157.752 | 161.751 |
| HOSP-STD-20-01 | 182.003 | 182.003 | 182.003 | 181.003 |
| HOSP-STD-20-02 | 207.003 | 207.003 | 207.003 | 207.003 |
| HOSP-STD-20-03 | 226.503 | 200.253 | 201.253 | 201.003 |
| HOSP-STD-25-01 | 239.704 | 220.754 | 226.254 | 228.004 |
| HOSP-STD-25-02 | 267.004 | 257.504 | 253.504 | 254.505 |
| HOSP-STD-25-03 | 239.004 | 233.004 | 236.479 | 234.754 |
| HOSP-STD-30-01 | 269.405 | 257.481 | 257.755 | 261.505 |
| HOSP-STD-30-02 | 310.306 | 299.006 | 297.507 | 295.131 |
| HOSP-STD-30-03 | 263.507 | 263.507 | 263.507 | 263.507 |

**D-MAB frente a Tabu mixto:** 101 victorias, 13 empates y 126 derrotas en pares instancia-semilla. Mediana de las 12 diferencias medianas: ≈0.000.

**UCB1 frente a Tabu mixto:** 100 victorias, 14 empates y 126 derrotas en pares instancia-semilla. Mediana de las 12 diferencias medianas: +1.125.

## Pruebas estadísticas

Wilcoxon de rangos con signo, bilateral, sobre las diferencias emparejadas del objetivo (alternativa − referencia; negativo favorece a la alternativa). Holm corrige las tres comparaciones globales.

| Comparación | Pares | Media dif. | Gana / empata / pierde | p | p Holm |
|---|---:|---:|---:|---:|---:|
| D-MAB vs Tabu mixto | 240 | +0.577 | 101 / 13 / 126 | 0.161 | 0.161 |
| UCB1 vs Tabu mixto | 240 | +1.182 | 100 / 14 / 126 | 0.0281 | 0.0842 |
| D-MAB vs UCB1 | 240 | -0.605 | 103 / 61 / 76 | 0.0592 | 0.118 |

Por instancia (36 pruebas, Holm): 0 con p Holm < 0,05.
Detalle en `statistics.csv`.

Estos resultados son empíricos y específicos del catálogo sintético. No prueban optimalidad ni una mejora universal del controlador. Las instancias de 15–30 cirugías no son los cuatro JSON históricos del repositorio oficial.

`runs.csv` conserva cada corrida; `baselines.csv`, `summary.csv`, `paired.csv` y `manifest.json` permiten auditar protocolo y comparaciones.

## Interpretación con umbral práctico

Una diferencia de menos de **0,25 min (15 s)** se considera pequeña para esta lectura descriptiva. El conteo exacto a tolerancia `1e−9` también está arriba; incluye cambios diminutos causados por el término de desempate `10⁻⁶ × suma de inicios`.

| Comparación con Tabu mixto | Gana >0,25 min | Diferencia ≤0,25 min | Pierde >0,25 min | Instancias gana / similar / pierde |
|---|---:|---:|---:|---:|
| D-MAB | 89 | 47 | 104 | 3 / 5 / 4 |
| UCB1 | 84 | 49 | 107 | 2 / 3 / 7 |

La mediana de las doce diferencias medianas de D-MAB frente a Tabu mixto es **+0.00 min** y el signo cambia entre instancias. La lectura inferencial está en la sección de pruebas estadísticas (Wilcoxon con corrección de Holm).

Las 12 instancias de validación **ya se habían usado para elegir la arquitectura**. Las semillas 40–59 son nuevas, pero no se ensayaron instancias nuevas. La generalización fuera de este catálogo queda pendiente.

FIFO, SPT y LPT forman parte de las 30 soluciones iniciales de Tabu. Por ello superar la mejor de esas reglas no es evidencia independiente del beneficio de Tabu o de D-MAB: Tabu comienza al menos tan bien como la mejor regla.

Las medianas de bloqueo total son cero en todas las instancias y políticas. Entre 240 calendarios finales por política, hubo bloqueo positivo en 13 de Tabu mixto, 11 de D-MAB y 13 de UCB1. Por ello este catálogo y decodificador discriminan poco en bloqueo; la variación del objetivo proviene principalmente del makespan. No se puede afirmar que el controlador reduzca los quirófanos bloqueados de forma general.
