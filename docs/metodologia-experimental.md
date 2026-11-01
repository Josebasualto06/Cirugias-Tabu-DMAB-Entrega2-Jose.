# Metodología y protocolo experimental

## Diseño vigente

La comparación principal responde si la selección aprendida de movimientos
mejora Tabu Search respecto de su selección uniforme. Se comparten
representación, planificador, función objetivo, movimientos, inicialización
y presupuesto; cambia el mecanismo que selecciona el tipo de movimiento.

| Sigla | Configuración | Presupuesto por corrida |
|---|---|---:|
| **TS-U** | Tabu Search con selección uniforme. | 6.060 evaluaciones |
| **TS-DMAB** | Tabu Search con D-MAB completo: UCB1 escalado y Page-Hinkley. | 6.060 evaluaciones |

Cada método devuelve su propio mejor calendario factible. D-MAB aprende
en línea y no requiere entrenamiento supervisado previo. Page-Hinkley es
una prueba estadística que reinicia las estimaciones del bandido ante una
caída de recompensa; no reinicia Tabu ni certifica un óptimo local.

La [arquitectura](arquitectura-final.md) explica responsabilidades y flujo.
La especificación vigente es el
[protocolo de Entrega 2 v2](../experiments/protocols/entrega2_v2/README.md),
con [parámetros](../experiments/protocols/entrega2_v2/protocolo.json) e
[inventario](../experiments/protocols/entrega2_v2/instancias.csv).
Su campaña está pendiente. La cartera y la variante sin Page-Hinkley
permanecen como estudios históricos, sin formar parte de esta comparación.

## Datos y alcance

