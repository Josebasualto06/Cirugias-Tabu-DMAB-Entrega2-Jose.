# Lectura exploratoria del estudio de congestión

**No estaba pre-registrada.** No integra la familia C1–C4, no corrige por comparaciones múltiples y necesita semillas nuevas para confirmarse.

## Contraste fuera de la familia

| Contraste | Pares | Media dif. | IC 95 % agrupado | Instancias mejor / peor | p sin corregir |
|---|---:|---:|---|---|---:|
| UCB1 − Tabu uniforme (3.030) | 960 | -2.617 | [-3.904, -1.345] | 35 / 13 | 0.0000 |

## Potencia con la variabilidad observada en C1

La potencia del protocolo supuso DE 7.034. La DE observada en congestión fue 13.214. Aproximación t sobre medias por instancia, con DE de diseño 2.984.

| Efecto | Potencia con alfa 0,05 | Potencia con alfa 0,0125 | Pares necesarios |
|---:|---:|---:|---:|
| 0.25 | 0.09 | 0.03 | 21930 |
| 0.65 | 0.32 | 0.15 | 3246 |

## Soluciones finales con espera

Tabu uniforme y D-MAB, 3.030 evaluaciones.

| Cirugías | Soluciones | Con espera | Espera total media |
|---|---:|---:|---:|
| 15 | 480 | 49.2% | 3.23 |
| 20 | 480 | 45.0% | 4.04 |
| 25 | 480 | 55.6% | 11.23 |
| 30 | 480 | 57.5% | 16.71 |
| todas | 1920 | 51.8% | 8.80 |
