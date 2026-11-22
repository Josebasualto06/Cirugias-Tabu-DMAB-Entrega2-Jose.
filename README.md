# Programación de cirugías electivas mediante búsqueda tabú y selección adaptativa de movimientos

Proyecto de la asignatura **OII464: Desarrollo de Diseños Híbridos para
Optimización**. Se propone combinar Tabu Search con aprendizaje online para
estudiar cuándo la selección adaptativa de movimientos mejora la calidad, el
tiempo o la robustez de la programación quirúrgica. La Entrega 1 presenta el
estado del arte, la arquitectura y el plan de evaluación del semestre.

## Arquitectura elegida: Tabu Search + D-MAB

El aprendizaje actúa en la fase de **evolución**, específicamente en la
selección del movimiento con que se genera cada vecino. Tabu Search mantiene
la búsqueda y su memoria; **D-MAB** aprende a elegir entre cinco movimientos:
intercambio, inserción, cambio de sala de anestesia, cambio de sala de cirugía
y cambio de ambas salas. UCB1 combina recompensa observada y exploración;
Page–Hinkley reinicia las estimaciones del bandido ante una caída de recompensa.
No reinicia Tabu ni identifica directamente un óptimo local.

La propuesta usa una **cartera fija con respaldo**:

1. Construir treinta soluciones iniciales por camino: FIFO, SPT, LPT y
   veintisiete alternativas aleatorias.
2. Ejecutar Tabu con selección uniforme durante **3.030 evaluaciones**.
3. Ejecutar otra trayectoria Tabu con D-MAB durante **3.030 evaluaciones**,
   con la misma semilla inicial y memoria independiente.
4. Entregar la solución factible de menor objetivo entre ambas.

El presupuesto total es **6.060 evaluaciones, incluidas las dos
inicializaciones**. El reparto 50/50 y la comparación final son deterministas;
la componente ML es D-MAB **dentro del segundo camino**. La ejecución de
referencia es secuencial. El estudio de LinUCB para repartir presupuesto entre
caminos queda como alternativa experimental archivada.

Consulta la [arquitectura completa](docs/arquitectura-final.md) y la
[metodología experimental](docs/metodologia-experimental.md).

## Problema, objetivo y restricciones

Cada solución contiene un orden de pacientes y asignaciones de sala para
anestesia y cirugía. Un planificador estricto asigna personal elegible y
comprueba precedencias, disponibilidad, preparación, transición, limpieza y
espera máxima entre etapas. Las salas pueden diferir entre etapas y no se
impone equilibrio entre pabellones. El decodificador repara preferencias de
sala y orden para conseguir factibilidad; esto puede restringir los
calendarios alcanzables.

Se minimiza:

`f = Cmax + 1e-6 × suma de inicios + 0,5 × espera total + 1,4 × espera máxima`.

`Cmax` es el tiempo de término de la última operación, incluida su limpieza.
La suma de inicios considera el comienzo de preparación o reserva de cada
operación. La espera se mide desde el fin de anestesia, incluida su limpieza,
hasta el inicio del procedimiento quirúrgico. Los tiempos están en minutos;
el valor de `f` es un **objetivo combinado**, no exclusivamente la duración de
la jornada. Makespan y espera también se reportan por separado.

D-MAB no requiere entrenamiento previo con etiquetas: recibe recompensas de
los candidatos evaluados durante cada corrida. La calibración de parámetros
se realiza fuera de línea, separada de la evaluación.

## Entrega 3 y final: resultados y conclusiones

- [Informe final](informe/Entrega_3_Tabu_DMAB.pdf), con las secciones de
  [resultados y discusión](informe/resultados.tex) y [conclusión](informe/conclusion.tex).
- [Presentación final](presentacion_final/main.pdf) y su [guion](presentacion_final/guion.md).
- Protocolos pre-registrados: [Entrega 2](docs/protocolo-entrega2.md) y
  [Entrega 3](docs/protocolo-entrega3.md), con sus registros de desviaciones.

En el catálogo de congestión, con 48 instancias y 960 pares por estudio:

