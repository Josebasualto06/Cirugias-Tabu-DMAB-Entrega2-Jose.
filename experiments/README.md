# Experimentos reproducibles

## Arquitectura vigente y ejecución individual

La propuesta elegida combina Tabu uniforme con Tabu+D-MAB en una **cartera
fija**: 3.030 evaluaciones por camino, incluidas inicializaciones, y 6.060 en
total. Se devuelve el mejor calendario factible. D-MAB aprende a seleccionar
movimientos en la fase de evolución de Tabu; el reparto y la comparación
final son deterministas. LinUCB permanece como alternativa experimental
archivada.

```bash
python -m surgery_optim.portfolio \
  --instance instances/standard/HOSP-STD-30-01.yaml \
  --seed 60 --budget 6060 \
  --output outputs/final/HOSP-STD-30-01-seed60.json
```

El JSON conserva ambos componentes, calendario elegido, calidad, evaluaciones
y tiempos. El comando ejecuta los caminos secuencialmente. La API equivalente
es `from surgery_optim.portfolio import run_portfolio` y
`run_portfolio(context, seed=60, budget=6060)`.

La [arquitectura](../docs/arquitectura-final.md) y la
[metodología](../docs/metodologia-experimental.md) explican representación,
reparación, restricciones y límites de interpretación. Ninguno de los pilotos
demuestra una superioridad general del aprendizaje con igual presupuesto.

## Estudio de selección de arquitectura: carteras, semillas 60–79

```bash
python -m experiments.compare_portfolios --workers 4
python -m experiments.verify_portfolios
python -m experiments.plot_portfolios
python -m experiments.analyze_portfolio_learning
```

El [protocolo de carteras](../docs/protocolo-carteras.md) fija métodos y
parámetros antes de evaluar doce instancias con veinte semillas por instancia.
Todas las alternativas principales reciben 6.060 evaluaciones; las
referencias de 3.030 están identificadas. Se comparan Tabu prolongado, dos Tabu
uniformes independientes, la cartera fija y dos repartos aprendidos con
LinUCB por bloques de 150 evaluaciones.

[`results/portfolios_60_79/`](results/portfolios_60_79/) contiene:

- `runs.csv`: métricas de siete alternativas por pareja instancia–semilla.
- `summary.csv` e `instances_summary.csv`: resúmenes generales y por instancia.
- `supplemental.csv`: comparación con las referencias de menor presupuesto.
- `solutions.jsonl`: todas las soluciones finales para recalcular factibilidad.
- `decisions.csv`: decisiones de las alternativas LinUCB, no de la cartera fija.
- `manifest.json`: parámetros, entorno, semillas y hashes de código/datos.
- `verification.json`: auditoría de soluciones, aprendizaje y presupuestos.
- `comparison.png`/`.svg`: diferencias con incertidumbre agrupada por instancia.
- `ANALYSIS.md`: comparación principal de igual presupuesto.
- `LEARNING.md` y `learning_added_value.csv`: contrastes secundarios exploratorios.
- `DECISION.md`: selección de la cartera fija y límites de la evidencia.

La comparación utiliza instancias como unidades y distingue la mejora frente
al Tabu de 3.030 de la mejora frente al de 6.060. El estudio reutiliza
prefijos para ahorrar cómputo: ejecuta cinco trayectorias y presenta siete
alternativas por pareja; los resultados no son independientes entre sí.
Los tiempos de carteras fijas son sumas de sus componentes medidos con cuatro
tareas del estudio concurrentes. No representan una prueba de paralelización
interna de las dos trayectorias.

El respaldo protege el objetivo del Tabu uniforme de 3.030 de la misma
semilla. No garantiza superar a Tabu prolongado ni mejorar cada métrica por
separado. Dos Tabu independientes se conserva como control del efecto de
repetir la búsqueda; UCB1 sin Page–Hinkley será la ablación del aprendizaje
interno.

## Comparación histórica de políticas: versión 2, semillas 40–59

```bash
python -m experiments.calibrate --workers 2        # opcional: semillas 0–5
python -m experiments.run_study --seed-start 40 --seed-count 20
python -m experiments.verify_results
python -m experiments.analyze_ablation
python -m experiments.finalize_analysis
python -m experiments.plot_paired_differences
python -m experiments.plot_convergence --seed 40
python -m experiments.audit_replay --seed 40
```

`experiments.calibrate` fija C y λ usando semillas exploratorias 0–5; su
resultado está en
[`results/calibration_0_5/CALIBRATION.md`](results/calibration_0_5/CALIBRATION.md).
`experiments.run_study` ejecuta `uniform`, `dmab` y `ucb` en las doce
instancias con veinte semillas nuevas (40–59) y **3.030 evaluaciones por
política**, incluido el inicio común de treinta soluciones. Calcula también
FIFO, SPT y LPT. Guarda cada fila de `runs.csv` y puede reanudarse con los
mismos argumentos. `experiments.verify_results` comprueba hashes, cobertura,
valor inicial y presupuesto; no reconstruye horarios desde ese CSV.

El directorio [`results/validation_40_59/`](results/validation_40_59/) contiene:

- `manifest.json`: protocolo, entorno, parámetros y hashes.
- `baselines.csv`, `runs.csv`, `summary.csv` y `paired.csv`: referencias,
  corridas, resúmenes y diferencias por instancia.
- `statistics.csv`: Wilcoxon emparejado y Holm para las familias históricas
  global y por instancia; no se combina con el análisis del estudio 60–79.
- `comparison.png`/`.pdf`: medianas por tamaño y réplica.
- `ANALYSIS.md`, `ABLATION.md` y `ablation_dmab_vs_ucb.csv`: resultados y
  comparación del reinicio dinámico.
- `paired_differences.png`: veinte diferencias por instancia, mediana y rango
  intercuartílico.
- `convergence.png` y `convergence_trace.csv`: ejemplo de semilla 40 y réplica
  01; la evidencia utiliza todas las semillas, no solo esas curvas.
- `replay_seed_40.csv`: treinta y seis calendarios reconstruidos y comparados
  con `runs.csv`, incluida la comprobación de espera máxima.

Esta validación motivó estudiar la conservación del resultado de Tabu base;
no constituye una evaluación de la cartera de 6.060.

## Archivos anteriores y reproducibilidad

La configuración inicial (semillas 20–39, C = 1, λ = 0,35) queda archivada en
[`results/validation_20_39/`](results/validation_20_39/README.md). Los
[exploratorios 0–19](results/exploratory_0_19/README.md) también se mantienen
separados. Esos estudios usan la revisión identificada por su manifiesto;
`TabuConfig.entrega1()` conserva sus ajustes de búsqueda.

No se mezclan resultados de versiones, semillas o presupuestos diferentes.
Los nuevos estudios fijan datos, pesos y parámetros antes de evaluar;
calibración y decisión de arquitectura son exploratorias. Semillas nuevas en
las mismas doce instancias no demuestran generalización a hospitales no
vistos.

Los manifiestos impiden reanudar al cambiar configuración o código. Debe
usarse la revisión que produjo cada estudio para reproducirlo exactamente y
una carpeta nueva para una variante, sin modificar evidencia archivada.
El catálogo oficial se conserva y el repositorio del profesor no se modifica.
