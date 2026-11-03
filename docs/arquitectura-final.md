# Arquitectura del proyecto: evolución guiada por D-MAB

## Pregunta y contribución

¿En qué condiciones la selección adaptativa de movimientos mediante D-MAB
mejora la calidad, el tiempo o la robustez de Tabu Search frente a elegir los
mismos movimientos uniformemente?

La contribución consiste en adaptar, implementar y evaluar selección online
de movimientos en el caso de programación quirúrgica del curso. Se estudia
una hipótesis de mejora; los pilotos no demuestran una superioridad general
del aprendizaje con igual presupuesto.

## Ubicación en la taxonomía ML → MH

La propuesta se ubica en **evolución: selección de operadores y generación
de vecinos**. En este contexto, evolución es la etapa iterativa en que una
metaheurística transforma soluciones; no implica que Tabu sea un algoritmo
evolutivo genético.

D-MAB aprende qué tipo de movimiento proponer. Tabu elige después el mejor
vecino admisible de un lote y mantiene su memoria. La función objetivo se
calcula con el planificador estricto, sin un modelo sustituto. La asignación
de personal y la reparación son reglas del planificador. La cartera externa
tiene reparto fijo y selección final determinista.

## Componentes y responsabilidades

| Componente | Función y estado |
|---|---|
| Tabu Search (MH) | Explora secuencias y salas; mantiene solución local, mejor global, memoria tabú y archivo de treinta soluciones. |
| D-MAB (ML) | Selecciona uno de cinco movimientos antes de cada propuesta; actualiza recompensas online con UCB1 escalado y Page–Hinkley. |
| Planificador y reparación | Asigna personal elegible, construye horarios y comprueba restricciones estrictas. Puede modificar el orden y las salas propuestas. |
| Datos | Doce instancias YAML sintéticas del catálogo oficial, con duraciones, recursos, elegibilidad, preparación, transición, limpieza y espera máxima. |
| Orquestación | Ejecuta dos caminos independientes de 3.030 evaluaciones y devuelve el mejor calendario factible; presupuesto total 6.060. |

Los cinco movimientos son `swap`, `insert`, `room_1`, `room_2` y
`room_pair`: intercambio, inserción, cambio de sala de anestesia, de cirugía
o de ambas. D-MAB decide el tipo; una regla aleatoria selecciona pacientes y
salas concretas. Con probabilidad 0,65 se prioriza uno de los tres pacientes
con más espera cuando existen pacientes bloqueados.

## Flujo de una corrida

1. Leer y validar la instancia. Sus datos permanecen fijos durante la corrida.
2. Inicializar cada camino con treinta soluciones: FIFO, SPT, LPT y
   veintisiete alternativas aleatorias, usando la misma semilla. La reparación
   puede cambiar las preferencias iniciales.
3. En cada camino, partir de la mejor solución inicial y generar lotes de
   hasta quince candidatos distintos.
4. En el camino uniforme, muestrear el movimiento uniformemente. En el
   camino aprendido, consultarlo a D-MAB antes de proponer cada candidato.
5. Reparar el candidato, evaluar el horario con restricciones estrictas y,
   en D-MAB, actualizar la recompensa. Los duplicados reciben recompensa cero
   y no consumen otra evaluación estricta.
6. Elegir el vecino de menor objetivo entre los admisibles. La aspiración
   admite un vecino tabú si mejora el mejor global. Si todos son tabú, la
   implementación actual utiliza el mejor del lote como salida de respaldo.
7. Actualizar memoria, archivo y mejor solución. Se admiten retrocesos del
   objetivo local para explorar; el mejor global se conserva.
8. Detener cada camino al alcanzar 3.030 evaluaciones, incluidas sus treinta
   iniciales. Revalidar ambas mejores soluciones y devolver la de menor
   objetivo combinado; se desempata por makespan y, si también coincide,
   se conserva Tabu uniforme.

La ejecución de referencia es secuencial, con estados y generadores
independientes. La misma semilla comparte el inicio, pero las trayectorias
posteriores pueden divergir: distintos movimientos consumen distintos números
aleatorios. No se atribuye a las pruebas una paralelización interna de la
cartera que no se haya medido.

## Ejecutar la cartera elegida

