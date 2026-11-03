# Metodología y protocolo experimental

## Propuesta vigente, pregunta e hipótesis

Se estudia si la selección adaptativa de movimientos **dentro de Tabu Search**
mejora la calidad, el tiempo o la robustez de la programación de cirugías
frente a elegir movimientos de manera
uniforme, bajo la misma representación, decodificador, función objetivo,
inicialización y presupuesto. La hipótesis de mejora es falsable: si el
controlador no reduce consistentemente el objetivo con las semillas nuevas,
el estudio no sostendrá esa ventaja. D-MAB es aprendizaje **en línea**, sin
entrenamiento previo ni metacaracterísticas contextuales.

La arquitectura seleccionada es una **cartera fija de Tabu uniforme y Tabu
con D-MAB**: 3.030 evaluaciones por camino, incluidas sus treinta soluciones
iniciales, y 6.060 en total. Se conserva la solución factible de menor
objetivo. El aprendizaje está en la **fase de evolución**, seleccionando el
movimiento que genera cada vecino dentro del segundo camino. El reparto del
presupuesto y la comparación final son deterministas. LinUCB permanece como
alternativa experimental archivada; no integra la arquitectura elegida.

La [arquitectura completa](arquitectura-final.md) fija responsabilidades,
flujo y límites del prototipo. Este documento separa esa propuesta de los
protocolos históricos que originaron los resultados ya archivados.

## Datos y alcance

El conjunto de validación contiene 12 instancias **completamente sintéticas**
`HOSP-STD-{15,20,25,30}-{01,02,03}.yaml`, de 15 a 30 cirugías. Cada
instancia declara salas, personal elegible, duración, preparación, transición,
limpieza y espera máxima para dos etapas: anestesia y cirugía. Se preserva el
`digest` del documento y se calcula SHA-256 del archivo en el manifiesto. Las
instancias YAML coinciden con el catálogo del repositorio oficial del caso; no
se afirma que sean los cuatro JSON originales mencionados en la presentación.
Son **las mismas doce instancias** del estudio exploratorio anterior; lo nuevo
son las semillas (20–39 en la configuración inicial, 40–59 en la versión 2
y 60–79 en el estudio de carteras). Esto prueba sensibilidad a la aleatoriedad
de la
búsqueda dentro del catálogo ya observado, no generalización a instancias
hospitalarias no vistas.

El repositorio oficial del caso se utilizó como **fuente de datos y contexto**:
<https://github.com/Saicooh/OII464_Hospitales>. Se trabajó sobre una copia
local independiente. Este proyecto no escribe en el repositorio oficial.
El commit `ecd30e3dbc1962d856c09b3470d1870c3b139a9a` fue el HEAD oficial
comprobado durante los pilotos; se verificó la igualdad de las doce
instancias estándar con ese commit. El manifiesto guarda además los hashes
de los archivos concretos usados aquí. Antes de la búsqueda se valida el
esquema, identificadores, dimensiones, duraciones y elegibilidad. D-MAB no
consume metacaracterísticas de la instancia: aprende solo de las recompensas
de los cinco movimientos.

## Representación, factibilidad y objetivo

Una solución es una permutación de cirugías y dos asignaciones de sala por
cirugía. Se permiten salas distintas para anestesia y cirugía. No se fuerza el
equilibrio de uso de salas. Una codificación de tres claves reales por cirugía
sirve para generar y reparar soluciones, pero el algoritmo Tabu opera sobre
la solución discreta decodificada.

La reparación puede cambiar tanto las salas como el orden propuesto. El
personal se asigna por una regla de disponibilidad; no forma parte de los
cinco movimientos. Por tanto, el método explora un subconjunto de horarios
construidos por este planificador y no todas las programaciones factibles
del problema general.

El planificador estricto asigna personal elegible, respeta disponibilidad de
salas y personal y **rechaza cualquier espera entre anestesia y cirugía que
supere `max_wait`** de la operación, con una única tolerancia numérica
`WAIT_TOLERANCE = 1e-9` compartida por planificador, decodificador, reglas
constructivas y función objetivo. Mientras una cirugía espera transferirse,
la sala de anestesia queda ocupada; si ambas etapas usan la misma sala, ésta
permanece ocupada durante cirugía y limpieza. Una propuesta no factible recibe
infinito y no puede ser la mejor solución. Los resultados guardados vuelven a
validarse con el planificador estricto.

