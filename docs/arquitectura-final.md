# Arquitectura del proyecto: evolución guiada por D-MAB

## Pregunta y contribución

¿La selección adaptativa de movimientos mediante D-MAB mejora la calidad,
el tiempo o la robustez de Tabu Search frente a elegir los mismos movimientos
uniformemente, con igual presupuesto computacional?

La propuesta adapta y evalúa aprendizaje en línea para la programación
quirúrgica de dos etapas del curso. Su aporte se contrastará experimentalmente;
la arquitectura no garantiza una mejora en cada instancia o semilla.

## Configuraciones vigentes

| Sigla | Experimento | Papel |
|---|---|---|
| **TS-U** | Tabu Search con selección uniforme de los cinco movimientos. | Metaheurística de referencia. |
| **TS-DMAB** | Tabu Search con D-MAB completo: UCB1 escalado y Page-Hinkley. | Diseño híbrido MH + ML. |

Cada algoritmo realiza **una trayectoria de 6.060 evaluaciones**, incluidas
sus treinta soluciones iniciales. Las configuraciones se ejecutan por separado
y cada una devuelve su propio mejor calendario factible. La campaña vigente
no incluye una cartera externa, dos reinicios ni una ablación sin detector.

## Ubicación en la taxonomía ML a MH

El aprendizaje actúa en **evolución: selección de operadores y generación
de vecinos**. Evolución describe aquí la transformación iterativa de soluciones;
Tabu Search no se convierte en un algoritmo genético.

D-MAB aprende qué tipo de movimiento proponer; Tabu elige el vecino admisible
y conserva su memoria. La función objetivo usa el planificador estricto,
sin un modelo sustituto. Personal, reparación y factibilidad se resuelven
mediante reglas comunes a ambas configuraciones.

## Componentes y responsabilidades

| Componente | Función |
|---|---|
| Tabu Search (MH) | Mantiene solución local, mejor global, memoria tabú y archivo de treinta soluciones. |
| D-MAB (ML) | Aprende de recompensas y selecciona uno de cinco movimientos mediante UCB1. |
| Page-Hinkley | Detecta caídas de recompensa y reinicia las estimaciones del bandido; conserva el estado de Tabu. |
| Planificador y reparación | Construye calendarios con personal elegible y restricciones estrictas; puede modificar orden y salas. |
| Datos | Doce instancias sintéticas con duraciones, recursos, elegibilidad, preparación, transición, limpieza y espera máxima. |
| Orquestación | Ejecuta una configuración por corrida, registra sus resultados y aplica el mismo presupuesto a ambos métodos. |

Page-Hinkley es la prueba estadística incorporada al D-MAB de referencia.
El aprendizaje y la selección de movimientos ya están en el mecanismo MAB/UCB1;
el detector permite renovar estimaciones ante cambios de recompensa. No
certifica estancamiento ni identifica directamente un óptimo local.

Los movimientos son `swap`, `insert`, `room_1`, `room_2` y `room_pair`:
intercambio, inserción, cambio de sala de anestesia, cirugía o ambas.
D-MAB decide el tipo; una regla aleatoria elige pacientes y salas concretas.
Con probabilidad 0,65 se prioriza uno de los tres pacientes con mayor espera,
cuando existen pacientes con espera positiva.

## Flujo de una corrida

1. Leer y validar la instancia, fija durante toda la búsqueda.
2. Construir treinta soluciones: FIFO, SPT, LPT y veintisiete alternativas
   aleatorias. Partir de la mejor y conservar el archivo inicial.
3. Generar lotes de hasta quince candidatos distintos. TS-U selecciona
   uniformemente el movimiento; TS-DMAB consulta al controlador.
4. Reparar la propuesta y evaluar el calendario con restricciones estrictas.
   En TS-DMAB, actualizar el bandido con la recompensa del candidato.
5. Elegir el vecino de menor objetivo entre los admisibles. La aspiración
   permite una solución tabú si mejora el mejor global; si todos los vecinos
   son tabú, el motor actual utiliza el mejor del lote como respaldo.
