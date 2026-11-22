# Descriptivos de la revisión final del informe

**No estaban pre-registrados.** No prueban hipótesis ni cambian las decisiones de C1–C4 o E1. Cada estudio conserva su rango de semillas y tiene su propia tabla.

- RPD: respecto del mejor valor por instancia entre las semillas 90–109 y 120–139. No es un óptimo ni una cota.
- Sobrecosto de tiempo: mediana de los cocientes pareados de tiempo, con procesos concurrentes.
- Propuestas decodificadas: incluyen duplicados, que no consumen evaluaciones.
- `bootstrap_se_ratio`: error estándar del bootstrap jerárquico sobre el de las medias por instancia. Solo diagnostica el intervalo; no lo reemplaza.
- Semillas 20–39: configuración anterior (C = 1, λ = 0,35). Semillas 40–59: la vigente. No se combinan.

## Semillas 90–109

| Medida | Elemento | Valor |
|---|---|---:|
| objective | fifo | 358.937 |
| makespan | fifo | 266.458 |
| blocked | fifo | 105.177 |
| max_wait | fifo | 28.490 |
| rpd | fifo | 33.235 |
| objective | spt | 352.939 |
| makespan | spt | 266.604 |
| blocked | spt | 103.188 |
| max_wait | spt | 24.812 |
| rpd | spt | 30.365 |
| objective | lpt | 364.313 |
| makespan | lpt | 272.344 |
| blocked | lpt | 94.823 |
| max_wait | lpt | 31.823 |
| rpd | lpt | 36.260 |
| best | dmab3030 | 279.325 |
| objective | dmab3030 | 296.403 |
| worst | dmab3030 | 312.882 |
| sd | dmab3030 | 8.849 |
| rpd | dmab3030 | 9.457 |
| makespan | dmab3030 | 287.791 |
| blocked | dmab3030 | 8.289 |
| max_wait | dmab3030 | 3.188 |
| runtime | dmab3030 | 6.515 |
| improvement_over_best_rule | dmab3030 | 11.416 |
| best | fixed_portfolio6060 | 277.155 |
| objective | fixed_portfolio6060 | 291.847 |
| worst | fixed_portfolio6060 | 304.906 |
| sd | fixed_portfolio6060 | 7.287 |
| rpd | fixed_portfolio6060 | 7.756 |
| makespan | fixed_portfolio6060 | 284.446 |
| blocked | fixed_portfolio6060 | 6.994 |
| max_wait | fixed_portfolio6060 | 2.784 |
| runtime | fixed_portfolio6060 | 12.865 |
| improvement_over_best_rule | fixed_portfolio6060 | 12.784 |
| best | two_uniform6060 | 277.875 |
| objective | two_uniform6060 | 292.256 |
| worst | two_uniform6060 | 305.894 |
| sd | two_uniform6060 | 7.285 |
| rpd | two_uniform6060 | 7.893 |
| makespan | two_uniform6060 | 284.735 |
| blocked | two_uniform6060 | 7.165 |
| max_wait | two_uniform6060 | 2.809 |
| runtime | two_uniform6060 | 12.585 |
| improvement_over_best_rule | two_uniform6060 | 12.671 |
| best | ucb3030 | 277.214 |
| objective | ucb3030 | 294.579 |
| worst | ucb3030 | 311.788 |
| sd | ucb3030 | 9.363 |
| rpd | ucb3030 | 8.788 |
| makespan | ucb3030 | 287.466 |
| blocked | ucb3030 | 6.684 |
| max_wait | ucb3030 | 2.690 |
| runtime | ucb3030 | 6.766 |
| improvement_over_best_rule | ucb3030 | 11.956 |
| best | uniform3030 | 280.308 |
| objective | uniform3030 | 297.196 |
| worst | uniform3030 | 312.797 |
| sd | uniform3030 | 8.722 |
| rpd | uniform3030 | 9.754 |
| makespan | uniform3030 | 287.559 |
| blocked | uniform3030 | 9.314 |
| max_wait | uniform3030 | 3.554 |
| runtime | uniform3030 | 6.166 |
| improvement_over_best_rule | uniform3030 | 11.178 |
| best | uniform6060 | 277.814 |
| objective | uniform6060 | 293.226 |
| worst | uniform6060 | 307.969 |
| sd | uniform6060 | 7.951 |
| rpd | uniform6060 | 8.247 |
| makespan | uniform6060 | 286.103 |
| blocked | uniform6060 | 6.832 |
| max_wait | uniform6060 | 2.645 |
| runtime | uniform6060 | 12.426 |
| improvement_over_best_rule | uniform6060 | 12.382 |
| time_overhead | dmab3030 | 3.990 |
| time_overhead | ucb3030 | 10.171 |
| relative_difference | C1 | -0.267 |
| instances_better | C1 | 30.000 |
| bootstrap_se_ratio | C1 | 1.616 |
| difference_15 | C1 | -0.514 |
| instances_better_15 | C1 | 7.000 |
| difference_20 | C1 | -0.437 |
| instances_better_20 | C1 | 6.000 |
| difference_25 | C1 | -0.123 |
| instances_better_25 | C1 | 7.000 |
| difference_30 | C1 | -2.099 |
| instances_better_30 | C1 | 10.000 |
| relative_difference | C2 | -0.471 |
| instances_better | C2 | 33.000 |
| bootstrap_se_ratio | C2 | 1.165 |
| difference_15 | C2 | 0.699 |
| instances_better_15 | C2 | 5.000 |
| difference_20 | C2 | 0.187 |
| instances_better_20 | C2 | 6.000 |
| difference_25 | C2 | -1.978 |
| instances_better_25 | C2 | 10.000 |
| difference_30 | C2 | -4.426 |
| instances_better_30 | C2 | 12.000 |
| relative_difference | C3 | -0.140 |
| instances_better | C3 | 31.000 |
| bootstrap_se_ratio | C3 | 1.437 |
| difference_15 | C3 | -0.122 |
| instances_better_15 | C3 | 6.000 |
| difference_20 | C3 | -0.308 |
| instances_better_20 | C3 | 7.000 |
| difference_25 | C3 | 0.375 |
| instances_better_25 | C3 | 7.000 |
| difference_30 | C3 | -1.581 |
| instances_better_30 | C3 | 11.000 |
| relative_difference | C4 | 0.619 |
| instances_better | C4 | 13.000 |
| bootstrap_se_ratio | C4 | 1.271 |
| difference_15 | C4 | -0.976 |
| instances_better_15 | C4 | 7.000 |
| difference_20 | C4 | 1.399 |
| instances_better_20 | C4 | 3.000 |
| difference_25 | C4 | 4.946 |
| instances_better_25 | C4 | 0.000 |
| difference_30 | C4 | 1.926 |
| instances_better_30 | C4 | 3.000 |
| decoded_proposals | dmab3030 | 3268.885 |
| decoded_overhead | dmab3030 | 4.611 |
| share_swap | dmab3030 | 16.970 |
| share_insert | dmab3030 | 17.272 |
| share_room_1 | dmab3030 | 27.050 |
| share_room_2 | dmab3030 | 17.941 |
| share_room_pair | dmab3030 | 20.767 |
| decoded_proposals | ucb3030 | 3439.261 |
| decoded_overhead | ucb3030 | 10.064 |
| share_swap | ucb3030 | 9.697 |
| share_insert | ucb3030 | 11.310 |
| share_room_1 | ucb3030 | 39.054 |
| share_room_2 | ucb3030 | 13.058 |
| share_room_pair | ucb3030 | 26.881 |
| decoded_proposals | uniform3030 | 3124.797 |
| decoded_overhead | uniform3030 | 0.000 |
| share_swap | uniform3030 | 20.264 |
| share_insert | uniform3030 | 20.540 |
| share_room_1 | uniform3030 | 19.594 |
| share_room_2 | uniform3030 | 19.007 |
| share_room_pair | uniform3030 | 20.596 |

