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
