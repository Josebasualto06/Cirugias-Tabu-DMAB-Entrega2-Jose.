# Calibración en semillas exploratorias 0–5

Diferencia emparejada contra Tabu uniforme con memoria de soluciones (configuración de la Entrega 1); negativo es mejor. 12 instancias × 6 semillas.

| Variante | Media dif. | Mediana de medianas por instancia | Gana / empata / pierde | Reinicios PH (mediana) | Reparados (mediana) |
|---|---:|---:|---:|---:|---:|
| `uniform|solution|C=1.0|lambda=0.35` | +0.000 | +0.000 | 0 / 72 / 0 | 0 | 928 |
| `uniform|attribute|C=1.0|lambda=0.35` | +3.525 | +1.500 | 11 / 20 / 41 | 0 | 934 |
| `dmab|attribute|C=0.1|lambda=0.35` | +4.684 | +3.250 | 10 / 17 / 45 | 106 | 928 |
| `dmab|attribute|C=0.1|lambda=1.0` | +4.776 | +5.375 | 8 / 18 / 46 | 54 | 914 |
| `dmab|attribute|C=0.1|lambda=3.0` | +5.190 | +3.875 | 5 / 18 / 49 | 13 | 847 |
| `dmab|attribute|C=0.03|lambda=0.35` | +4.838 | +4.250 | 10 / 16 / 46 | 110 | 906 |
| `dmab|attribute|C=0.03|lambda=1.0` | +5.163 | +4.987 | 5 / 18 / 49 | 60 | 887 |
| `dmab|solution|C=1.0|lambda=0.35` | -0.140 | -0.250 | 28 / 15 / 29 | 18 | 899 |
| `dmab|solution|C=0.1|lambda=1.0` | -0.224 | +0.125 | 25 / 18 / 29 | 12 | 874 |
| `dmab|solution|C=0.1|lambda=10.0` | +1.173 | +0.000 | 25 / 16 / 31 | 0 | 880 |
| `dmab|solution|C=0.02|lambda=1.0` | +2.047 | +1.200 | 21 / 13 / 38 | 12 | 837 |
| `dmab|solution|C=0.02|lambda=10.0` | +2.228 | +2.000 | 21 / 12 / 39 | 0 | 788 |
| `ucb|solution|C=0.1|lambda=0.35` | +1.236 | +0.375 | 24 / 15 / 33 | 0 | 861 |
| `ucb|solution|C=0.02|lambda=0.35` | +2.387 | +1.375 | 21 / 12 / 39 | 0 | 854 |

Gana/pierde usan el umbral práctico de 0,25 min de la Entrega 1.

## Decisión

Regla fijada antes de validar: se usa la memoria tabú y los parámetros (C, λ) de la variante D-MAB con menor diferencia media; UCB1 usa el mismo C para que la ablación solo quite Page–Hinkley.

* **Memoria tabú:** la memoria por atributo empeora a Tabu uniforme (+3,5 min de media) y a todas las variantes D-MAB; se mantiene la memoria de soluciones.
* **Escala C:** reducir C para que el bandit explote las recompensas **empeora** el resultado (C = 0,02: +2,0 a +2,4 min). Con C = 1 el controlador elige casi por turnos, pero esa diversidad de movimientos es valiosa: la recompensa de mejora inmediata no predice bien qué movimiento conviene seguir usando.
* **Page–Hinkley:** con C = 0,1, los reinicios (λ = 1, mediana 12 por corrida) ayudan frente a no reiniciar (λ = 10 o UCB1), porque devuelven exploración al controlador.
* **Elegida:** C = 0,1 y λ = 1,0 (media −0,22 min frente a −0,14 min de C = 1, λ = 0,35). La diferencia entre ambas es menor que la variación entre semillas, así que la calibración no anticipa una ventaja clara de D-MAB.
* **Movimientos reparados:** cerca de 900 de 3.000 candidatos (≈30 %) salen del decodificador distintos de la propuesta, en todas las políticas.
