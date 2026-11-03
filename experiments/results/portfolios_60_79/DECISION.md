# Decisión de arquitectura tras el estudio de carteras

## Recomendación

Para continuar el proyecto se recomienda **una cartera fija de Tabu mixto y
Tabu con D-MAB que conserve el mejor resultado**, sin agregar por ahora un
segundo controlador LinUCB. Es una decisión de simplicidad y respaldo: estas
pruebas no establecen que sea la alternativa de mejor calidad ni que el
aprendizaje supere a los controles con igual presupuesto.

Si el único criterio fuese la menor función objetivo media observada, dos
ejecuciones independientes de Tabu obtuvieron el menor valor. La diferencia
frente a la asignación aprendida fue de apenas 0,002 unidades del objetivo y
no permite declarar un ganador general. Ese control debe permanecer en la
evaluación del proyecto para distinguir aprendizaje de diversidad de búsqueda.

## Evidencia con el mismo presupuesto

Se evaluaron doce instancias sintéticas oficiales de 15, 20, 25 y 30 cirugías,
con tres réplicas por tamaño y veinte semillas nuevas (60–79). Hay 240 pares
instancia–semilla por alternativa. Cada método de la tabla recibió **6.060
evaluaciones**, incluidas inicializaciones y bloques de prueba.

| Alternativa | Objetivo medio | Reducción media frente a Tabu prolongado | IC 95 % de la reducción | Mejora / similar / empeora |
|---|---:|---:|---|---|
| Tabu prolongado | 214,294 | 0,000 | — | Referencia |
| Dos ejecuciones de Tabu | 213,504 | 0,790 | [−0,138; 1,711] | 76 / 125 / 39 |
| Mejor de Tabu y Tabu+D-MAB | 213,638 | 0,656 | [−0,169; 1,584] | 74 / 122 / 44 |
| Reparto aprendido con LinUCB | 213,506 | 0,788 | [−0,046; 1,732] | 74 / 123 / 43 |
| LinUCB después de completar Tabu base | 214,024 | 0,269 | [−0,405; 0,994] | 51 / 158 / 31 |

La reducción es objetivo de Tabu prolongado menos objetivo de la alternativa;
positivo favorece a la alternativa. Los conteos consideran similares las
diferencias de hasta 0,25. La función objetivo combina makespan, espera total,
espera máxima y un término pequeño para desempatar inicios: estos valores no
son exclusivamente minutos de duración de la jornada.

Todos los intervalos incluyen cero. Ninguna de las cuatro comparaciones
principales es significativa tras Holm (p ajustada entre 0,256 y 0,569).
Los intervalos agrupan por instancia y semilla; Wilcoxon utiliza doce medias
por instancia. No se trata de 240 instancias independientes.

Las reducciones medias frente al Tabu prolongado son pequeñas: alrededor de
0,31 % para la cartera fija y 0,37 % para dos Tabu o LinUCB libre. En makespan,
las medias fueron 214,056 minutos para Tabu prolongado, 213,452 para la cartera
fija, 213,323 para dos Tabu, 213,304 para LinUCB libre y 213,794 para LinUCB con
respaldo. Son resultados descriptivos del catálogo evaluado.

## ¿Aporta el nuevo controlador?

LinUCB libre redujo el objetivo medio en 0,132 frente a la cartera fija;
el IC 95 % de esa reducción es [−0,133; 0,443]. Frente a dos Tabu, su objetivo
medio fue 0,002 mayor; el IC 95 % de esa diferencia es [−1,008; 1,049].
La variante con respaldo tuvo menor mejora media que ambas alternativas.
Las cinco comparaciones secundarias son exploratorias y no muestran
significación tras su corrección Holm separada.

Por tanto, no hay evidencia suficiente para justificar la complejidad del
segundo controlador. La falta de significación tampoco demuestra equivalencia
entre métodos ni prueba que el aprendizaje sea inútil en otros presupuestos
o instancias.

## Flujo recomendado y papel del aprendizaje

1. Construir los mismos treinta inicios, incluidos FIFO, SPT y LPT.
2. Ejecutar Tabu mixto con selección uniforme durante 3.030 evaluaciones.
3. Ejecutar otra trayectoria Tabu con D-MAB durante 3.030 evaluaciones,
   incluida su inicialización, con la misma semilla inicial.
4. Conservar el calendario factible de menor objetivo entre las dos.

Ambos caminos mantienen estado y memoria propios. D-MAB sigue siendo la
componente de aprendizaje online: selecciona los movimientos dentro de su
trayectoria mediante UCB1 y Page–Hinkley. El reparto 50/50 y la comparación
final son decisiones deterministas, no un nuevo algoritmo de ML. Este flujo
no detecta anticipadamente cuándo el resultado final de D-MAB será mejor.

Con respecto al Tabu de **3.030** evaluaciones de la misma semilla, la cartera
fija obtuvo 99 mejoras prácticas, 141 resultados similares y cero pérdidas;
la reducción media fue 2,416. Preservar esa solución garantiza no aumentar su
objetivo, pero requiere el doble de evaluaciones. Contra Tabu de **6.060**,
hubo 44 pérdidas prácticas: no existe esa garantía con igual presupuesto.
La protección se refiere al objetivo combinado, no a cada métrica por separado.

## Evaluación que debe acompañar la propuesta

El control principal será Tabu prolongado con el mismo presupuesto. Dos Tabu
independientes serán el control de repetición de búsqueda. D-MAB siempre
activo y UCB1 sin Page–Hinkley permiten estudiar el aporte de selección y
reinicio; FIFO, SPT y LPT mantienen las referencias clásicas del problema.

La arquitectura puede presentarse como una propuesta híbrida respaldada por
una comparación reproducible. No corresponde afirmar que el ML siempre
mejora, que se ha demostrado una mejora general ni que se encontró el óptimo.
Las semillas son nuevas, pero las instancias ya se conocían al escoger la
arquitectura. Los tiempos se midieron con tareas concurrentes y son descriptivos.

## Verificación y archivos

- [Análisis principal](ANALYSIS.md), [comparaciones del aprendizaje](LEARNING.md)
  y [gráfico](comparison.png).
- [Resultados completos](runs.csv), [soluciones finales](solutions.jsonl),
  [decisiones del controlador](decisions.csv) y [manifiesto](manifest.json).
- [Auditoría](verification.json): 1.680 horarios recalculados, 480 ejecuciones
  del asignador y 14.400 decisiones reproducidas; presupuestos, respaldo y
  hashes coinciden.

El conjunto de pruebas de código pasó sus dieciséis casos, incluida la
igualdad exacta entre búsqueda continua y búsqueda pausada.
