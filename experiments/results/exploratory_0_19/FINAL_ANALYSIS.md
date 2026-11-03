# Prueba de controladores de movimientos para Tabu Search

## Protocolo

Se usaron las 12 réplicas YAML estándar (15, 20, 25 y 30 cirugías, tres réplicas por tamaño), 20 semillas por réplica y 3.030 evaluaciones estrictas por corrida. La población inicial, las reglas FIFO/SPT/LPT, el decodificador factible y el objetivo sin equilibrio son compartidos. El simulador impide exceder `max_wait`.

Se hicieron dos experimentos distintos:

1. **Por lote:** uniforme, D-MAB y LinUCB eligen un tipo de movimiento para 15 candidatos. Esta arquitectura cambia la mezcla del Tabu original.
2. **Por candidato:** D-MAB y LinUCB eligen un movimiento para cada propuesta. La política uniforme reproduce exactamente el Tabu mixto anterior; las demás reglas de búsqueda son iguales.

D-MAB usa UCB1 y detección Page-Hinkley. LinUCB usa progreso, estancamiento, bloqueo, dispersión de salas y distancia entre la solución actual y la mejor. Cada recompensa se basa en la mejora local por evaluación, escalada al 2 % del objetivo inicial. Son modelos online que se reinician en cada corrida.

## Resultado principal: elección por candidato

Valores: mediana del objetivo en 20 semillas; menor es mejor.

| Instancia | Tabu mixto | Tabu + D-MAB | Tabu + LinUCB |
|---|---:|---:|---:|
| HOSP-STD-15-01 | 144.50 | 145.75 | 145.75 |
| HOSP-STD-15-02 | 171.00 | 169.50 | 172.00 |
| HOSP-STD-15-03 | 154.50 | 155.00 | 155.75 |
| HOSP-STD-20-01 | 181.75 | 182.00 | 182.00 |
| HOSP-STD-20-02 | 207.00 | 207.00 | 207.00 |
| HOSP-STD-20-03 | 200.40 | 199.73 | 201.75 |
| HOSP-STD-25-01 | 222.75 | 223.00 | 223.00 |
| HOSP-STD-25-02 | 256.93 | 254.25 | 256.00 |
| HOSP-STD-25-03 | 236.50 | 234.75 | 234.50 |
| HOSP-STD-30-01 | 258.76 | 255.51 | 260.51 |
| HOSP-STD-30-02 | 300.26 | 296.51 | 297.26 |
| HOSP-STD-30-03 | 263.51 | 263.51 | 263.51 |

| Política aprendida | Réplicas con mejora > 0,1 min | Réplicas con deterioro > 0,1 min | Empates | Mediana de diferencia (min) | IC bootstrap 95 % |
|---|---:|---:|---:|---:|---|
| DMAB | 6/12 | 4/12 | 2/12 | -0.34 | [-2.21, +0.25] |
| LinUCB | 3/12 | 7/12 | 2/12 | +0.25 | [-0.46, +1.25] |

Los intervalos remuestrean las **12 medianas de instancia**, no las 240 corridas como si fueran independientes. Son exploratorios: el intervalo de D-MAB incluye cero. En las 12 instancias, la prueba emparejada de Wilcoxon entrega p=0.151 para D-MAB y p=0.520 para LinUCB; no se deben interpretar como confirmación después de explorar varias variantes.

Las medianas de bloqueo de las tres políticas por candidato son cero en las 12 réplicas. Las 720 corridas (240 por política) usaron exactamente 3.030 evaluaciones cada una; todas las soluciones evaluadas fueron factibles. La mediana de tiempo por corrida fue 0.97 s para Tabu mixto, 0.97 s para D-MAB y 1.11 s para LinUCB.

## Por qué importó la granularidad

En el experimento por lote, D-MAB mejoró al uniforme en 7/12 réplicas y empeoró en 1/12, pero quedó por detrás del Tabu mixto anterior en 8/12. Agrupar todos los candidatos bajo un solo tipo de movimiento perjudicó a la búsqueda. Elegir por candidato recuperó el rendimiento base y produjo algunas mejoras, especialmente en dos réplicas de 30 cirugías.

## Conclusión

D-MAB por candidato es la opción aprendida más prometedora de las probadas, pero **todavía no hay una mejora general demostrada** sobre Tabu mixto: 6 réplicas mejoran, 4 empeoran y 2 empatan. LinUCB no muestra ventaja con estas señales y parámetros. Para el proyecto, conservaría Tabu mixto como base y D-MAB por candidato como hipótesis de componente ML; antes de afirmarlo como beneficio, probaría más instancias y una recompensa menos dispersa, con parámetros fijados antes de evaluar nuevas réplicas.

## Archivos

- `candidate_evidence.png/pdf`: efecto por instancia y frecuencia de movimientos.
- `legacy_mixed_runs.csv`, `candidate_runs.csv`: corridas individuales.
- `candidate_decisions.csv`: decisiones y recompensas durante cada corrida.
- `candidate_paired_vs_legacy.csv`: diferencias por semilla e instancia.
- `manifest.json`, `legacy_manifest.json`, `candidate_manifest.json`: instancias, parámetros y hashes del código.
