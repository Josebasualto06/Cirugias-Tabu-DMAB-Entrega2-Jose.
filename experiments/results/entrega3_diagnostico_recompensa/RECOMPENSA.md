# Recompensa media y momento de los reinicios

**Exploratorio y posterior.** No prueba hipótesis ni cambia decisiones.

- Muestra: 384 corridas archivadas (48 instancias, semillas 90–93, Tabu uniforme y D-MAB), repetidas sin discrepancias.
- `mean_reward`: recompensa por propuesta, que es lo que observa Page–Hinkley. Un duplicado vale cero.
- Tercios y décimos se forman con los 200 lotes de cada corrida.

| Medida | Elemento | Valor |
|---|---|---:|
| mean_reward_by_third | uniform:1 | 0.0228 |
| mean_reward_by_third | uniform:2 | 0.0206 |
| mean_reward_by_third | uniform:3 | 0.0211 |
| mean_reward_by_tenth | uniform:1 | 0.0252 |
| mean_reward_by_tenth | uniform:2 | 0.0237 |
| mean_reward_by_tenth | uniform:3 | 0.0203 |
| mean_reward_by_tenth | uniform:4 | 0.0216 |
| mean_reward_by_tenth | uniform:5 | 0.0212 |
| mean_reward_by_tenth | uniform:6 | 0.0199 |
| mean_reward_by_tenth | uniform:7 | 0.0193 |
| mean_reward_by_tenth | uniform:8 | 0.0211 |
| mean_reward_by_tenth | uniform:9 | 0.0214 |
| mean_reward_by_tenth | uniform:10 | 0.0213 |
| mean_reward_by_third | dmab:1 | 0.0252 |
| restarts_share_by_third | dmab:1 | 40.7286 |
| mean_reward_by_third | dmab:2 | 0.0218 |
| restarts_share_by_third | dmab:2 | 29.7775 |
| mean_reward_by_third | dmab:3 | 0.0223 |
| restarts_share_by_third | dmab:3 | 29.4939 |
| mean_reward_by_tenth | dmab:1 | 0.0276 |
| restarts_share_by_tenth | dmab:1 | 14.7251 |
| mean_reward_by_tenth | dmab:2 | 0.0245 |
| restarts_share_by_tenth | dmab:2 | 11.3220 |
| mean_reward_by_tenth | dmab:3 | 0.0243 |
| restarts_share_by_tenth | dmab:3 | 11.4092 |
| mean_reward_by_tenth | dmab:4 | 0.0221 |
| restarts_share_by_tenth | dmab:4 | 9.0096 |
| mean_reward_by_tenth | dmab:5 | 0.0219 |
| restarts_share_by_tenth | dmab:5 | 8.5297 |
| mean_reward_by_tenth | dmab:6 | 0.0219 |
| restarts_share_by_tenth | dmab:6 | 8.7260 |
| mean_reward_by_tenth | dmab:7 | 0.0222 |
| restarts_share_by_tenth | dmab:7 | 9.3150 |
| mean_reward_by_tenth | dmab:8 | 0.0227 |
| restarts_share_by_tenth | dmab:8 | 9.2059 |
| mean_reward_by_tenth | dmab:9 | 0.0218 |
| restarts_share_by_tenth | dmab:9 | 8.3333 |
| mean_reward_by_tenth | dmab:10 | 0.0220 |
| restarts_share_by_tenth | dmab:10 | 9.4241 |
| restarts_after_first_third | dmab | 59.2714 |