Se minimiza

\[
f(S)=C_{\max}+10^{-6}\sum_{o\in S} t_o^{\mathrm{inicio}}
     +0{,}5\sum_j w_j+1{,}4\max_j w_j,
\]

donde `S` es el calendario; `f(S)`, el objetivo combinado; `Cmax`, el tiempo
de término de la última operación incluida su limpieza; `o`, una operación;
`t_o` de inicio, el comienzo de preparación o reserva; `j`, un paciente; y `w_j`, el
intervalo entre el fin de anestesia (incluida limpieza) y el inicio del
procedimiento quirúrgico (después de preparación o transición). Todos los
tiempos se expresan en minutos; los coeficientes son pesos fijos del
objetivo. **Supuesto de
modelado:** la limpieza de anestesia se cuenta dentro de la etapa, de modo
que la espera bloqueante se mide desde que esa etapa termina por completo; si
el grupo considera que la limpieza ocurre después del traslado, `w_j` debería
medirse desde el fin del procedimiento anestésico (`processing_end`). La
reserva del anestesista dura hasta el inicio de cirugía y la del cirujano
hasta el fin de limpieza quirúrgica; no se presenta este supuesto como una
descripción universal del trabajo clínico. Además,
el validador exige hoy que toda operación admita todas las salas
(`all_rooms_policy`), por lo que la elegibilidad de salas no restringe nada en
este catálogo. `Cmax`, la suma
de esperas y la espera máxima se reportan por separado. El pequeño término de
inicios usa `ScheduleEntry.start`, es decir, el inicio de preparación o reserva
del recurso para cada operación, y desempata soluciones cercanas. **No hay
penalización por desequilibrio
entre salas.** El objetivo combinado es la métrica primaria fijada antes de la
validación. El makespan y el bloqueo son métricas secundarias; no se interpreta
un descenso del objetivo como descenso automático de cada componente.

## Selección de movimientos dentro de cada trayectoria

Las tres políticas comparadas comparten el mismo Tabu Search y cinco
movimientos discretos:

1. `swap`: intercambiar dos pacientes en la secuencia.
2. `insert`: sacar un paciente e insertarlo en otra posición.
3. `room_1`: cambiar su sala de anestesia.
4. `room_2`: cambiar su sala de cirugía.
5. `room_pair`: cambiar ambas salas.

La selección del paciente prioriza, con probabilidad 0,65, a uno de los tres
con mayor espera actual, cuando los hay. El resto se elige del conjunto de
pacientes. Se generan 15 candidatos distintos por lote.

La **memoria tabú** guarda las 7 últimas soluciones completas aceptadas; una
solución tabú se admite si mejora el mejor valor global (aspiración). Si
todos los candidatos del lote son tabú, el código utiliza el mejor del lote
como salida de respaldo. Con 15
vecinos aleatorios por iteración, repetir una solución exacta es poco
probable, así que esta memoria restringe poco la búsqueda. Se probó una
memoria por atributo (el paciente movido queda tabú 7 iteraciones,
`tabu_memory="attribute"`), pero en la calibración empeoró a Tabu uniforme
en 3,5 unidades del objetivo de media, por lo que se mantiene la memoria de
soluciones de la configuración inicial
(ver `experiments/results/calibration_0_5/CALIBRATION.md`).

La búsqueda mantiene además un **archivo poblacional**: la inicialización
coloca FIFO, SPT y LPT en las primeras tres posiciones y genera otras 27 por
claves aleatorias; Tabu parte de la mejor de las 30, cada candidato aceptado
reemplaza a la peor solución archivada y la solución local salta a la mejor
del archivo cuando ésta mejora el incumbente. En sentido estricto se trata de
un Tabu asistido por población, y así debe describirse.

| Política | Selección de cada propuesta |
|---|---|
| Tabu mixto (`uniform`) | Muestra cada uno de los cinco movimientos con probabilidad uniforme. |
| Tabu + D-MAB (`dmab`) | Usa UCB1 escalado (`media + C·√(2 ln t / n)`) para seleccionar movimiento y Page–Hinkley para reiniciar estimaciones tras caída de recompensa. |
| Tabu + UCB1 (`ucb`) | Usa el mismo UCB1 escalado sin reinicio Page–Hinkley: ablación del componente dinámico. |

