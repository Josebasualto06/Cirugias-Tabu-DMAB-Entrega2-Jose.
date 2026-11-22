# Diagnóstico posterior del reinicio y del modelo

**No estaba pre-registrado.** No prueba hipótesis ni cambia las decisiones de C1–C4 o E1.

- Las corridas de Tabu uniforme y D-MAB de las semillas 90–109 se repitieron con observadores; todas reprodujeron su valor archivado.
- El banco estacionario solo alimenta el bandido. Sortea recompensas de la misma instancia, observadas bajo selección uniforme, que no cambian durante la corrida. `identical_arms` da además la misma distribución a los cinco brazos.
- `rewarded_that_improve_best`: recompensadas que mejoran el mejor global previo al lote.
- La regla del simulador docente retiene la sala de anestesia hasta el final de la cirugía. La del proyecto sigue la formulación de clase: hasta que empieza la cirugía.
- Recalcular calendarios con otra regla no dice qué habría encontrado una búsqueda con esa regla.

| Medida | Elemento | Valor |
|---|---|---:|
| rewarded_share | uniform | 3.864 |
| rewarded_that_improve_best | uniform | 8.509 |
| rewarded_share_by_phase | uniform:1 | 3.904 |
| global_improvements_per_1000_by_phase | uniform:1 | 7.357 |
| rewarded_share_by_phase_and_move | uniform:1:swap | 2.113 |
| rewarded_share_by_phase_and_move | uniform:1:insert | 2.368 |
| rewarded_share_by_phase_and_move | uniform:1:room_1 | 7.599 |
| rewarded_share_by_phase_and_move | uniform:1:room_2 | 3.747 |
| rewarded_share_by_phase_and_move | uniform:1:room_pair | 3.689 |
| rewarded_share_by_phase | uniform:2 | 3.832 |
| global_improvements_per_1000_by_phase | uniform:2 | 1.639 |
| rewarded_share_by_phase_and_move | uniform:2:swap | 1.830 |
| rewarded_share_by_phase_and_move | uniform:2:insert | 2.096 |
| rewarded_share_by_phase_and_move | uniform:2:room_1 | 7.958 |
| rewarded_share_by_phase_and_move | uniform:2:room_2 | 3.443 |
| rewarded_share_by_phase_and_move | uniform:2:room_pair | 3.877 |
| rewarded_share_by_phase | uniform:3 | 3.857 |
| global_improvements_per_1000_by_phase | uniform:3 | 0.861 |
| rewarded_share_by_phase_and_move | uniform:3:swap | 1.760 |
| rewarded_share_by_phase_and_move | uniform:3:insert | 2.106 |
| rewarded_share_by_phase_and_move | uniform:3:room_1 | 7.975 |
| rewarded_share_by_phase_and_move | uniform:3:room_2 | 3.417 |
| rewarded_share_by_phase_and_move | uniform:3:room_pair | 3.970 |
| rewarded_share | dmab | 4.145 |
| rewarded_that_improve_best | dmab | 8.377 |
| rewarded_share_by_phase | dmab:1 | 4.205 |
| global_improvements_per_1000_by_phase | dmab:1 | 7.718 |
| rewarded_share_by_phase_and_move | dmab:1:swap | 2.170 |
| rewarded_share_by_phase_and_move | dmab:1:insert | 2.486 |
| rewarded_share_by_phase_and_move | dmab:1:room_1 | 7.083 |
| rewarded_share_by_phase_and_move | dmab:1:room_2 | 3.793 |
| rewarded_share_by_phase_and_move | dmab:1:room_pair | 3.711 |
| rewarded_share_by_phase | dmab:2 | 4.107 |
| global_improvements_per_1000_by_phase | dmab:2 | 1.748 |
| rewarded_share_by_phase_and_move | dmab:2:swap | 1.755 |
| rewarded_share_by_phase_and_move | dmab:2:insert | 2.262 |
| rewarded_share_by_phase_and_move | dmab:2:room_1 | 6.886 |
| rewarded_share_by_phase_and_move | dmab:2:room_2 | 3.432 |
| rewarded_share_by_phase_and_move | dmab:2:room_pair | 3.967 |
| rewarded_share_by_phase | dmab:3 | 4.124 |
| global_improvements_per_1000_by_phase | dmab:3 | 1.006 |
| rewarded_share_by_phase_and_move | dmab:3:swap | 1.914 |
| rewarded_share_by_phase_and_move | dmab:3:insert | 2.297 |
| rewarded_share_by_phase_and_move | dmab:3:room_1 | 6.915 |
| rewarded_share_by_phase_and_move | dmab:3:room_2 | 3.322 |
| rewarded_share_by_phase_and_move | dmab:3:room_pair | 4.019 |
| instances_with_same_best_move_in_all_phases | uniform | 47.000 |
| instances_with_room_1_best_in_all_phases | uniform | 47.000 |
| median_restarts | dmab | 24.000 |
| restarts_by_leader_share | dmab | 96.811 |
| stationary_median_restarts | identical_arms | 25.000 |
| stationary_median_restarts | different_arms | 28.000 |
| stationary_share_of_possible_gain | different_arms | 18.276 |
| stationary_median_restarts | different_arms_lambda_10 | 0.000 |
| stationary_share_of_possible_gain | different_arms_lambda_10 | 75.051 |
| stationary_median_restarts | different_arms_without_restart | 0.000 |
| stationary_share_of_possible_gain | different_arms_without_restart | 75.456 |
| final_schedules | all | 7680.000 |
| infeasible_with_repository_rule | all | 83.411 |
| cross_room_share | all | 65.981 |
| ucb_time_overhead_by_size | 15 | 12.093 |
| ucb_time_overhead_by_size | 20 | 11.990 |
| ucb_time_overhead_by_size | 25 | 10.290 |
| ucb_time_overhead_by_size | 30 | 7.222 |