## Semillas 120–139

| Medida | Elemento | Valor |
|---|---|---:|
| best | ucb3030 | 276.643 |
| objective | ucb3030 | 294.561 |
| worst | ucb3030 | 313.350 |
| sd | ucb3030 | 9.890 |
| rpd | ucb3030 | 8.792 |
| makespan | ucb3030 | 286.855 |
| blocked | ucb3030 | 7.223 |
| max_wait | ucb3030 | 2.921 |
| runtime | ucb3030 | 6.011 |
| improvement_over_best_rule | ucb3030 | 11.943 |
| best | uniform3030 | 279.923 |
| objective | uniform3030 | 297.311 |
| worst | uniform3030 | 312.720 |
| sd | uniform3030 | 8.902 |
| rpd | uniform3030 | 9.800 |
| makespan | uniform3030 | 288.510 |
| blocked | uniform3030 | 8.548 |
| max_wait | uniform3030 | 3.229 |
| runtime | uniform3030 | 5.434 |
| improvement_over_best_rule | uniform3030 | 11.130 |
| time_overhead | ucb3030 | 9.838 |
| relative_difference | E1 | -0.925 |
| instances_better | E1 | 38.000 |
| bootstrap_se_ratio | E1 | 1.307 |
| difference_15 | E1 | 0.123 |
| instances_better_15 | E1 | 6.000 |
| difference_20 | E1 | -2.960 |
| instances_better_20 | E1 | 10.000 |
| difference_25 | E1 | -3.912 |
| instances_better_25 | E1 | 11.000 |
| difference_30 | E1 | -4.249 |
| instances_better_30 | E1 | 11.000 |
| decoded_proposals | ucb3030 | 3436.711 |
| decoded_overhead | ucb3030 | 9.933 |
| share_swap | ucb3030 | 9.822 |
| share_insert | ucb3030 | 11.819 |
| share_room_1 | ucb3030 | 38.502 |
| share_room_2 | ucb3030 | 13.298 |
| share_room_pair | ucb3030 | 26.559 |
| decoded_proposals | uniform3030 | 3126.200 |
| decoded_overhead | uniform3030 | 0.000 |
| share_swap | uniform3030 | 20.441 |
| share_insert | uniform3030 | 20.285 |
| share_room_1 | uniform3030 | 19.578 |
| share_room_2 | uniform3030 | 19.243 |
| share_room_pair | uniform3030 | 20.453 |

