# Protocolo pre-registrado de la Entrega 3: confirmación de UCB1 sin reinicio

**Estado:** congelado antes de ejecutar cualquier corrida de esta entrega
(2026-11-15). Este archivo no se edita después de su commit. Todo cambio
posterior se anota en `docs/protocolo-entrega3-desviaciones.md`, con fecha,
motivo y efecto. El protocolo de la Entrega 2 (`docs/protocolo-entrega2.md`,
commit `a0da669`) sigue vigente y no se modifica.

## 1. Origen y pregunta

El estudio de congestión de la Entrega 2 incluyó una lectura exploratoria, no
pre-registrada (nota N3 del registro de desviaciones). En las semillas 90–109,
la diferencia `UCB1 − Tabu uniforme` con 3.030 evaluaciones fue −2,617, con IC
95 % [−3,904; −1,345] (`experiments/results/entrega2_exploratorio/`). Ese
contraste no integró la familia C1–C4 ni tuvo corrección múltiple. Por tanto,
es una hipótesis y no un resultado.

**Pregunta.** Bajo congestión y con igual presupuesto, ¿Tabu con UCB1 sin
reinicio Page–Hinkley obtiene menor `f` que Tabu uniforme?

Este protocolo define una sola comparación confirmatoria, con semillas nuevas.

## 2. Hipótesis y regla de decisión

**Métrica primaria.** El objetivo combinado de `objective.py`, sin cambios:

`f = Cmax + 1e-6 × Σ inicios + 0,5 × Σ esperas + 1,4 × espera máxima`.

**H1c (falsable).** En el catálogo de congestión, con 3.030 evaluaciones, Tabu
con UCB1 sin reinicio obtiene menor `f` medio que Tabu uniforme. La diferencia
pareada `UCB1 − uniforme` es negativa.

**H0.** La mediana de las medias por instancia de esa diferencia es cero.

**Regla de decisión.** Es la misma regla de C1. H1c queda respaldada solo si se
cumplen las tres condiciones:

1. `p` de Wilcoxon menor que 0,05.
2. IC 95 % agrupado completamente bajo cero.
3. Media pareada menor o igual que −0,25.

Hay una sola comparación. Por eso no se aplica corrección múltiple: Holm sobre
una familia de tamaño uno deja `p` sin cambios. Cualquier otro resultado no
respalda H1c. La falta de significación no prueba equivalencia entre métodos.
El resultado se informa tal cual salga, a favor o en contra.

## 3. Datos

Las 48 instancias de `instances/congestion/` (catálogo `congestion-v1`), sin
cambios. El manifiesto guarda el SHA-256 de cada archivo.

## 4. Semillas

Semillas 120–139: 20 por instancia y 960 pares instancia–semilla. Salen de la
reserva «120 en adelante» del protocolo de la Entrega 2. Las semillas 0–119 y
1.000.060–1.000.109 están consumidas y no se reutilizan. Las semillas 90–109
no se amplían ni se combinan con este estudio.

## 5. Métodos, presupuesto y conteo

- Referencia: Tabu uniforme. Alternativa: Tabu + UCB1 (política `ucb`, es
  decir, el bandido con `dynamic=False`).
- Configuración: `TabuConfig()` por defecto, sin cambios. `C=0,1`, tenure 7
  sobre firmas de solución, 15 candidatos por lote y 30 soluciones iniciales.
  `delta` y `lambda` no actúan en UCB1.
- Presupuesto y parada: 3.030 evaluaciones por camino, incluidas las 30
  iniciales. El conteo es el de la sección 4 del protocolo de la Entrega 2.
- Emparejamiento: ambas trayectorias reciben la misma instancia y semilla.
- D-MAB no se ejecuta aquí. C4 ya comparó D-MAB con UCB1 de forma confirmatoria.
- Sin cambios en `src/` ni en `experiments/results/` archivados. Los
  verificadores históricos deben seguir pasando al terminar.

## 6. Estadística

- **Diferencia:** `UCB1 − uniforme`. Un valor negativo favorece a UCB1.
- **Unidad de análisis:** la instancia. Primero se promedian las 20 semillas.
- **Prueba:** Wilcoxon de rangos con signo, bilateral, sobre las medias por
  instancia, con `zero_method="zsplit"`.
- **Incertidumbre:** bootstrap jerárquico de instancias y semillas emparejadas,
  5.000 réplicas, generador con semilla 20261102. Se usa la misma función
  `clustered_interval` del estudio de congestión.
- **Umbral práctico:** 0,25 unidades de `f`.
- **Secundarias, solo descriptivas:** `Cmax`, espera total, espera máxima,
  proporción de soluciones con espera, factibilidad, reparación, tiempo y
  evaluación de la última mejora.
- **Tamaño fijado de antemano:** 48 instancias × 20 semillas = 960 pares.
- **Sin parada opcional:** no se agregan ni quitan semillas o instancias según
  el resultado. El script no calcula ningún estadístico hasta terminar todos
  los pares.
- **Fallos:** si una corrida falla, el par se excluye y se informa el conteo.
  Si falla más de 1 % de los pares, se registra una desviación y el resultado
  pasa a ser exploratorio.

## 7. Potencia de planificación

La planificación usa el contraste exploratorio de las semillas 90–109. La DE de
las medias por instancia de `UCB1 − uniforme` fue 3,508
(`entrega2_congestion_90_109/runs.csv`). Con la aproximación t, 48 instancias y
`alfa=0,05` bilateral:

| Efecto supuesto | Potencia aproximada |
|---:|---:|
| 2,617 (el observado) | 1,00 |
| 1,309 (la mitad) | 0,72 |
| 0,65 | 0,24 |

El efecto observado puede estar inflado por haberse elegido después de mirar
los datos. Por eso se informa también la mitad. El script guarda este cálculo
en el manifiesto. Un resultado no significativo no probará equivalencia.

## 8. Ejecución, auditoría y fecha de corte

- Ejecución: `python -m experiments.confirm_ucb1 --workers 12`.
- Salida: `experiments/results/entrega3_confirmacion_ucb1/`, con manifiesto
  (hashes de código, instancias y protocolo, y commit), `runs.csv`,
  `solutions.jsonl`, `failures.csv`, `comparisons.csv`, `descriptive.csv` y
  `ANALYSIS.md`.
- Auditoría: `python -m experiments.verify_confirm_ucb1` recalcula cada
  calendario final con el planificador estricto y comprueba presupuesto,
  cobertura y hashes. Escribe `verification.json`.
- **Fecha de corte:** miércoles 18 de noviembre de 2026, 23:59. Si el estudio
  no termina antes, se abandona y queda como trabajo futuro. Los resultados
  parciales no se analizan.

## 9. Alcance y límites declarados

- Las semillas nuevas sobre el mismo catálogo confirman el contraste en estas
  48 instancias. No miden generalización a otros hospitales ni a instancias no
  vistas.
- El catálogo de congestión remuestrea el catálogo estándar y comparte su
  perfil de duraciones. No constituye un dominio independiente.
- Este estudio no evalúa una cartera con UCB1, ni compara UCB1 con Tabu
  prolongado o con dos Tabu independientes. Un resultado favorable no convierte
  a UCB1 en una propuesta evaluada con 6.060 evaluaciones.
- Los resultados no se mezclan en una misma tabla con estudios de otro
  presupuesto, catálogo o rango de semillas.
- Ningún estudio demuestra optimalidad. El control de cómputo es el número de
  evaluaciones; el tiempo depende del equipo y de su carga.