| Comparación (diferencia: alternativa − referencia) | Media | IC 95 % | Lectura |
|---|---:|---|---|
| C1: D-MAB − Tabu uniforme, 3.030 | −0,793 | [−1,850; +0,279] | No concluyente |
| C4: D-MAB − UCB1 sin reinicio, 3.030 | +1,824 | [+0,566; +3,124] | Favorece a UCB1; frágil por base |
| C2: cartera − Tabu prolongado, 6.060 | −1,380 | [−2,405; −0,398] | Favorece a la cartera; frágil por base |
| C3: cartera − dos Tabu, 6.060 | −0,409 | [−1,126; +0,338] | No concluyente |

Estas cuatro comparaciones usan las semillas 90–109
([análisis](experiments/results/entrega2_congestion_90_109/ANALYSIS.md)). Un valor
negativo favorece a la alternativa. Aparte, una confirmación pre-registrada con
las semillas nuevas 120–139 comparó UCB1 sin reinicio con Tabu uniforme: −2,749,
IC 95 % [−4,069; −1,453]
([análisis](experiments/results/entrega3_confirmacion_ucb1/ANALYSIS.md)).

**No se demostró que D-MAB mejore a Tabu uniforme**: el intervalo de C1 incluye
el cero. La cartera supera al Tabu prolongado, pero no se distingue de dos Tabu
independientes, así que su ganancia es compatible con repetir la búsqueda. El
reinicio Page–Hinkley no ayudó bajo congestión; UCB1 sin reinicio sí superó a
Tabu uniforme, aunque no con 15 cirugías y con cerca de 10 % más de tiempo. En
el catálogo estándar los signos no fueron consistentes entre estudios
([descriptivos](experiments/results/entrega3_revision/DESCRIPTIVOS.md)). Las
semillas nuevas sobre el mismo catálogo sintético no miden generalización a
otros hospitales.

Las 48 instancias derivan de 12 bases. Un
[reanálisis exploratorio](experiments/results/entrega3_sensibilidad_bases/SENSIBILIDAD.md),
decidido después de ver los resultados, usa la base como unidad. Con él, C1 sigue
sin cumplir la regla, C2 y C4 dejan de cumplirla y la confirmación de UCB1 la
mantiene. No reemplaza las decisiones registradas.

La regla de salas sigue la formulación de clase y difiere de la del simulador
estricto del repositorio docente: los valores no son comparables con los de ese
simulador (sección 3.5 del informe).

## Entrega 1

- [Informe en LaTeX](informe/main.tex) y [PDF compilado](informe/Entrega_1_Tabu_DMAB.pdf).
- [Matriz de criterios](informe/criterios-entrega.md).
- [Arquitectura elegida y papel de ML](docs/arquitectura-final.md).
- [Protocolo y alcance de los experimentos](docs/metodologia-experimental.md).
- [Evidencia que motivó la selección](experiments/results/portfolios_60_79/DECISION.md).

La pregunta de investigación es: **¿en qué condiciones la selección
adaptativa de movimientos mediante D-MAB mejora Tabu Search frente a elegir
los mismos movimientos uniformemente?** La evaluación distingue el aporte
del aprendizaje del efecto de repetir la búsqueda o consumir más cómputo.

## Evidencia preliminar y controles

El [estudio de carteras](experiments/results/portfolios_60_79/ANALYSIS.md)
utilizó doce instancias sintéticas del catálogo oficial, veinte semillas
nuevas por instancia (60–79) y 6.060 evaluaciones por alternativa.

| Alternativa | Reducción media del objetivo frente a Tabu de 6.060 | IC 95 % |
|---|---:|---|
| Dos Tabu independientes | 0,790 | [−0,138; 1,711] |
| Cartera fija Tabu + D-MAB | 0,656 | [−0,169; 1,584] |
| Reparto aprendido con LinUCB | 0,788 | [−0,046; 1,732] |
| LinUCB después de completar Tabu base | 0,269 | [−0,405; 0,994] |

Una reducción positiva favorece a la alternativa. Los intervalos agrupan por
instancia y semilla; todos incluyen cero y ninguna comparación principal
resultó significativa tras Holm. **No hay una superioridad general
demostrada del aprendizaje.** LinUCB añade complejidad sin una ventaja clara
en este piloto; la cartera fija se eligió por sencillez y conservación de una
referencia. Dos Tabu independientes permanece como control obligatorio.