6. Actualizar memoria, archivo y mejor global. Pueden aceptarse retrocesos
   del objetivo local para explorar; se conserva el mejor resultado global.
7. Detenerse al alcanzar 6.060 evaluaciones, incluidas las treinta iniciales.
   Revalidar el mejor calendario y guardar resultados y trazas.

Para cada pareja instancia-semilla se comparte la inicialización. Las
trayectorias posteriores pueden divergir porque distintos movimientos consumen
distintos números aleatorios. No se supone sincronización perfecta de sorteos.

## Aprendizaje y tareas fuera de línea

**Fuera de línea:** revisar literatura, validar datos y fijar objetivo,
presupuesto, parámetros y protocolo. Cualquier calibración posterior utiliza
datos de desarrollo distintos de la evaluación.

**Durante la corrida:** D-MAB empieza con estimaciones vacías, prueba los
movimientos y actualiza sus recompensas. La recompensa es la mejora positiva
respecto del objetivo local antes del lote, dividida por
`max(1, 0,02 × objetivo inicial)` y limitada a `[0,1]`. Los candidatos que
no mejoran reciben cero. También se evalúan candidatos que Tabu no acepta
finalmente; los duplicados sin reevaluación reciben cero sin consumir otra
valoración de objetivo.

UCB1 combina recompensa media y exploración. Page-Hinkley detecta caídas en
la recompensa de un movimiento y reinicia las estadísticas de todos los brazos,
sin cambiar el calendario, la memoria ni el archivo de Tabu. D-MAB no usa
metacaracterísticas contextuales, etiquetas de óptimo local ni resultados futuros.

Se mantienen `C=0,1`, `delta=0,01` y `lambda=1`, memoria de siete soluciones,
quince candidatos por lote y treinta soluciones iniciales. No se calibrarán
con las semillas 80-109 de la campaña prevista.

## Objetivo y límites

Se minimiza `f = Cmax + 1e-6 × suma de inicios + 0,5 × espera total + 1,4 × espera máxima`.
`Cmax` es el término de la última operación incluida limpieza; los inicios
son los de preparación o reserva; las esperas transcurren entre el término
de anestesia incluida limpieza y el inicio del procedimiento quirúrgico.
No se penaliza el desequilibrio entre salas ni se exige usar la misma sala
en ambas etapas. Un menor objetivo no implica mejorar cada componente.

La asignación de personal es constructiva y la reparación restringe los
calendarios alcanzables. El planificador reserva anestesista hasta el inicio
de cirugía y cirujano hasta el fin de limpieza quirúrgica. Estos supuestos
se mantienen explícitos, sin presentarlos como descripción universal de la
práctica clínica. La espera máxima es estricta.

La agenda es estática. Cancelaciones, urgencias, fijación de cirugías en curso
y aprendizaje entre jornadas son extensiones pendientes. No se garantiza
superioridad de TS-DMAB ni optimalidad global.

## Evaluación y reproducibilidad

El [protocolo vigente](../experiments/protocols/entrega2_v2/README.md) fija
12 instancias, 30 repeticiones, semillas 80-109 y dos métodos: 720 registros
principales. El efecto mínimo relevante es 1% del objetivo ponderado.
Se reportan makespan, esperas, factibilidad, tiempo, convergencia y eventos
del controlador. El contraste estudia el controlador completo; los reinicios
registrados no permiten atribuir causalmente un efecto aislado a Page-Hinkley.

La [metodología](metodologia-experimental.md) detalla presupuesto, análisis
y uso de la API. La comparación secundaria asigna diez segundos a cada
algoritmo; su criterio temporal requiere implementación y verificación antes
de ejecutar esa campaña. Los estudios de cartera se preservan en su
[protocolo histórico](protocolo-carteras.md) y
[resultados](../experiments/results/portfolios_60_79/DECISION.md).