En el índice UCB1, `media` es la recompensa promedio del movimiento, `C` el
peso de exploración, `t` el total de observaciones desde el reinicio y `n`
las observaciones del movimiento. Primero se prueba cada movimiento; luego
se elige el de mayor índice. La memoria tabú controla admisión y el bandido
controla generación: son funciones distintas.

**Escala de exploración C.** El D-MAB original de Da Costa et al. (2008)
multiplica el término de exploración por un factor C. La configuración inicial
archivada usaba
C = 1; como la recompensa media observada es del orden de 0,02 y el término
de exploración ronda 0,16 tras unas 600 elecciones por brazo, la exploración
dominaba y los cinco movimientos se elegían casi por turnos. En la versión 2,
C y el umbral λ de Page–Hinkley se calibran en las semillas exploratorias
0–5 (`experiments/calibrate.py`, resultados en
`experiments/results/calibration_0_5/`) y se fijan **antes** de la validación.

**Semillas y flujo aleatorio.** En la versión 2 todas las políticas extraen
del generador el paciente objetivo y un movimiento uniforme; los
controladores reemplazan ese movimiento por el elegido. La inicialización
comparte la semilla y estas extracciones, pero los distintos movimientos
consumen distintas cantidades de números aleatorios, de modo que no se
garantizan trayectorias sincronizadas. En la configuración inicial los
controladores no extraían el
movimiento uniforme, por lo que sus flujos divergían tras la población
inicial.

**Movimientos reparados.** El decodificador puede deshacer parte de un
movimiento para respetar `max_wait`. `runs.csv` registra en
`repaired_candidates` cuántos candidatos evaluados difieren de la propuesta
original; en esos casos la recompensa se atribuye a un movimiento que no se
aplicó tal cual.

La recompensa para un candidato es la mejora positiva respecto del valor local
antes del lote, dividida por `max(1, 0,02 × objetivo inicial)` y truncada en
`[0,1]`. Un candidato duplicado entrega recompensa cero: se mantiene así
porque, si los duplicados no actualizaran el bandido, UCB (que es
determinista) volvería a elegir el mismo brazo hasta agotar los intentos del
lote. La recompensa se
actualiza después de cada propuesta evaluada, aunque el candidato no sea
elegido después por Tabu. D-MAB es un bandido no
contextual: no recibe el tamaño de la instancia, el historial de estancamiento
ni una etiqueta de óptimo local. Page–Hinkley reinicia **sus estadísticas**,
no la solución ni la búsqueda Tabu.

## Evaluación de la arquitectura seleccionada

La cartera se compara principalmente con **Tabu prolongado de 6.060** y
**dos Tabu uniformes independientes de 3.030**. Cada alternativa usa 6.060
evaluaciones de búsqueda, con inicializaciones incluidas. Esto distingue el
aporte del aprendizaje del cómputo adicional y de la diversidad por
reinicios. Tabu de 3.030 se conserva como referencia de menor presupuesto:
la cartera protege su objetivo de la misma semilla, pero no garantiza
superar al control de 6.060 ni mejorar cada métrica por separado.

El criterio de parada vigente es agotar las 3.030 evaluaciones por camino.
La ejecución implementada es secuencial. El presupuesto cuenta las llamadas
de evaluación de búsqueda; reparación, construcción, propuestas duplicadas,
selección y comprobaciones finales también consumen tiempo y se incluyen en
la duración medida. Las 6.060 no representan todos los accesos internos al
planificador ni 6.060 ejecuciones independientes del algoritmo.

El estudio de carteras 60–79 fija umbral descriptivo 0,25 del objetivo,
bootstrap jerárquico de instancias y semillas emparejadas y Wilcoxon sobre
doce medias por instancia, con Holm para cuatro comparaciones de igual
presupuesto. El [protocolo de carteras](protocolo-carteras.md) conserva los
detalles de LinUCB y las variantes evaluadas. Los intervalos incluyen cero;
la propuesta sigue siendo una hipótesis de investigación.

Durante el semestre se ampliarán tamaños y congestión. Se medirán por
separado resultados con igual número de evaluaciones y con igual límite de
tiempo. Se conservarán FIFO, SPT y LPT como referencias constructivas, y la
comparación uniforme/D-MAB/UCB1 sin Page–Hinkley como ablación del aprendizaje
interno. Calibración y selección de arquitectura serán exploratorias; una
validación con instancias realmente nuevas se distinguirá de repetir
semillas en el catálogo ya conocido.

