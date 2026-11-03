# Protocolo de comparación de carteras

## Estado y relación con la propuesta

Este protocolo documenta el estudio de semillas 60–79, terminado y archivado
en `experiments/results/portfolios_60_79/`. La arquitectura elegida para el
semestre es la **cartera fija de Tabu uniforme y Tabu con D-MAB**, con 3.030
evaluaciones por camino y selección de la mejor solución factible. Su
implementación está en `surgery_optim.portfolio` y su flujo en
[arquitectura-final.md](arquitectura-final.md).

El ML seleccionado es D-MAB dentro de la trayectoria, aplicado a **evolución:
selección de movimientos y generación de vecinos**. El reparto fijo y el
mínimo final son deterministas. Los métodos LinUCB descritos abajo son
alternativas experimentales; no forman parte de la arquitectura elegida.
Los intervalos agrupados de este estudio incluyeron cero y no se demostró
superioridad general a igual presupuesto. La decisión prioriza sencillez y
conservación de la referencia, manteniendo dos Tabu como control.

## Pregunta

¿Conviene repartir el cómputo entre Tabu mixto y Tabu con D-MAB, o dedicarlo a
Tabu mixto? ¿Aprender ese reparto añade valor frente a ejecutar ambos caminos
con una asignación fija?

## Diseño fijado antes de evaluar

- Datos: doce instancias YAML oficiales `HOSP-STD-{15,20,25,30}-{01,02,03}`.
- Semillas nuevas: 60–79, veinte por instancia; no se ajustan parámetros con
  sus resultados. El catálogo ya se había usado en la selección de arquitectura.
- Base: versión 2, `C=0,1`, `lambda=1`, memoria de siete soluciones, quince
  candidatos por lote, treinta soluciones iniciales y restricciones estrictas.
- Presupuesto principal: 6.060 evaluaciones de búsqueda, incluidas todas las
  inicializaciones y pruebas. Se conserva Tabu de 3.030 como referencia menor.
- Métrica principal: función objetivo existente, sin penalización por equilibrio.
  Se guardan makespan, espera, factibilidad y tiempo por separado.
- Comparaciones de igual presupuesto: cuatro alternativas frente a Tabu de
  6.060. Las diferencias se promedian primero dentro de cada instancia;
  Wilcoxon usa esas doce medias y Holm corrige las cuatro pruebas.
- Incertidumbre: bootstrap jerárquico de instancias y semillas emparejadas.
  Un cambio de hasta 0,25 del objetivo se considera similar descriptivamente.

## Métodos

| Método | Distribución del presupuesto | Aprendizaje |
|---|---|---|
| Tabu prolongado | Un camino uniforme de 6.060 | No |
| Dos reinicios de Tabu | Dos caminos uniformes de 3.030; devolver el mejor | No |
| Cartera fija (elegida) | Tabu uniforme y Tabu con D-MAB de 3.030 cada uno; devolver el mejor | D-MAB dentro de su camino; el reparto es fijo |
| Asignación aprendida (archivada) | LinUCB reparte 6.060 entre los dos caminos | Online por bloques |
| Asignación con respaldo (archivada) | Completar Tabu de 3.030; LinUCB reparte el resto | Online por bloques |

Los dos caminos de la cartera Tabu+D-MAB comienzan con la misma semilla. Cada
uno preserva su estado y memoria; su evolución aleatoria posterior puede
diferir. Dos reinicios uniformes usan `seed` y `seed+1.000.000`, incluidas sus
inicializaciones aleatorias independientes. Esta diferencia se declara para
evaluar el valor de combinar modos frente al valor de diversificar inicios.

## Controlador contextual evaluado como alternativa

LinUCB usa modelos lineales separados para los dos modos, regularización
identidad y exploración `alpha=0,25`. Antes de cada bloque de 150 evaluaciones
observa diez características: constante, tamaño, presupuesto usado,
participación del camino, progreso global, brecha entre camino y mejor global,
brecha local, bloques estancados, progreso de los cinco bloques recientes y
espera normalizada. Todas las entradas proceden del estado ya observado.

