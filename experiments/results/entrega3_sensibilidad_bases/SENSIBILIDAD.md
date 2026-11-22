# Sensibilidad exploratoria por instancia base

**No estaba pre-registrada y se eligió después de ver los resultados.** No confirma hipótesis ni reemplaza las decisiones de C1–C4 o E1.

- Único cambio: la unidad. Son 12 bases, cada una con sus 4 instancias y 80 pares, en lugar de 48 instancias con 20 pares.
- Wilcoxon, la familia de Holm, el bootstrap (función, réplicas y semilla) y los tres criterios son los registrados. Antes se reprodujo el análisis registrado.
- Con 12 unidades la prueba tiene menos potencia: perder significación no prueba ausencia de efecto.
- C1–C4 y E1 son estudios distintos; por eso van en tablas separadas.
- Razón de EE: error estándar de las medias por base sobre el de las medias por instancia. Sobre 1, la unidad registrada daba más precisión que esta.

## Semillas 90–109

| Id | Media | IC 95 % | p | p Holm | Bases con media negativa | Razón de EE | Criterios por instancia | Criterios por base |
|---|---:|---|---:|---:|---:|---:|---|---|
| C1 | -0,793 | [-1,786; +0,176] | 0,002 | 0,010 | 10 de 12 | 0,815 | no cumple | no cumple |
| C2 | -1,380 | [-2,844; +0,123] | 0,064 | 0,192 | 10 de 12 | 1,627 | cumple | no cumple |
| C3 | -0,409 | [-1,124; +0,288] | 0,204 | 0,204 | 8 de 12 | 1,093 | no cumple | no cumple |
| C4 | +1,824 | [+0,085; +3,566] | 0,092 | 0,192 | 4 de 12 | 1,619 | cumple | no cumple |

## Semillas 120–139

| Id | Media | IC 95 % | p | p Holm | Bases con media negativa | Razón de EE | Criterios por instancia | Criterios por base |
|---|---:|---|---:|---:|---:|---:|---|---|
| E1 | -2,749 | [-4,335; -1,191] | 0,005 | 0,005 | 11 de 12 | 1,352 | cumple | cumple |
