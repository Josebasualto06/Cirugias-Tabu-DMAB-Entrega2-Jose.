# Registro de desviaciones del protocolo de la Entrega 2

El protocolo congelado es `docs/protocolo-entrega2.md`, commit `a0da669`. Ese
archivo no se edita. Este registro anota cada cambio, aclaración o error
detectado después del congelamiento, en orden cronológico.

## Aclaraciones

**A1 (2026-10-31). Comparación usada en la regla de tamaño.** La sección 5 fija
la regla de potencia, pero no nombra la comparación. Se aplica a C1, D-MAB frente
a Tabu uniforme con 3.030 evaluaciones, porque es la hipótesis primaria. Esta
aclaración se escribió antes de generar el catálogo y no cambia el resultado: las
otras dos comparaciones tampoco alcanzan 0,80 con alfa 0,0125 para `I < 48` y la
regla entrega `I = 48`.

## Correcciones de implementación

**C1 (2026-10-31). Tiempo de cómputo de la simulación de potencia.** La primera
versión de `power_analysis.py` no terminó. SciPy convierte todo un arreglo en una
prueba de permutación si alguna fila de hasta 13 valores tiene empates. Ahora
las filas empatadas se prueban por separado. La prueba no cambia.

**C2 (2026-10-31). Doble conteo en la simulación de potencia.** La segunda versión
terminó, pero subestimaba la potencia: las medias por instancia ya contienen ruido
de semillas y la simulación lo agregaba otra vez. La señal fue una contradicción
interna: la fórmula t pedía 35 instancias y la simulación daba 0,55 con 36. Se
corrigió reduciendo las medias a la varianza entre instancias estimada. También se
pasó a la DE de diseño `sqrt(entre + intra / 20)`, y se dejó sin valor el límite
con semillas infinitas cuando la varianza entre instancias se estima en cero.

Esa salida se generó y se reemplazó el mismo día, sin usarla en ninguna decisión.
Con ambas versiones la regla entrega `I = 48`. Solo la versión corregida queda en
`experiments/results/entrega2_potencia/`.

## Desviaciones del protocolo

Ninguna a la fecha de este registro.

## Efecto en la interpretación

El error tipo I simulado de C1 queda calibrado: 0,049 con alfa 0,05 e `I = 48`.
El de cartera frente a Tabu prolongado sube a 0,082 con `I = 48`. Por tanto, una
potencia simulada para esa comparación debe leerse como optimista.

## Notas posteriores a la ejecución

Estas notas se agregaron al terminar el estudio de congestión. Ninguna cambia
hipótesis, semillas, familia de comparaciones ni regla de decisión.

**N1 (2026-10-31). Variabilidad mayor que la supuesta.** La DE de C1 fue 13,214 en
congestión, frente a 7,034 en el catálogo estándar. La potencia aproximada para
detectar 0,65 cae a 0,32 con alfa 0,05. El estudio quedó más subdimensionado de lo
planificado. No se agregaron semillas ni instancias, porque el protocolo prohíbe la
parada opcional.

**N2 (2026-10-31). Límites del piloto a igual tiempo.** La Tarea 4 usó límites
derivados de la Tarea 1 para alcanzar unas 3.030 evaluaciones. El equipo corrió más
rápido y alcanzó cerca de 4.500. La comparación sigue siendo a igual tiempo, pero
el rendimiento del equipo varió entre sesiones. La causa no se investigó.

**N3 (2026-10-31). Análisis fuera del protocolo.** `experiments/explore_congestion.py`
calcula UCB1 frente a Tabu uniforme y la potencia realizada. Ese contraste no integra
la familia C1–C4, no tiene corrección múltiple y se informa solo como exploratorio.
Confirmarlo requiere semillas nuevas. El rango reservado empieza en 120.

**N4 (2026-10-31). Verificación de la congestión.** El criterio de más de 50 % se
fijó sobre instancias de desarrollo, donde la celda elegida alcanzó 55 %. En el
catálogo final alcanza 51,8 %, con 995 de 1.920 soluciones de Tabu uniforme y D-MAB.
El margen es estrecho: por tamaño va de 45,0 % a 57,5 %.

**N5 (2026-11-22). Descriptivos de la revisión final.** Después de ver los resultados se
calcularon, sobre las semillas 90–109 archivadas, la dispersión, el RPD, el efecto por tamaño,
el sobrecosto y la razón entre el error estándar del bootstrap jerárquico y el de las medias
por instancia. No estaban en el protocolo, no prueban hipótesis y no cambian C1–C4. El
bootstrap resulta conservador, porque remuestrea semillas dentro de medias que ya contienen
ese ruido; se mantiene porque se fijó antes. H1 sigue sin respaldo.

**N6 (2026-11-22). Precisión de N5: dependencia entre instancias.** El bootstrap es conservador
solo frente al ruido de semillas. Las 48 instancias derivan de las 12 estándar, cuatro de cada
una, y tanto Wilcoxon como el bootstrap las tratan como independientes. Sus valores p e
intervalos pueden ser optimistas por esa dependencia. El protocolo no la modeló. No se cambia
ninguna decisión.

**N7 (2026-11-22). Reanálisis exploratorio por instancia base.** El protocolo fija la
instancia como unidad. Después de ver los resultados, incluido un cálculo informal de los
valores p por base, se decidió repetir C1–C4 con la base como unidad y se fijó informarlos
todos. No se cambió la prueba, la familia de Holm, el bootstrap ni la regla. Según
`experiments/results/entrega3_sensibilidad_bases/`, C1 sigue sin cumplir la regla (p de Holm
0,010; IC [−1,786; +0,176]) y C3 tampoco la cumple. C2 y C4 dejan de cumplirla (p de Holm
0,192 en ambas). Con 12 unidades hay menos potencia: eso no prueba ausencia de efecto. Las
decisiones registradas no cambian y no se agregaron corridas, semillas ni instancias.
