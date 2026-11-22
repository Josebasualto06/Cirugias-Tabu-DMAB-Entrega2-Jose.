# Cierre del informe: tres medidas exploratorias

**Se calcularon después de ver los resultados.** No prueban hipótesis ni cambian las decisiones registradas.

- `effect_size_r`: r = Z/√n de la prueba de Wilcoxon registrada, sobre las mismas medias por instancia. Z usa la aproximación normal; un valor negativo favorece a la alternativa.
- Retraso: solo se mueve el inicio de la anestesia, hasta que la preparación de la cirugía puede empezar. Cada calendario se comprobó sin solapamientos. No se repitió la búsqueda, así que no dice qué habría encontrado con esa regla.
- `official`: instancias oficiales, semillas 60–79, media por instancia frente a la mejor de FIFO, SPT y LPT en cada medida. `course_objective` suma 100 veces el desequilibrio de salas del objetivo de clase. No usa el simulador docente ni su regla de salas.

| Medida | Elemento | Valor |
|---|---|---:|
| effect_size_r | C1 | -0.333 |
| effect_size_r | C2 | -0.426 |
| effect_size_r | C3 | -0.275 |
| effect_size_r | C4 | 0.459 |
| effect_size_r | E1 | -0.637 |
| delayed_schedules | all | 7680.000 |
| schedules_waiting_after_delay | all | 0.000 |
| best_rule_delayed_objective | all | 253.734 |
| mean_objective | entrega2_congestion_90_109:dmab3030 | 296.403 |
| mean_delayed_objective | entrega2_congestion_90_109:dmab3030 | 287.796 |
| instances_where_best_rule_wins | entrega2_congestion_90_109:dmab3030 | 48.000 |
| mean_objective | entrega2_congestion_90_109:fixed_portfolio6060 | 291.847 |
| mean_delayed_objective | entrega2_congestion_90_109:fixed_portfolio6060 | 284.451 |
| instances_where_best_rule_wins | entrega2_congestion_90_109:fixed_portfolio6060 | 48.000 |
| mean_objective | entrega2_congestion_90_109:two_uniform6060 | 292.256 |
| mean_delayed_objective | entrega2_congestion_90_109:two_uniform6060 | 284.741 |
| instances_where_best_rule_wins | entrega2_congestion_90_109:two_uniform6060 | 48.000 |
| mean_objective | entrega2_congestion_90_109:ucb3030 | 294.579 |
| mean_delayed_objective | entrega2_congestion_90_109:ucb3030 | 287.471 |
| instances_where_best_rule_wins | entrega2_congestion_90_109:ucb3030 | 48.000 |
| mean_objective | entrega2_congestion_90_109:uniform3030 | 297.196 |
| mean_delayed_objective | entrega2_congestion_90_109:uniform3030 | 287.564 |
| instances_where_best_rule_wins | entrega2_congestion_90_109:uniform3030 | 48.000 |
| mean_objective | entrega2_congestion_90_109:uniform6060 | 293.226 |
| mean_delayed_objective | entrega2_congestion_90_109:uniform6060 | 286.108 |
| instances_where_best_rule_wins | entrega2_congestion_90_109:uniform6060 | 48.000 |
| ucb_minus_uniform_objective | entrega2_congestion_90_109 | -2.617 |
| ucb_minus_uniform_delayed_objective | entrega2_congestion_90_109 | -0.093 |
| mean_objective | entrega3_confirmacion_ucb1:ucb3030 | 294.561 |
| mean_delayed_objective | entrega3_confirmacion_ucb1:ucb3030 | 286.860 |
| instances_where_best_rule_wins | entrega3_confirmacion_ucb1:ucb3030 | 48.000 |
| mean_objective | entrega3_confirmacion_ucb1:uniform3030 | 297.311 |
| mean_delayed_objective | entrega3_confirmacion_ucb1:uniform3030 | 288.516 |
| instances_where_best_rule_wins | entrega3_confirmacion_ucb1:uniform3030 | 48.000 |
| ucb_minus_uniform_objective | entrega3_confirmacion_ucb1 | -2.749 |
| ucb_minus_uniform_delayed_objective | entrega3_confirmacion_ucb1 | -1.656 |
| official_instances_better_than_best_rule | fixed_portfolio6060:objective | 12.000 |
| official_mean_gain_percent | fixed_portfolio6060:objective | 5.892 |
| official_runs_worse_than_best_rule | fixed_portfolio6060:objective | 0.000 |
| official_instances_better_than_best_rule | fixed_portfolio6060:makespan | 10.000 |
| official_mean_gain_percent | fixed_portfolio6060:makespan | 1.424 |
| official_runs_worse_than_best_rule | fixed_portfolio6060:makespan | 50.000 |
| official_instances_better_than_best_rule | fixed_portfolio6060:course_objective | 10.000 |
| official_mean_gain_percent | fixed_portfolio6060:course_objective | 5.815 |
| official_runs_worse_than_best_rule | fixed_portfolio6060:course_objective | 25.000 |
| official_instances_better_than_best_rule | two_uniform6060:objective | 12.000 |
| official_mean_gain_percent | two_uniform6060:objective | 5.904 |
| official_runs_worse_than_best_rule | two_uniform6060:objective | 0.000 |
| official_instances_better_than_best_rule | two_uniform6060:makespan | 10.000 |
| official_mean_gain_percent | two_uniform6060:makespan | 1.449 |
| official_runs_worse_than_best_rule | two_uniform6060:makespan | 43.000 |
| official_instances_better_than_best_rule | two_uniform6060:course_objective | 10.000 |
| official_mean_gain_percent | two_uniform6060:course_objective | 5.826 |
| official_runs_worse_than_best_rule | two_uniform6060:course_objective | 32.000 |