La recompensa es la reducción del mejor objetivo global después del bloque,
dividida por `max(1, 0,02 * objetivo inicial)` y limitada a `[0,1]`. Se ejecuta
un bloque de cada modo para comenzar; después se elige el mayor índice de
confianza contextual. Los bloques no seleccionados no se ejecutan ni se
usan como etiquetas futuras. El aprendizaje se reinicia en cada corrida.

La memoria de cada trayectoria permanece intacta al pausarla. El resultado
final es el mejor calendario factible observado en cualquiera de las dos.
LinUCB está descrito en [Li et al. (2010)](https://arxiv.org/abs/1003.0146);
su aplicación a este reparto constituye una adaptación experimental.

## Alcance de la protección

La cartera fija y la asignación con respaldo conservan el resultado completo
del Tabu de 3.030 de la misma semilla. Por construcción su objetivo final no
puede empeorarlo. Esa protección utiliza cómputo adicional y no garantiza
superar a Tabu que dispone de las 6.060 evaluaciones completas.
La protección se refiere al objetivo combinado; no garantiza que cada
componente, como makespan o espera, disminuya individualmente.

Se distingue una mejora por el reparto aprendido de una mejora por repetir
la búsqueda: se incluyen la cartera fija, dos reinicios y Tabu prolongado.
No se exige que cada bloque mejore inmediatamente: ambas trayectorias pueden
aceptar movimientos que empeoran la solución local, conservando la mejor.

La selección de una arquitectura considera reducción media del objetivo,
incertidumbre agrupada, diferencias por instancia y cómputo. Una mejora
consistentemente respaldada requiere evidencia frente a Tabu con igual
presupuesto; una diferencia pequeña cuyo intervalo incluye cero se presenta
como resultado preliminar. El respaldo frente a 3.030 no se usa para afirmar
superioridad frente a 6.060.

Para ahorrar cómputo al ejecutar el estudio se reutiliza el prefijo de 3.030
de Tabu prolongado y se construyen las carteras fijas a partir de los dos
resultados completos. Cada alternativa conserva su presupuesto y tiempo
serial equivalente. Por pareja se ejecutan cinco trayectorias y se informan
siete resultados; no son siete corridas estadísticamente independientes.

## Verificación y reproducción

La implementación experimental de trayectorias se contrasta con `run_tabu`:
pausar no altera resultados ni evaluaciones. Las soluciones finales se
recalculan con el planificador estricto. Se verifican los presupuestos de
cada método y que el respaldo coincide con el Tabu de referencia.

```bash
python -m pytest -q
python -m experiments.compare_portfolios --workers 4
python -m experiments.verify_portfolios
python -m experiments.plot_portfolios
python -m experiments.analyze_portfolio_learning
```

Los resultados y su manifiesto están en
`experiments/results/portfolios_60_79/`. La retrospectiva 40–59 es descriptiva;
no se mezcla con la validación de semillas 60–79.

Para ejecutar solamente la arquitectura elegida:

```bash
python -m surgery_optim.portfolio \
  --instance instances/standard/HOSP-STD-30-01.yaml \
  --seed 60 --budget 6060 \
  --output outputs/final/HOSP-STD-30-01-seed60.json
```

Los archivos de resultados archivados se mantienen intactos. Se exige
coincidencia con sus hashes antes de reanudar; los cambios en una versión
experimental deben usar otra carpeta de resultados.

El estudio mantiene las reglas de personal y limpieza de la versión 2. Los
tiempos se miden con tareas concurrentes y se interpretan descriptivamente;
el presupuesto de evaluaciones es el control principal de cómputo.
El tiempo de la cartera fija en este estudio es la suma de sus dos caminos;
no se midió una ejecución simultánea interna de ambos. Las tareas de
reparación y validación final consumen tiempo además de las evaluaciones
contabilizadas en el presupuesto de búsqueda.
