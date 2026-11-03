# Protocolo pre-registrado de la Entrega 2

**Estado:** congelado antes de ejecutar cualquier experimento de esta entrega.
Este archivo no se edita después de su commit. Todo cambio posterior se anota
en `docs/protocolo-entrega2-desviaciones.md`, con fecha, motivo y efecto.

## 1. Pregunta, hipótesis y métrica primaria

**Pregunta.** ¿En qué condiciones la selección adaptativa de movimientos con
D-MAB mejora Tabu Search frente a elegir los mismos movimientos uniformemente?

**Condición nueva.** El catálogo estándar casi no tiene bloqueo: 16 de 240
soluciones finales presentan espera en `portfolios_60_79`. Esta entrega crea un
catálogo donde la espera sea la norma y repite la comparación en esa condición.

**Métrica primaria.** El objetivo combinado de `objective.py`, sin cambios:

`f = Cmax + 1e-6 × Σ inicios + 0,5 × Σ esperas + 1,4 × espera máxima`.

**H1 (falsable).** En el catálogo de congestión, con igual presupuesto, Tabu con
D-MAB obtiene menor `f` medio que Tabu uniforme. La diferencia pareada
`D-MAB − uniforme` (comparación C1) es negativa.

**H0.** La mediana de las medias por instancia de esa diferencia es cero.

**Regla de decisión.** H1 queda respaldada solo si se cumplen las tres
condiciones en C1:

1. `p` de Holm menor que 0,05.
2. IC 95 % agrupado completamente bajo cero.
3. Media pareada menor o igual que −0,25.

Cualquier otro resultado no respalda H1. La falta de significación no prueba
equivalencia entre métodos.

## 2. Predicción mecánica previa sobre la congestión

El código permite deducir una predicción antes de medir. En el catálogo
estándar, `setup` y `transition` de cirugía valen cero en todas las operaciones.
Con la misma sala en ambas etapas, la espera depende solo del cirujano. Reducir
salas desplaza la cola hacia antes de la anestesia y no hacia el tramo entre
etapas. Ajustar `max_wait` limita la espera, pero no la provoca.

**P1.** Reducir salas o ajustar `max_wait`, sin reducir cirujanos, no alcanza el
objetivo de espera de la sección 5. **P2.** Reducir cirujanos sí lo alcanza.

El planificador tampoco inserta una demora antes de la anestesia. Por eso, un
exceso de escasez de cirujanos puede volver imposible el orden propuesto. El
criterio de la sección 5 descarta esas celdas.

**Palanca prohibida.** No se asigna `setup` ni `transition` positivos a la
cirugía. Esa espera sería constante por construcción y no mediría congestión.

## 3. Asignación de semillas

Las semillas 0–79 están consumidas. También lo están 1.000.060–1.000.079,
usadas por el segundo Tabu independiente. Ningún experimento nuevo las reutiliza.

| Rango | Uso | Catálogo |
|---|---|---|
| 80–84 | Tarea 1: tiempos de pared | Estándar |
| 85–89 | Tarea 3: calibración de la congestión | Instancias de desarrollo |
| 90–109 | Tarea 3: estudio principal | Congestión |
| 1.000.090–1.000.109 | Tarea 3: segundo Tabu independiente (`semilla + 1.000.000`) | Congestión |
| 110–114 | Tarea 4: piloto a igual tiempo | Estándar |
| 115–119 | Diagnóstico de reparación, recompensa y archivo | Estándar |
| 120 en adelante | Reserva para desviaciones registradas | — |

Las semillas 90–109 no se usan hasta fijar el catálogo de congestión. Las
instancias de desarrollo nunca forman parte de ese catálogo.

## 4. Presupuesto, parada y conteo

- Criterio de parada: agotar el presupuesto de evaluaciones del camino.
- Presupuestos: 3.030 por camino y 6.060 por alternativa de igual presupuesto.
- Cuenta una evaluación: cada llamada a `quality()` sobre una solución inicial o
  sobre un candidato distinto dentro de su lote. Las treinta iniciales cuentan.
