# Confirmación pre-registrada: UCB1 sin reinicio frente a Tabu uniforme

48 instancias de congestión, 20 semillas (120–139), 960 pares. Pares fallidos: 0 de 960. Menor es mejor; la diferencia es alternativa menos referencia. Una sola comparación: no hay corrección múltiple.

| Id | Comparación | Media dif. | IC 95 % agrupado | Mejora / similar / empeora | Instancias mejor / peor | p |
|---|---|---:|---|---|---|---:|
| E1 | Tabu + UCB1 (3.030) vs Tabu uniforme (3.030) | -2.749 | [-4.069, -1.453] | 555 / 22 / 383 | 38 / 10 | 0.0000 |

| Alternativa | Objetivo medio | Makespan medio | Espera total media | Espera máxima media | Finales con espera | Reparación media | Última mejora (mediana) | Factibles |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Tabu uniforme (3.030) | 297.311 | 288.510 | 8.548 | 3.229 | 50.6% | 46.4% | 1380 | 100.0% |
| Tabu + UCB1 (3.030) | 294.561 | 286.855 | 7.223 | 2.921 | 49.9% | 40.3% | 1418 | 100.0% |

## Decisión pre-registrada sobre H1c

E1: media -2.749, IC [-4.069, -1.453], p 0.0000. **H1c queda respaldada.**
La regla exige p menor que 0,05, IC completo bajo cero y media de a lo sumo −0,25. La falta de significación no prueba equivalencia entre métodos.

## Variabilidad realizada

DE de la diferencia 13.684; DE de medias por instancia 3.551; ICC 0.018.

Las semillas nuevas sobre el mismo catálogo no miden generalización a otros hospitales. Estos resultados no se mezclan con estudios anteriores.
