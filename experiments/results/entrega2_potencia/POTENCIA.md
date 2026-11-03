# Análisis de potencia estadística

Fuente: `portfolios_60_79/runs.csv`, 12 instancias por 20 semillas, 240 pares. Potencia 0,80 y alfa 0,05 bilateral. Este análisis no ejecuta búsquedas.

## Tamaños necesarios

| Comparación | Efecto | DE dif. | ICC | Efecto de diseño | Pares si fueran independientes | Veces 240 | Instancias con 20 semillas | Instancias con semillas infinitas |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| D-MAB − Tabu uniforme (3.030) | 0.25 | 7.034 | 0.000 | 1.00 | 6217 | 25.9 | 317 | sin límite estimable |
| D-MAB − Tabu uniforme (3.030) | 0.65 | 7.034 | 0.000 | 1.00 | 922 | 3.8 | 49 | sin límite estimable |
| Cartera − Tabu prolongado (6.060) | 0.25 | 4.292 | 0.047 | 1.89 | 2315 | 9.6 | 221 | 111 |
| Cartera − Tabu prolongado (6.060) | 0.65 | 4.292 | 0.047 | 1.89 | 345 | 1.4 | 35 | 19 |
| Cartera − Dos Tabu (6.060) | 0.25 | 5.018 | 0.053 | 2.02 | 3165 | 13.2 | 322 | 172 |
| Cartera − Dos Tabu (6.060) | 0.65 | 5.018 | 0.053 | 2.02 | 470 | 2.0 | 50 | 28 |

Si la varianza entre instancias se estima en cero, las semillas por sí solas bastarían y no hay límite estimable en instancias. Esa estimación tiene 11 grados de libertad y no prueba que la varianza sea nula.

## Diseño actual

| Comparación | Media observada | DE observada de medias | DE de diseño | Pares efectivos | Efecto mínimo detectable con 12 instancias |
|---|---:|---:|---:|---:|---:|
| D-MAB − Tabu uniforme (3.030) | +0.108 | 1.332 | 1.584 | 240.0 | 1.41 |
| Cartera − Tabu prolongado (6.060) | -0.656 | 1.321 | 1.321 | 127.2 | 1.17 |
| Cartera − Dos Tabu (6.060) | +0.134 | 1.596 | 1.596 | 119.1 | 1.42 |

La DE de diseño es `sqrt(entre + intra / 20)`. Se usa porque se extiende a otro número de semillas. Coincide con la DE observada salvo cuando la varianza entre instancias se trunca en cero.

## Potencia simulada de la prueba real

Wilcoxon sobre medias por instancia, 5000 réplicas, 20 semillas. El efecto 0 mide el error tipo I.

| Comparación | Efecto | Instancias | Rechazo con alfa 0,05 | Rechazo con alfa 0,0125 |
|---|---:|---:|---:|---:|
| D-MAB − Tabu uniforme (3.030) | 0.00 | 12 | 0.039 | 0.012 |
| D-MAB − Tabu uniforme (3.030) | 0.00 | 24 | 0.048 | 0.012 |
| D-MAB − Tabu uniforme (3.030) | 0.00 | 36 | 0.054 | 0.013 |
| D-MAB − Tabu uniforme (3.030) | 0.00 | 48 | 0.049 | 0.011 |
| D-MAB − Tabu uniforme (3.030) | 0.25 | 12 | 0.075 | 0.025 |
| D-MAB − Tabu uniforme (3.030) | 0.25 | 24 | 0.130 | 0.044 |
| D-MAB − Tabu uniforme (3.030) | 0.25 | 36 | 0.187 | 0.076 |
| D-MAB − Tabu uniforme (3.030) | 0.25 | 48 | 0.239 | 0.103 |
| D-MAB − Tabu uniforme (3.030) | 0.65 | 12 | 0.297 | 0.146 |
| D-MAB − Tabu uniforme (3.030) | 0.65 | 24 | 0.581 | 0.338 |
| D-MAB − Tabu uniforme (3.030) | 0.65 | 36 | 0.766 | 0.557 |
| D-MAB − Tabu uniforme (3.030) | 0.65 | 48 | 0.873 | 0.719 |
| Cartera − Tabu prolongado (6.060) | 0.00 | 12 | 0.054 | 0.019 |
| Cartera − Tabu prolongado (6.060) | 0.00 | 24 | 0.062 | 0.019 |
| Cartera − Tabu prolongado (6.060) | 0.00 | 36 | 0.079 | 0.023 |
| Cartera − Tabu prolongado (6.060) | 0.00 | 48 | 0.082 | 0.026 |
| Cartera − Tabu prolongado (6.060) | 0.25 | 12 | 0.068 | 0.020 |
| Cartera − Tabu prolongado (6.060) | 0.25 | 24 | 0.110 | 0.030 |
| Cartera − Tabu prolongado (6.060) | 0.25 | 36 | 0.154 | 0.053 |
| Cartera − Tabu prolongado (6.060) | 0.25 | 48 | 0.185 | 0.076 |
| Cartera − Tabu prolongado (6.060) | 0.65 | 12 | 0.400 | 0.209 |
| Cartera − Tabu prolongado (6.060) | 0.65 | 24 | 0.733 | 0.493 |
| Cartera − Tabu prolongado (6.060) | 0.65 | 36 | 0.894 | 0.735 |
| Cartera − Tabu prolongado (6.060) | 0.65 | 48 | 0.950 | 0.865 |
| Cartera − Dos Tabu (6.060) | 0.00 | 12 | 0.043 | 0.011 |
| Cartera − Dos Tabu (6.060) | 0.00 | 24 | 0.054 | 0.011 |
| Cartera − Dos Tabu (6.060) | 0.00 | 36 | 0.050 | 0.014 |
| Cartera − Dos Tabu (6.060) | 0.00 | 48 | 0.058 | 0.017 |
| Cartera − Dos Tabu (6.060) | 0.25 | 12 | 0.094 | 0.036 |
| Cartera − Dos Tabu (6.060) | 0.25 | 24 | 0.159 | 0.062 |
| Cartera − Dos Tabu (6.060) | 0.25 | 36 | 0.219 | 0.094 |
| Cartera − Dos Tabu (6.060) | 0.25 | 48 | 0.263 | 0.128 |
| Cartera − Dos Tabu (6.060) | 0.65 | 12 | 0.290 | 0.140 |
| Cartera − Dos Tabu (6.060) | 0.65 | 24 | 0.561 | 0.331 |
| Cartera − Dos Tabu (6.060) | 0.65 | 36 | 0.762 | 0.550 |
| Cartera − Dos Tabu (6.060) | 0.65 | 48 | 0.866 | 0.709 |

## Regla para el catálogo de congestión

Regla del protocolo sobre la hipótesis primaria: `I = 48`. Ningún nivel alcanza 0,80 con alfa 0,0125, por lo que el diseño queda declarado como subdimensionado.

La extrapolación supone instancias nuevas parecidas a las doce observadas y un efecto homogéneo. La varianza del catálogo de congestión puede ser distinta.