- También cuentan los candidatos infactibles, que reciben `f` infinito.
- No cuentan: duplicados del lote, intentos de propuesta, reparación, cálculo de
  prioridad por espera, selección del movimiento ni revalidación final.
- Parámetros congelados: `C=0,1`, `delta=0,01`, `lambda=1`, tenure 7 sobre firmas
  de solución, 15 candidatos por lote, 30 soluciones iniciales.
- Sin cambios en `src/` ni en `experiments/results/` archivados. Los verificadores
  históricos deben seguir pasando al terminar.

## 5. Catálogo de congestión

**Generador.** `experiments/generate_congestion.py` crea cada instancia en tres
pasos, con semilla propia por instancia:

1. Remuestrea con reemplazo pacientes de la instancia estándar del mismo tamaño.
2. Multiplica cada tiempo por ruido lognormal de `sigma=0,10` y redondea a 0,5 min.
3. Aplica `rho_R`, `rho_S` y `rho_W`, y redibuja la elegibilidad de personal.

`rho_R` escala las salas, `rho_S` escala los cirujanos y `rho_W` escala
`max_wait`. Los anestesistas no cambian. La elegibilidad usa tres profesionales
por operación, como el catálogo estándar. Todas las salas siguen elegibles.

**Calibración.** Se usan cuatro instancias de desarrollo, una por tamaño, y la
grilla completa de 18 celdas:

| Factor | Niveles |
|---|---|
| `rho_S` | 1,00; 0,60; 0,40 |
| `rho_R` | 1,00; 0,75 |
| `rho_W` | 0,50; 1,00; 2,00 |

Cada celda corre Tabu uniforme y Tabu con D-MAB, 3.030 evaluaciones, semillas
85–89.

**Celda válida.** Una celda es válida si cumple todo lo siguiente:

1. FIFO, SPT y LPT encuentran solución factible en las cuatro instancias.
2. Ninguna corrida falla.
3. Al menos 95 % de las evaluaciones son factibles.
4. Más de 50 % de las soluciones finales tiene espera positiva.

**Selección.** Entre las celdas válidas se elige la más cercana al catálogo
estándar: mayor `rho_S`, luego mayor `rho_R`, luego `rho_W` más cercano a 1
(`|ln rho_W|` mínimo). Si ninguna es válida, se registra una desviación antes de
ampliar la grilla.

**Tamaño del catálogo.** Las instancias pesan más que las semillas, porque
comparten datos entre semillas. Se fijan 20 semillas por instancia. El número de
instancias `I` sale de la Tarea 2: el menor valor de {12, 24, 36, 48} con
potencia simulada de al menos 0,80 para detectar 0,65, con `alfa=0,0125`. Ese
alfa corresponde al peor caso de Holm con cuatro comparaciones. Si ninguno
alcanza la potencia, se usa `I=48` y se declara el subdimensionamiento. La regla
usa solo datos archivados, nunca resultados de congestión.

Si la estimación de duración supera 60 minutos de pared, se reduce `I` al
siguiente nivel menor, y se registra como desviación antes de ejecutar.

Cada YAML debe pasar `load_instance`. Su SHA-256 queda en el manifiesto.

## 6. Comparaciones y estadística

Todas las comparaciones usan pares instancia–semilla sobre el catálogo de
congestión y la diferencia `alternativa − referencia`. Negativo favorece a la
alternativa.

| Id | Alternativa | Referencia | Presupuesto | Qué aísla |
|---|---|---|---|---|
| C1 | Tabu + D-MAB | Tabu uniforme | 3.030 c/u | Efecto del aprendizaje (hipótesis primaria) |
| C2 | Cartera fija | Tabu prolongado | 6.060 c/u | Repartir frente a prolongar |
| C3 | Cartera fija | Dos Tabu independientes | 6.060 c/u | Aprendizaje frente a repetir la búsqueda |
| C4 | Tabu + D-MAB | Tabu + UCB1 | 3.030 c/u | Ablación de Page–Hinkley |