## Semillas 20–39

| Medida | Elemento | Valor |
|---|---|---:|
| difference | dmab-uniform | -0.513 |
| instances_better | dmab-uniform | 8.000 |
| difference | ucb-uniform | -0.455 |
| instances_better | ucb-uniform | 8.000 |
| difference | dmab-ucb | -0.058 |
| instances_better | dmab-ucb | 7.000 |

## Semillas 40–59

| Medida | Elemento | Valor |
|---|---|---:|
| difference | dmab-uniform | 0.577 |
| instances_better | dmab-uniform | 4.000 |
| difference | ucb-uniform | 1.182 |
| instances_better | ucb-uniform | 3.000 |
| difference | dmab-ucb | -0.605 |
| instances_better | dmab-ucb | 9.000 |

## Semillas 60–79

| Medida | Elemento | Valor |
|---|---|---:|
| difference | dmab3030-uniform3030 | 0.108 |
| instances_better | dmab3030-uniform3030 | 6.000 |
| difference | fixed_portfolio6060-uniform6060 | -0.656 |
| instances_better | fixed_portfolio6060-uniform6060 | 8.000 |
| difference | fixed_portfolio6060-two_uniform6060 | 0.134 |
| instances_better | fixed_portfolio6060-two_uniform6060 | 7.000 |

## Semillas 110–114

| Medida | Elemento | Valor |
|---|---|---:|
| difference | dmab-uniform | 1.653 |
| instances_better | dmab-uniform | 1.000 |
| difference_15 | dmab-uniform | 0.210 |
| difference_20 | dmab-uniform | -2.300 |
| difference_25 | dmab-uniform | 2.700 |
| difference_30 | dmab-uniform | 6.001 |

## Semillas 0–5

| Medida | Elemento | Valor |
|---|---|---:|
| variants | all | 14.000 |
| difference | chosen | -0.224 |
| difference | runner_up | -0.140 |
| difference | lambda_10 | 1.173 |

## Semillas 90–139

| Medida | Elemento | Valor |
|---|---|---:|
| replayed_runs | all | 4800.000 |