La cartera conserva el objetivo del Tabu de **3.030** evaluaciones de la
misma semilla: frente a esa referencia hubo 99 mejoras prácticas, 141
resultados similares y ninguna pérdida (umbral descriptivo 0,25). Esa
protección consume el doble de evaluaciones; **no garantiza superar a Tabu de
6.060 ni mejorar el makespan por separado**. Las instancias ya eran conocidas
al escoger la arquitectura; las semillas nuevas evalúan variación de búsqueda
dentro del catálogo, no generalización a hospitales no vistos.

## Instalar y reproducir

Se requiere Python 3.11 o posterior. Desde la raíz del repositorio:

```bash
python -m venv .venv
.venv/bin/python -m pip install -e '.[test]'
.venv/bin/python -m pytest -q
.venv/bin/python -m surgery_optim.portfolio \
  --instance instances/standard/HOSP-STD-30-01.yaml \
  --seed 60 --budget 6060 \
  --output outputs/final/HOSP-STD-30-01-seed60.json
```

El JSON conserva ambos componentes, solución, calendario, evaluaciones y
tiempos. Se incluye un [ejemplo reproducido](outputs/final/HOSP-STD-30-01-seed60.json)
que coincide con la cartera fija archivada para esa instancia y semilla.
La cartera también está disponible como
`from surgery_optim.portfolio import run_portfolio`.
Su implementación está en [`src/surgery_optim/portfolio/`](src/surgery_optim/portfolio/).

Los estudios guardan resultados parciales y comprueban configuración, datos y
hashes para reanudar. Los archivos históricos se preservan con la versión que
los produjo; un cambio de código requiere otra carpeta de resultados. La
[guía de experimentos](experiments/README.md) documenta cada etapa y sus
comandos. Las 6.060 son evaluaciones de soluciones dentro de una corrida.

## Organización e historial de estudios

| Ruta | Contenido |
|---|---|
| [`informe/`](informe/) | Informe de la primera entrega, fuentes y PDF. |
| [`src/surgery_optim/`](src/surgery_optim/) | Datos, planificador, objetivo, Tabu, D-MAB y cartera fija. |
| [`instances/standard/`](instances/standard/) | Doce YAML sintéticos, de 15 a 30 cirugías. |
| [`docs/`](docs/) | Arquitectura, metodología y protocolos. |
| [`experiments/results/exploratory_0_19/`](experiments/results/exploratory_0_19/) | Pilotos exploratorios iniciales, archivados. |
| [`experiments/results/validation_20_39/`](experiments/results/validation_20_39/) | Validación de la configuración inicial, archivada. |
| [`experiments/results/calibration_0_5/`](experiments/results/calibration_0_5/) | Calibración de la versión 2 con semillas exploratorias. |
| [`experiments/results/validation_40_59/`](experiments/results/validation_40_59/) | Comparación de políticas de 3.030 evaluaciones, versión 2. |
| [`experiments/results/portfolios_60_79/`](experiments/results/portfolios_60_79/) | Comparación de carteras de 6.060 y decisión de arquitectura. |
| [`tests/`](tests/) | Restricciones, reproducibilidad y consistencia de búsquedas. |
| [`outputs/final/`](outputs/final/) | Ejemplo ejecutable de la cartera final, con ambos caminos y calendario elegido. |

En la validación 40–59, D-MAB tuvo 101 victorias, 13 empates y 126 derrotas
frente a Tabu uniforme (tolerancia numérica `1e-9`). Ese estudio no se mezcla
con el de carteras: usa otro presupuesto y otra definición descriptiva de
similitud. Los informes históricos conservan sus conclusiones originales.

## Procedencia y alcance

Las doce instancias coinciden con las del [repositorio oficial del
caso](https://github.com/Saicooh/OII464_Hospitales) en el commit
`ecd30e3dbc1962d856c09b3470d1870c3b139a9a`. Son datos sintéticos; no son
pacientes reales ni los cuatro JSON históricos de la presentación. El
repositorio oficial se utilizó como fuente y no se modificó.

Ninguna corrida demuestra optimalidad global. El planificador asigna personal
mediante una regla y reserva recursos según los supuestos documentados;
todavía no se estudian urgencias, cancelaciones o replanificación durante la
jornada. La extensión a instancias mayores, más congestión y límites de
tiempo forma parte del trabajo futuro del semestre.
