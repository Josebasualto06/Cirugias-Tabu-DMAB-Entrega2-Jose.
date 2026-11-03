# Comparación de carteras y asignación aprendida

Doce instancias YAML oficiales, veinte semillas nuevas 60–79 y siete resultados por pareja. El objetivo conserva makespan y espera. Menor es mejor; la diferencia es método menos Tabu con 6.060 evaluaciones.

## Presupuesto comparable

| Método | Evaluaciones | Diferencia media | IC 95 % agrupado | Mejora / similar / empeora | p Holm |
|---|---:|---:|---|---|---:|
| Tabu (6.060) | 6060 | +0.000 | [+0.000, +0.000] | 0 / 240 / 0 | — |
| Dos reinicios de Tabu | 6060 | -0.790 | [-1.711, +0.138] | 76 / 125 / 39 | 0.256 |
| Mejor de Tabu y D-MAB | 6060 | -0.656 | [-1.584, +0.169] | 74 / 122 / 44 | 0.330 |
| Asignación aprendida | 6060 | -0.788 | [-1.732, +0.046] | 74 / 123 / 43 | 0.330 |
| Asignación con respaldo | 6060 | -0.269 | [-0.994, +0.405] | 51 / 158 / 31 | 0.569 |

Los intervalos remuestrean instancias y semillas emparejadas dentro de instancia. Wilcoxon usa doce diferencias medias por instancia; Holm corrige las cuatro comparaciones de igual presupuesto. Los conteos usan un umbral práctico de 0,25 del objetivo.

## Respaldo y comparaciones adicionales

| Método | Referencia | Diferencia media | Mejora / similar / empeora |
|---|---|---:|---|
| Mejor de Tabu y D-MAB | Tabu (3.030) | -2.416 | 99 / 141 / 0 |
| Asignación con respaldo | Tabu (3.030) | -2.030 | 89 / 151 / 0 |
| Mejor de Tabu y D-MAB | Dos reinicios de Tabu | +0.134 | 71 / 104 / 65 |
| Asignación aprendida | Mejor de Tabu y D-MAB | -0.132 | 13 / 218 / 9 |
| Asignación con respaldo | Mejor de Tabu y D-MAB | +0.386 | 21 / 182 / 37 |

## Qué aprende el controlador

LinUCB elige qué trayectoria recibe el próximo bloque de 150 evaluaciones. Cada trayectoria conserva solución local, archivo, memoria tabú y su propio generador aleatorio. Sus diez entradas describen presupuesto, progreso, distancia al mejor, estancamiento y espera. La recompensa es la mejora del mejor global por bloque, normalizada al 2 % del objetivo inicial y limitada a [0,1]. Se observa únicamente el bloque realmente ejecutado.

La variante con respaldo termina primero 3.030 evaluaciones de Tabu uniforme. Conserva ese resultado y emplea el resto del presupuesto en los dos caminos. La garantía es frente a esa ejecución de 3.030, no frente a Tabu de 6.060. Las dos inicializaciones y los bloques de prueba se cuentan en las 6.060 evaluaciones.

## Límites

Las doce instancias ya se conocían al decidir la arquitectura: nuevas semillas no son nuevas instancias. No se seleccionaron parámetros con las semillas 60–79. El presupuesto protege la comparación de calidad, pero no iguala tiempo; los tiempos son descriptivos, medidos con tareas concurrentes. Dos reinicios de Tabu usan semillas independientes; Tabu+D-MAB comparte la inicialización de su primer camino. La función objetivo, la reparación y la disponibilidad de personal son las de la versión 2; la limpieza y las esperas máximas se mantienen. No se demuestra optimalidad.

## Reproducibilidad

Ejecutar `python -m experiments.compare_portfolios --workers 4`. `runs.csv` conserva resultados, `solutions.jsonl` conserva soluciones verificables y `decisions.csv` registra las decisiones online. El manifiesto fija parámetros, hashes y presupuesto.