## Protocolos históricos de 3.030 evaluaciones

Las tres políticas usan 3.030 evaluaciones por corrida, **incluidas las 30
iniciales**. La versión 2 se valida con las mismas instancias y semillas
enteras 40–59. Las semillas 0–19 (exploratorias; 0–5 usadas para calibrar)
y 20–39 (validación de la configuración inicial) se mantienen separadas y no se mezclan
en la tabla de validación. Para una pareja instancia-semilla se
comprueba que las tres políticas tienen el mismo objetivo inicial. También se
verifica que se usen exactamente 3.030 evaluaciones factibles.

Los candidatos duplicados se descartan dentro de cada lote y no consumen una
evaluación del planificador, aunque sí cuestan trabajo de generación y pueden
actualizar el bandido con recompensa cero. Por eso el presupuesto iguala
evaluaciones estrictas, no necesariamente intentos de propuesta ni segundos
de CPU. Desde la versión 2 `runs.csv` registra intentos y evaluaciones por
movimiento para las tres políticas (en la configuración inicial la política uniforme los
dejaba en cero). Los duplicados de D-MAB/UCB1 actualizan el bandido con cero;
en Tabu uniforme no hay modelo que actualizar. Esta asimetría es parte de la
definición operativa de los controladores, no una evaluación adicional.

FIFO, SPT y LPT se calculan una vez por instancia como reglas clásicas de
referencia. Para cada algoritmo y cada instancia se reportan la mediana entre
20 semillas, mínimo y máximo del objetivo, mediana de makespan, bloqueo y
tiempo. La comparación principal utiliza diferencias **emparejadas** por
instancia y semilla (`alternativa − Tabu mixto`); valor negativo favorece al
controlador. Se muestran victorias, empates y derrotas con tolerancia `1e−9`.
La comparación con UCB1 ayuda a atribuir el efecto del reinicio dinámico.

**Pruebas estadísticas.** Desde la versión 2 se aplica la prueba de rangos con
signo de Wilcoxon, bilateral, a las diferencias emparejadas del objetivo
(`zero_method="zsplit"` para repartir los empates). En ese protocolo hay dos
familias con
corrección de Holm: las tres comparaciones globales (D-MAB vs uniforme,
UCB1 vs uniforme, D-MAB vs UCB1, 240 pares cada una) y las 36 comparaciones
por instancia (20 pares cada una). Los resultados están en `statistics.csv`.
Como las semillas de una misma instancia no son independientes entre
instancias, la prueba global debe leerse junto con el signo de las doce
diferencias por instancia.

Se evita agregar todas las corridas como si fueran instancias independientes:
las tres réplicas de cada tamaño son distintas, pero las veinte semillas de
una réplica comparten datos. Cualquier conclusión general debe considerar
este agrupamiento, el tamaño reducido del catálogo y que las instancias ya
influyeron en la elección de la arquitectura antes de esta validación.

## Reproducibilidad y procedencia del código

El código independiente del repositorio reutiliza y adapta las ideas y partes
de implementación de la copia de trabajo exploratoria de este proyecto:

| Módulo nuevo | Procedencia local |
|---|---|
| `model.py`, `instances.py` | `data/instance_model.py`, `data/instance_loader.py` |
| `scheduler.py` | Núcleo estricto de `simulation/scheduler.py` |
| `baselines.py` | `algorithms/constructive_baselines.py` |
| `encoding.py` | Decodificación de `algorithms/mh.py` y `algorithms/gwo_eyeing_comparison.py`; codificación de `algorithms/gwo_tabu_comparison.py` |
| `objective.py` | Agregación de `algorithms/mh.py`, sin término de equilibrio |
| `bandit.py` | D-MAB de `algorithms/gwo_eyeing_comparison.py` |
| `tabu.py` | Movimientos y búsqueda de `algorithms/gwo_tabu_comparison.py` y `algorithms/tabu_candidate_selection.py` |

La copia exploratoria está separada del repositorio oficial del profesor. Se
comprobaron 24 corridas antiguas (4 tamaños × 3 semillas × 2 políticas): el
valor inicial, objetivo final, makespan y esperas total/máxima coincidieron
numéricamente con los CSV anteriores. Cada estudio contiene hashes del código
para identificar la versión exacta.

### Archivo 20–39: revisión histórica y motor actual

