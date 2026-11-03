# Estudio de congestión: comparaciones C1–C4

48 instancias, 20 semillas (90–109), 960 pares. Pares fallidos: 0 de 960. Menor es mejor; la diferencia es alternativa menos referencia.

## Presupuesto 3.030

| Id | Comparación | Media dif. | IC 95 % agrupado | Mejora / similar / empeora | Instancias mejor / peor | p | p Holm |
|---|---|---:|---|---|---|---:|---:|
| C1 | Tabu + D-MAB (3.030) vs Tabu uniforme (3.030) | -0.793 | [-1.850, +0.279] | 504 / 38 / 418 | 30 / 18 | 0.020 | 0.041 |
| C4 | Tabu + D-MAB (3.030) vs Tabu + UCB1 (3.030) | +1.824 | [+0.566, +3.124] | 410 / 45 / 505 | 13 / 35 | 0.001 | 0.005 |

| Alternativa | Objetivo medio | Makespan medio | Espera total media | Espera máxima media | Finales con espera | Última mejora (mediana) | Factibles |
|---|---:|---:|---:|---:|---:|---:|---:|
| Tabu uniforme (3.030) | 297.196 | 287.559 | 9.314 | 3.554 | 53.0% | 1230 | 100.0% |
| Tabu + D-MAB (3.030) | 296.403 | 287.791 | 8.289 | 3.188 | 50.6% | 1380 | 100.0% |
| Tabu + UCB1 (3.030) | 294.579 | 287.466 | 6.684 | 2.690 | 48.5% | 1410 | 100.0% |

## Presupuesto 6.060

| Id | Comparación | Media dif. | IC 95 % agrupado | Mejora / similar / empeora | Instancias mejor / peor | p | p Holm |
|---|---|---:|---|---|---|---:|---:|
| C2 | Cartera fija (6.060) vs Tabu prolongado (6.060) | -1.380 | [-2.405, -0.398] | 366 / 326 / 268 | 33 / 15 | 0.003 | 0.008 |
| C3 | Cartera fija (6.060) vs Dos Tabu (6.060) | -0.409 | [-1.126, +0.338] | 340 / 327 / 293 | 31 / 17 | 0.057 | 0.057 |

| Alternativa | Objetivo medio | Makespan medio | Espera total media | Espera máxima media | Finales con espera | Última mejora (mediana) | Factibles |
|---|---:|---:|---:|---:|---:|---:|---:|
| Tabu prolongado (6.060) | 293.226 | 286.103 | 6.832 | 2.645 | 46.0% | 2580 | 100.0% |
| Dos Tabu (6.060) | 292.256 | 284.735 | 7.165 | 2.809 | 51.1% | 1380 | 100.0% |
| Cartera fija (6.060) | 291.847 | 284.446 | 6.994 | 2.784 | 50.3% | 1530 | 100.0% |

## Decisión pre-registrada sobre H1

C1: media -0.793, IC [-1.850, +0.279], p Holm 0.041. **H1 no queda respaldada.**
La falta de significación no prueba equivalencia entre métodos.

## Variabilidad realizada de C1

DE de la diferencia 13.214; DE de medias por instancia 2.314; ICC 0.000.

Las alternativas de una misma pareja comparten prefijos y no son independientes. Estos resultados no se mezclan con estudios anteriores.