- **Unidad de análisis:** la instancia. Primero se promedian las semillas.
- **Prueba:** Wilcoxon de rangos con signo, bilateral, sobre las medias por
  instancia, con `zero_method="zsplit"`.
- **Familia:** C1–C4, corregida con Holm. Es la única familia confirmatoria.
- **Incertidumbre:** bootstrap jerárquico de instancias y semillas emparejadas,
  5.000 réplicas, generador con semilla 20261102.
- **Secundarias, solo descriptivas:** `Cmax`, espera total, espera máxima,
  factibilidad, tiempo y evaluación de la última mejora. Una baja de `f` no
  implica una baja en cada componente.
- **Sin parada opcional:** no se agregan semillas ni instancias según el resultado.
- **Fallos:** si una corrida falla, el par se excluye de todas las comparaciones
  y se informa el conteo. Si falla más de 1 % de los pares, se registra una
  desviación y C1–C4 pasan a ser exploratorias.

## 7. Umbral de relevancia práctica

El umbral es **0,25 unidades de `f`**. Todos los tiempos de las instancias son
múltiplos de 0,5 min. Por tanto, `Cmax` cambia en pasos de 0,5 y un paso de
espera total mueve `f` en 0,25. Una diferencia menor no representa un cambio de
un paso en ningún componente del calendario. El umbral conserva además
comparabilidad descriptiva con `portfolios_60_79`.

## 8. Tareas no inferenciales

**Tarea 1, entorno.** Registra CPU, núcleos, RAM, sistema operativo y versiones.
Mide `run_portfolio` con 6.060 evaluaciones en las 12 instancias estándar, semillas
80–84, en un solo proceso y sin otra carga del agente. Informa mediana y rango
por tamaño.

**Tarea 2, potencia.** Usa `portfolios_60_79/runs.csv`. Compara cartera frente a
Tabu de 6.060, cartera frente a dos Tabu y D-MAB frente a uniforme de 3.030.
Calcula, para efectos de 0,25 y 0,65, potencia 0,80 y `alfa=0,05` bilateral:

1. Pares necesarios si fueran independientes.
2. Componentes de varianza entre e intra instancia, ICC y efecto de diseño.
3. Instancias necesarias con 20 semillas, y límite con semillas infinitas.
4. Potencia simulada de la prueba real: Wilcoxon sobre medias por instancia.

Esta tarea no ejecuta búsquedas.

**Tarea 4, piloto a igual tiempo.** El límite de cada camino es la mitad de la
mediana de la Tarea 1 para ese tamaño. Corre Tabu uniforme y D-MAB en las
instancias `-01` de cada tamaño, semillas 110–114, en un solo proceso. Es un
piloto descriptivo y no sustenta conclusiones. Si no alcanza el tiempo, queda
como protocolo planificado.

**Diagnóstico.** En las 12 instancias estándar, semillas 115–119, mide la fracción
de candidatos reparados, la fracción de propuestas con recompensa positiva y la
igualdad de trayectorias al retirar el archivo de 30 soluciones. Solo describe
mecanismos del motor.

## 9. Alcance y límites declarados

- Las semillas nuevas sobre el catálogo estándar no miden generalización a
  instancias no vistas.
- El catálogo de congestión remuestrea el catálogo estándar. Sus instancias son
  nuevas para la búsqueda, pero comparten perfil de duraciones. No representan
  hospitales reales ni un dominio independiente.
- Las instancias estándar ya se conocían al elegir la arquitectura.
- Los resultados de congestión no se mezclan en tablas con estudios anteriores.
- Ningún estudio demuestra optimalidad.
- El tiempo medido depende del equipo y de su carga. El control principal de
  cómputo es el número de evaluaciones.