La revisión histórica
`8ce37bcb834c3efd8fcca480e4ce1dbb3de2cf6f` (`8ce37bc`) existe en el
historial de `origin/main`. Se comprobó que sus nueve archivos de código
coinciden con los hashes de `validation_20_39/manifest.json`. Por tanto, es
la referencia concreta para reproducir el estudio completo de 720 corridas
con su motor original. En una **copia aislada situada en esa revisión**, se
instalan sus dependencias y se ejecuta:

```bash
python -m experiments.run_study --seed-start 20 --seed-count 20 \
  --budget 3030 --output outputs/reproduccion_20_39
python -m experiments.verify_results outputs/reproduccion_20_39
```

La carpeta nueva preserva la evidencia archivada. Para comparar con ella se
usan los valores de calidad, presupuesto y datos; los tiempos de ejecución
dependen del equipo y de la carga del sistema. El manifiesto histórico
declara versiones de Python, NumPy y demás dependencias para identificar el
entorno original.

El código actual cambió respecto de ese motor, por lo que
`experiments.verify_results experiments/results/validation_20_39` falla en
la comprobación de hashes. Esa negativa identifica una diferencia de versión;
no invalida por sí sola las métricas archivadas. **Ejecutar el script actual
`run_study` con `--seed-start 20` no reproduce el protocolo antiguo**: usa
por defecto `C=0,1`, `lambda=1` y la política aleatoria de la versión 2.

El motor actual ofrece otra vía, que no es una reproducción del código
original: `TabuConfig.from_manifest` restaura los parámetros antiguos
(`C=1`, `lambda=0,35`, memoria de soluciones y
`common_random_numbers=False`), y `experiments.audit_replay` compara las
corridas recalculadas con los CSV. La muestra de **semilla 20** tiene 36
corridas, doce instancias por tres políticas; sus valores de inicio,
objetivo, makespan y espera coinciden dentro de `1e-9`, con el presupuesto
completo y calendarios estrictos reconstruidos. No se presenta esa muestra
como una nueva auditoría de las 720 corridas.

La evidencia está en `validation_20_39/replay_seed_20.csv` y su manifiesto.
Para repetir el comprobador conservando el archivo original, se copia ese
directorio a una carpeta de trabajo y se pasa su ruta mediante `--directory`:

```bash
python -m experiments.audit_replay \
  --directory ruta/a/copia/validation_20_39 --seed 20
```

El comando genera `replay_seed_20.csv` y su manifiesto en la copia. Los CSV
históricos permiten auditar cobertura y cálculos de resúmenes; no contienen
todos los calendarios finales, por lo que su factibilidad no puede
reconstruirse únicamente leyendo `runs.csv`.

Para ejecutar la arquitectura vigente desde la raíz del repositorio:

```bash
python -m venv .venv
.venv/bin/python -m pip install -e '.[test]'
.venv/bin/python -m pytest -q
.venv/bin/python -m surgery_optim.portfolio \
  --instance instances/standard/HOSP-STD-30-01.yaml \
  --seed 60 --budget 6060 \
  --output outputs/final/HOSP-STD-30-01-seed60.json
```

`surgery_optim.portfolio.run_portfolio(context, seed=60, budget=6060)`
ofrece la misma ejecución mediante API. El JSON conserva componentes y
calendario final. Los scripts de estudios históricos guardan `runs.csv` tras
cada corrida y permiten reanudar solo sin cambios en configuración, semillas,
instancias o código. Para reproducir resultados archivados debe usarse la
revisión de su manifiesto; al cambiar los archivos de código incluidos en
sus hashes, datos o configuración se utiliza una carpeta nueva de salida,
sin sobrescribir evidencia histórica. Los
comandos de cada etapa están en la [guía de experimentos](../experiments/README.md).

`runs.csv` conserva métricas, no el calendario final de cada corrida. Por
ello `experiments.verify_results` audita cobertura, presupuesto, hashes y
resúmenes, pero **no puede reconstruir `max_wait` desde el CSV**. La
factibilidad procede del planificador estricto en cada evaluación, de la
revalidación de la mejor solución antes de devolverla y de las pruebas que
comprueban un incumplimiento artificial y la reproducibilidad de una corrida.
Además, `experiments.audit_replay` vuelve a ejecutar la semilla 40 en las
doce instancias y tres políticas, compara objetivo, makespan y bloqueo con
`runs.csv`, y reconstruye los 36 calendarios para verificar elegibilidad y
holgura no negativa frente a `max_wait`.