Desde la raíz del repositorio, después de instalar el proyecto:

```bash
.venv/bin/python -m surgery_optim.portfolio \
  --instance instances/standard/HOSP-STD-30-01.yaml \
  --seed 60 --budget 6060 \
  --output outputs/final/HOSP-STD-30-01-seed60.json
```

La API correspondiente es:

```python
from surgery_optim.instances import load_instance
from surgery_optim.portfolio import run_portfolio

context = load_instance("instances/standard/HOSP-STD-30-01.yaml")
result = run_portfolio(context, seed=60, budget=6060)
```

El resultado incluye los dos componentes, el calendario elegido, su calidad,
presupuesto y tiempos. El presupuesto cuenta las evaluaciones de búsqueda;
las comprobaciones finales de factibilidad se realizan adicionalmente y su
tiempo queda incluido en la medición de ejecución.

## Aprendizaje online y tareas offline

**Offline:** leer la literatura, validar datos, calibrar parámetros con
semillas exploratorias, fijar pesos del objetivo, presupuesto y protocolo.
Los parámetros vigentes son `C=0,1`, `delta=0,01` y `lambda=1` para D-MAB;
memoria de siete soluciones y quince candidatos por lote para Tabu.

**Online:** D-MAB empieza con estimaciones vacías en cada corrida, prueba los
cinco movimientos y actualiza sus recompensas. La recompensa es la mejora
positiva del candidato respecto del valor local anterior al lote,
normalizada por `max(1, 0,02 × objetivo inicial)` y limitada a `[0,1]`.
Se evalúan también candidatos no seleccionados finalmente por Tabu.

UCB1 balancea explotación y exploración. Page–Hinkley detecta caídas en la
recompensa de un movimiento y reinicia las estimaciones de todos los brazos;
mantiene intactos el horario, la memoria y el archivo de Tabu. D-MAB no recibe
metacaracterísticas contextuales, etiquetas de óptimo local ni resultados
futuros de caminos no ejecutados.

## Protección y límites del modelo

La selección final conserva el objetivo del Tabu uniforme de 3.030 de la
misma semilla. Esta propiedad cuesta el doble de evaluaciones y no garantiza
superar a Tabu prolongado con 6.060. Tampoco protege cada métrica individual:
un menor objetivo combinado puede acompañarse de mayor makespan o espera.

El personal se asigna de forma constructiva; no se exploran todas sus
asignaciones. La reparación puede alterar un movimiento y limita los horarios
que la búsqueda alcanza. La espera se mide desde el término de anestesia
incluida su limpieza; el planificador reserva al anestesista hasta el inicio
de cirugía y al cirujano hasta el fin de limpieza quirúrgica. Estos supuestos
se mantienen explícitos y requieren revisión para una aplicación hospitalaria.

El flujo actual resuelve una instancia estática. Replanificación por
cancelaciones o urgencias, fijación de cirugías en curso y aprendizaje entre
jornadas son extensiones pendientes, sin resultados atribuidos al prototipo.

## Evaluación del semestre

- Controles de igual presupuesto: Tabu prolongado de 6.060 y dos Tabu
  uniformes independientes de 3.030.
- Comparación del aprendizaje interno: Tabu uniforme, Tabu+D-MAB y
  Tabu+UCB1 sin Page–Hinkley bajo igual presupuesto por política.
- Referencias constructivas: FIFO, SPT y LPT, que también forman parte de la
  inicialización común.
- Métricas: objetivo combinado, makespan, espera total y máxima, factibilidad,
  tiempo, dispersión entre semillas y proporción de candidatos reparados.
- Ampliación prevista: tamaños y congestión mayores; comparar por separado
  con igual número de evaluaciones y con igual límite de tiempo.
- Análisis: diferencias emparejadas, incertidumbre agrupada por instancia y
  corrección de comparaciones múltiples; distinguir pruebas exploratorias de
  validación y nuevas semillas de instancias realmente nuevas.

LinUCB queda documentado en el [protocolo histórico de
carteras](protocolo-carteras.md) y sus [resultados](../experiments/results/portfolios_60_79/DECISION.md).
No forma parte del flujo seleccionado: no mostró una ventaja suficiente para
justificar un segundo controlador en el piloto.