Se usan doce instancias completamente sintéticas del repositorio
[OII464_Hospitales](https://github.com/Saicooh/OII464_Hospitales), revisión
`ecd30e3dbc1962d856c09b3470d1870c3b139a9a`:
`HOSP-STD-{15,20,25,30}-{01,02,03}.yaml`. Antes de cada campaña se comprueban
esquema, elegibilidad, unidades y SHA-256 del archivo. La copia oficial no
se modifica. Son las mismas instancias conocidas por el proyecto; semillas
nuevas miden variación de búsqueda dentro del catálogo y no generalización
a hospitales o instancias no vistos.

Una ampliación a 50, 100 y 150 cirugías tendrá una especificación separada
de generación, cantidad de casos y admisión, anterior a comparar algoritmos.
Esas instancias se reservarán de la calibración.

## Representación, factibilidad y objetivo

La solución fija secuencia y dos salas por cirugía, con asignaciones
independientes por etapa. Tres claves reales por cirugía permiten generar
y reparar soluciones; Tabu opera sobre la solución discreta decodificada.
La reparación puede cambiar orden y salas. El personal se asigna por
reglas de disponibilidad y no forma parte de los cinco movimientos.

El planificador comprueba precedencia, elegibilidad, disponibilidad,
preparación, transición, limpieza y espera máxima. Usa la tolerancia numérica
`WAIT_TOLERANCE = 1e-9` para la espera estricta; una propuesta no factible
no puede ser la mejor solución. La primera sala se retiene hasta el traslado
si la cirugía utiliza otra sala. El anestesista queda reservado hasta el
inicio quirúrgico y el cirujano hasta el fin de limpieza quirúrgica.

Se minimiza

`f = Cmax + 1e-6 × suma de inicios + 0,5 × espera total + 1,4 × espera máxima`.

`Cmax` incluye limpieza de la última operación; los inicios son los de
preparación o reserva; las esperas se miden desde el fin de anestesia
incluida limpieza hasta el inicio del procedimiento quirúrgico. Los tiempos
están en minutos, pero `f` es un objetivo ponderado. Se reportan sus
componentes por separado. No se penaliza desequilibrio entre salas.

Estos supuestos pertenecen al modelo docente y al planificador actual.
El personal constructivo y la reparación limitan los calendarios alcanzables;
no se afirma explorar todas las soluciones factibles ni demostrar optimalidad.

## Búsqueda y aprendizaje

Ambas políticas usan los mismos movimientos:

1. `swap`: intercambio de dos pacientes.
2. `insert`: inserción de un paciente en otra posición.
3. `room_1`: cambio de sala de anestesia.
4. `room_2`: cambio de sala de cirugía.
5. `room_pair`: cambio de ambas salas.

Se generan lotes de quince candidatos distintos. Con probabilidad 0,65
se prioriza uno de los tres pacientes con mayor espera, cuando existen.
La memoria conserva las siete últimas soluciones aceptadas; se permite
aspiración por mejora global y, si todo el lote es tabú, se usa su mejor
candidato como respaldo.

La inicialización evalúa treinta soluciones: FIFO, SPT, LPT y veintisiete
alternativas aleatorias. La búsqueda parte de la mejor, mantiene un archivo
de treinta soluciones y actualiza su peor miembro con el candidato aceptado.
El motor puede retornar al mejor del archivo cuando mejora el estado local.

TS-U selecciona el tipo de movimiento uniformemente. TS-DMAB usa
`media + C × sqrt(2 ln(t) / n)`, donde `media` es la recompensa media del
movimiento, `C` el peso de exploración, `t` el número total de observaciones
desde el reinicio y `n` sus observaciones. Primero prueba cada movimiento.

La recompensa es la mejora positiva del candidato reparado respecto del
estado local antes del lote, dividida por `max(1, 0,02 × objetivo inicial)`
y truncada a `[0,1]`. Un empeoramiento recibe cero. Los duplicados descartados
sin valoración reciben cero y no consumen otra evaluación del objetivo.
El bandido aprende incluso de candidatos no aceptados finalmente por Tabu.

Se fijan `C=0,1`, `delta=0,01` y `lambda=1`. Page-Hinkley detecta caídas
persistentes de recompensa y reinicia las estadísticas de los brazos,
conservando solución, memoria y archivo. No usa metacaracterísticas
contextuales ni etiquetas de estancamiento. Registrar activaciones permite
describir el controlador, no aislar la contribución causal del detector.

## Repeticiones y presupuesto

Se fijan 30 repeticiones por método e instancia, semillas 80-109:

- **720 registros principales:** 12 × 30 × 2.
- **720 trayectorias:** una por configuración, instancia y semilla.
- **4.363.200 valoraciones presupuestadas:** 720 × 6.060.

El presupuesto incluye las treinta evaluaciones iniciales. Los duplicados
sin reevaluación no consumen otra valoración; las evaluaciones repetidas
entre lotes sí cuentan. Intentos, reparación y tiempo se registran. La
revalidación final del mejor calendario se contabiliza aparte del presupuesto,
con su costo incluido en el tiempo total.

La misma semilla comparte las soluciones iniciales. El flujo posterior puede
divergir porque los movimientos consumen distintos números aleatorios;
no se afirma sincronización perfecta. No se calibrarán parámetros con estas
semillas. Cualquier ajuste posterior requiere datos de desarrollo separados
y una versión nueva del protocolo.

## Comparación secundaria por tiempo

Se especifica otra campaña de **720 registros** con los mismos métodos,
instancias y semillas: diez segundos de búsqueda por corrida, incluida
inicialización. La parada temporal reemplaza al presupuesto de evaluaciones.
El reloj monotónico se consulta antes de generar cada candidato; una unidad
atómica comprende generación, reparación y valoración. Se permite finalizar
la última unidad iniciada dentro del plazo y registrar su sobrepaso, sin
iniciar otro candidato. Se registran inicializaciones incompletas y tiempos
de búsqueda y ejecución total por separado.

El motor requiere implementar y verificar este criterio antes de la campaña.
Diez segundos es un presupuesto fijado a priori, no una duración observada.
La comparación temporal es secundaria y separada del contraste principal.

## Métricas e inferencia

La métrica primaria es el objetivo ponderado, con **1% de reducción** como
efecto mínimo relevante. Se publican makespan, esperas total y máxima,
factibilidad, tiempo, evaluaciones, convergencia y eventos del controlador.
Se describen mediana y dispersión entre semillas; los puntos de convergencia
comunes son 10, 50 y 100% del presupuesto.

El análisis global toma doce pares de medianas por instancia, no 360
corridas como si fueran instancias independientes. La ganancia interpretable
es `100 × (mediana_TS-U - mediana_TS-DMAB) / mediana_TS-U`.
La inferencia usa diferencia dividida por el máximo de ambas medianas,
invariante al intercambio de etiquetas. Se fija Wilcoxon bilateral,
alfa 0,05, con ceros Pratt y enumeración de cambios de signo. Al existir
un único contraste principal no se requiere Holm global.

Se realiza un contraste exploratorio por instancia con las treinta
parejas: doce pruebas en total, con corrección de Holm. Se fija prueba de signos como
sensibilidad ante asimetría, sin escoger la prueba por su valor p.
Friedman y post hoc no se aplican al diseño vigente de dos métodos.
La campaña temporal tiene un único contraste exploratorio separado.

Se estiman intervalos del 95% mediante 5.000 remuestreos jerárquicos de
instancias y semillas emparejadas. Las semillas estadísticas son distintas
de las de búsqueda. Se puede informar A12 como efecto marginal descriptivo,
con bootstrap que respeta el pareamiento. Todos los empates, ausencia de
diferencias, familias y semillas quedan definidos en el protocolo legible
por máquina. No rechazar la hipótesis no demuestra equivalencia; treinta
repeticiones no garantizan potencia suficiente para detectar 1%.

## Integridad, entorno y registros

Antes de ejecutar se registran CPU, memoria, versiones, revisión y hashes
recursivos del código. La referencia es macOS/arm64, Python 3.12.14,
NumPy 2.3.5 y SciPy 1.18.1. Se ejecuta una búsqueda por vez, con orden
balanceado y sin otras cargas de cálculo concurrentes.

Se guardan métricas de corridas, calendarios, trazas, eventos Page-Hinkley,
manifiesto e inventario. Se comprueban cobertura, claves únicas, presupuesto
y factibilidad antes del análisis. El contraste global exige las treinta corridas
válidas de ambos métodos en las doce instancias. Fallos y faltantes no se
sustituyen ni se excluyen silenciosamente; una comparación incompleta se
declara no evaluable bajo el protocolo. Las correcciones requieren enmienda,
conservando la evidencia original.

## Uso de la API e historial

Desde un entorno con el paquete instalado, una pareja del motor se ejecuta
mediante la API existente:

```python
from surgery_optim.instances import load_instance
from surgery_optim.tabu import TabuConfig, run_tabu

context = load_instance("instances/standard/HOSP-STD-30-01.yaml")
config = TabuConfig(evaluation_budget=6060)
for label, policy in (("TS-U", "uniform"), ("TS-DMAB", "dmab")):
    result = run_tabu(context, seed=80, policy=policy, config=config)
    print(label, result.final_quality.objective, result.evaluations)
```

El ejemplo utiliza el motor de evaluaciones y no sustituye el registro ni
el análisis completos del protocolo. El runner temporal sigue pendiente.

Los estudios archivados conservan parámetros, manifiestos y resultados propios:
[exploración 0-19](../experiments/results/exploratory_0_19/),
[validación 20-39](../experiments/results/validation_20_39/),
[calibración 0-5](../experiments/results/calibration_0_5/),
[validación 40-59](../experiments/results/validation_40_59/) y
[carteras 60-79](../experiments/results/portfolios_60_79/).
El [protocolo de carteras](protocolo-carteras.md) y el
[protocolo v1 de Entrega 2](../experiments/protocols/entrega2_v1/README.md)
son referencias históricas; no se mezclan con la nueva campaña.

Para reproducir un archivo histórico debe usarse la revisión y configuración
de su manifiesto. El motor conserva `TabuConfig.entrega1()` y
`TabuConfig.from_manifest()` para restaurar parámetros, pero eso no equivale
por sí solo a reproducir el código antiguo. Los manifiestos de las carpetas
[20-39](../experiments/results/validation_20_39/manifest.json) y
[40-59](../experiments/results/validation_40_59/manifest.json), y la
[guía de experimentos](../experiments/README.md), documentan las versiones.
Los CSV de métricas no permiten reconstruir por sí solos la factibilidad:
para ello hacen falta calendarios o una reproducción con el motor correspondiente.
