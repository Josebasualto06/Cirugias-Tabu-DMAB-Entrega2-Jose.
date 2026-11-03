# Archivo de resultados exploratorios anteriores

Estos CSV se copiaron **sin alterar** desde la carpeta de trabajo local
`OII464_Hospitales-main/experiments/results/tabu_operators_no_balance_20/`.
No proceden directamente del repositorio oficial del profesor. Usaron las 12
instancias estándar, semillas 0–19 y 3.030 evaluaciones. `legacy_mixed` es la
política uniforme equivalente a `uniform` en el código nuevo;
`candidate_runs.csv` incluye D-MAB y LinUCB, pero este proyecto final estudia
D-MAB y la ablación UCB1 sin Page–Hinkley. Las rutas del manifiesto original
son relativas a la antigua copia de trabajo; para reproducir el estudio
**nuevo** se usa `../validation_40_59/manifest.json` y el código de este
repositorio.

Estos resultados se usaron para escoger la arquitectura. Por ese motivo son
**exploratorios**: no se agregan a los CSV de validación ni se utilizan para
elevar artificialmente el número de semillas de confirmación.
