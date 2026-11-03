# Validación emparejada (semillas nuevas)

Menor valor es mejor. Las celdas son medianas de 20 semillas por instancia. El objetivo incluye makespan y bloqueo; sus componentes se reportan por separado.

| Instancia | Mejor regla | Tabu mixto | Tabu + D-MAB | Tabu + UCB1 |
|---|---:|---:|---:|---:|
| HOSP-STD-15-01 | 147.502 | 145.752 | 145.002 | 143.752 |
| HOSP-STD-15-02 | 196.052 | 169.502 | 169.752 | 168.502 |
| HOSP-STD-15-03 | 173.001 | 157.227 | 155.101 | 156.252 |
| HOSP-STD-20-01 | 182.003 | 180.503 | 181.253 | 182.003 |
| HOSP-STD-20-02 | 207.003 | 207.003 | 207.003 | 207.003 |
| HOSP-STD-20-03 | 226.503 | 195.003 | 200.753 | 196.827 |
| HOSP-STD-25-01 | 239.704 | 223.254 | 225.004 | 222.254 |
| HOSP-STD-25-02 | 267.004 | 255.755 | 253.504 | 252.755 |
| HOSP-STD-25-03 | 239.004 | 234.504 | 234.754 | 235.504 |
| HOSP-STD-30-01 | 269.405 | 259.006 | 256.506 | 260.481 |
| HOSP-STD-30-02 | 310.306 | 298.906 | 296.757 | 297.256 |
| HOSP-STD-30-03 | 263.507 | 263.507 | 263.507 | 263.507 |

**D-MAB frente a Tabu mixto:** 115 victorias, 19 empates y 106 derrotas en pares instancia-semilla. Mediana de las 12 diferencias medianas: ≈0.000.

**UCB1 frente a Tabu mixto:** 118 victorias, 14 empates y 108 derrotas en pares instancia-semilla. Mediana de las 12 diferencias medianas: ≈0.000.

Estos resultados son empíricos y específicos del catálogo sintético. No prueban optimalidad ni una mejora universal del controlador. Las instancias de 15–30 cirugías no son los cuatro JSON históricos del repositorio oficial.

`runs.csv` conserva cada corrida; `baselines.csv`, `summary.csv`, `paired.csv` y `manifest.json` permiten auditar protocolo y comparaciones.

## Interpretación con umbral práctico

Una diferencia de menos de **0,25 min (15 s)** se considera pequeña para esta lectura descriptiva. El conteo exacto a tolerancia `1e−9` también está arriba; incluye cambios diminutos causados por el término de desempate `10⁻⁶ × suma de inicios`.

| Comparación con Tabu mixto | Gana >0,25 min | Diferencia ≤0,25 min | Pierde >0,25 min | Instancias gana / similar / pierde |
|---|---:|---:|---:|---:|
| D-MAB | 106 | 39 | 95 | 4 / 6 / 2 |
| UCB1 | 105 | 34 | 101 | 4 / 3 / 5 |

El efecto cambia de signo entre instancias; la mediana de las doce diferencias medianas de D-MAB es aproximadamente **0 min**. Estos datos no sostienen superioridad general sobre Tabu mixto. La ablación directa tampoco identifica una ventaja consistente del reinicio Page–Hinkley frente a UCB1.

Las 12 instancias de validación **ya se habían usado para elegir la arquitectura**. Las semillas 20–39 son nuevas, pero no se ensayaron instancias nuevas. La generalización fuera de este catálogo queda pendiente.

FIFO, SPT y LPT forman parte de las 30 soluciones iniciales de Tabu. Por ello superar la mejor de esas reglas no es evidencia independiente del beneficio de Tabu o de D-MAB: Tabu comienza al menos tan bien como la mejor regla.

Las medianas de bloqueo total son cero en todas las instancias y políticas. Entre 240 calendarios finales por política, hubo bloqueo positivo en 14 de Tabu mixto, 10 de D-MAB y 18 de UCB1. Por ello este catálogo y decodificador discriminan poco en bloqueo; la variación del objetivo proviene principalmente del makespan. No se puede afirmar que el controlador reduzca los quirófanos bloqueados de forma general.
