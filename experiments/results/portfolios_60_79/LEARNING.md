# Aporte del reparto aprendido

Comparaciones secundarias exploratorias con 6.060 evaluaciones por método. Negativo favorece al método de la primera columna. No se ajustaron parámetros ni se repitió la búsqueda a partir de estos resultados.

| Método | Referencia | Diferencia media | IC 95 % agrupado | p Holm |
|---|---|---:|---|---:|
| Mejor de Tabu y D-MAB | Dos reinicios de Tabu | +0.134 | [-0.907, +1.206] | 1.000 |
| Asignación aprendida | Mejor de Tabu y D-MAB | -0.132 | [-0.443, +0.133] | 1.000 |
| Asignación aprendida | Dos reinicios de Tabu | +0.002 | [-1.008, +1.049] | 1.000 |
| Asignación con respaldo | Mejor de Tabu y D-MAB | +0.386 | [-0.123, +0.962] | 0.420 |
| Asignación con respaldo | Dos reinicios de Tabu | +0.520 | [-0.466, +1.555] | 1.000 |

Los intervalos agrupan por instancia y semilla; Wilcoxon usa las doce medias por instancia. Holm corrige estas cinco comparaciones secundarias como familia separada de las cuatro comparaciones principales. Se interpretan exploratoriamente, sin convertir la falta de significación en prueba de equivalencia.
