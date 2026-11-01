# Programación de cirugías electivas mediante búsqueda tabú y selección adaptativa de movimientos

Proyecto de **OII464: Desarrollo de Diseños Híbridos para Optimización**.
Se estudia si incorporar aprendizaje en línea a Tabu Search permite mejorar
la programación de cirugías frente a seleccionar sus movimientos uniformemente.

Integrantes: **José Basualto, Cristopher Dauros y Carlos Ruz**.

## Propuesta vigente: Tabu Search + D-MAB

El aprendizaje interviene en la **evolución de la búsqueda**, seleccionando
el tipo de movimiento con que se genera cada vecino. El controlador D-MAB
incluye **UCB1 y Page-Hinkley**: UCB1 aprende de las recompensas y equilibra
exploración y explotación; Page-Hinkley detecta caídas en esas recompensas y
reinicia las estimaciones del bandido. Mantiene el estado de Tabu y no
identifica directamente un óptimo local.

La evaluación vigente comprende dos configuraciones independientes:

| Sigla | Configuración | Evaluaciones por corrida |
|---|---|---:|
| **TS-U** | Tabu Search con selección uniforme de movimientos. | 6.060 |
| **TS-DMAB** | Tabu Search con selección aprendida mediante D-MAB completo: UCB1 y Page-Hinkley. | 6.060 |

Ambas comparten operadores, inicialización, restricciones y objetivo. Cada
corrida devuelve su propio mejor calendario factible. El presupuesto incluye
las treinta soluciones iniciales: FIFO, SPT, LPT y veintisiete aleatorias.
La comparación evalúa el efecto del controlador completo; no atribuye por
separado una mejora a Page-Hinkley.

Consulta la [arquitectura](docs/arquitectura-final.md), la
[metodología](docs/metodologia-experimental.md) y el
[protocolo vigente](experiments/protocols/entrega2_v2/README.md).

## Segunda entrega

- [Informe completo](informe/entrega_2/Entrega_2_Tabu_DMAB.pdf).
- [Fuentes y detalles de compilación](informe/entrega_2/README.md).
- [Configuración experimental en LaTeX](informe/entrega_2/secciones/configuracion_experimental.tex).
- [Protocolo versionado](experiments/protocols/entrega2_v2/README.md) e
  [inventario de instancias](experiments/protocols/entrega2_v2/instancias.csv).

Se fijan doce instancias de 15, 20, 25 y 30 cirugías, treinta repeticiones
por método e instancia y semillas 80-109: **720 registros principales**.
El efecto mínimo relevante es **1% del objetivo ponderado**, con makespan
y esperas reportados por separado. Como fase secundaria se especifica una
comparación con diez segundos por algoritmo y corrida, también de 720 registros.

**Estado:** protocolo definido; sus campañas no se han ejecutado. El criterio
temporal y el análisis deben implementarse y verificarse antes de ejecutar
esa campaña. El informe presenta la metodología y no resultados preliminares.

## Problema, objetivo y restricciones

Cada solución contiene un orden de pacientes y asignaciones de sala para
anestesia y cirugía. Un planificador estricto asigna personal elegible y
comprueba precedencias, disponibilidad, preparación, transición, limpieza y
espera máxima entre etapas. Las salas pueden diferir entre etapas y no se
impone equilibrio entre pabellones. La reparación puede modificar preferencias
de sala y orden para conseguir factibilidad y restringe los calendarios alcanzables.

Se minimiza:

`f = Cmax + 1e-6 × suma de inicios + 0,5 × espera total + 1,4 × espera máxima`.

`Cmax` es el término de la última operación, incluida su limpieza. La suma
de inicios considera el comienzo de preparación o reserva. La espera se mide
desde el fin de anestesia, incluida su limpieza, hasta el inicio del
procedimiento quirúrgico. Los tiempos están en minutos; `f` es un objetivo
combinado, no exclusivamente la duración de la jornada.

D-MAB aprende durante cada corrida, sin entrenamiento previo con etiquetas.
La calibración posterior utilizará datos de desarrollo separados de la evaluación.

## Instalar y utilizar el motor

Se requiere Python 3.11 o posterior. Desde la raíz:

```bash
python -m venv .venv
.venv/bin/python -m pip install -e '.[test]'
.venv/bin/python -m pytest -q
```

La API actual admite las dos políticas y el presupuesto fijado:

```python
from surgery_optim.instances import load_instance
from surgery_optim.tabu import TabuConfig, run_tabu

context = load_instance("instances/standard/HOSP-STD-30-01.yaml")
config = TabuConfig(evaluation_budget=6060)
for label, policy in (("TS-U", "uniform"), ("TS-DMAB", "dmab")):
    result = run_tabu(context, seed=80, policy=policy, config=config)
    print(label, result.final_quality.objective, result.evaluations)
```

Este ejemplo muestra una pareja de corridas; no ejecuta ni registra la campaña
completa del protocolo. La implementación está en
[`src/surgery_optim/tabu.py`](src/surgery_optim/tabu.py) y
[`src/surgery_optim/bandit.py`](src/surgery_optim/bandit.py).

## Versiones y estudios anteriores

La [primera entrega](informe/README.md), con su
[fuente](informe/main.tex) y [PDF](informe/Entrega_1_Tabu_DMAB.pdf), se conserva
como documento histórico independiente. El diseño de seis configuraciones de
[Entrega 2 v1](experiments/protocols/entrega2_v1/README.md) fue sustituido
antes de ejecutar su campaña por el protocolo vigente de dos configuraciones.

Los estudios anteriores y sus datos se preservan con los parámetros y
manifiestos que los produjeron:

| Ruta | Contenido histórico |
|---|---|
| [Exploración 0-19](experiments/results/exploratory_0_19/) | Pilotos iniciales. |
| [Validación 20-39](experiments/results/validation_20_39/) | Configuración inicial. |
| [Calibración 0-5](experiments/results/calibration_0_5/) | Calibración de la segunda configuración del motor. |
| [Validación 40-59](experiments/results/validation_40_59/) | Comparación de políticas con 3.030 evaluaciones. |
| [Carteras 60-79](experiments/results/portfolios_60_79/) | Carteras y reparto de presupuesto. |

La [guía de experimentos](experiments/README.md) documenta sus comandos.
El [protocolo de carteras](docs/protocolo-carteras.md), su
[decisión histórica](experiments/results/portfolios_60_79/DECISION.md), el
[módulo de cartera](src/surgery_optim/portfolio/) y el
[ejemplo conservado](outputs/final/HOSP-STD-30-01-seed60.json) corresponden
al diseño anterior. No forman parte de la comparación vigente TS-U/TS-DMAB.
Los resultados archivados no se presentan como resultados de la nueva campaña.

## Procedencia y alcance

Las doce instancias son sintéticas y coinciden con el
[repositorio oficial del caso](https://github.com/Saicooh/OII464_Hospitales)
en la revisión `ecd30e3dbc1962d856c09b3470d1870c3b139a9a`.
No son pacientes reales ni los cuatro JSON históricos de la presentación.
El repositorio oficial se utiliza como fuente y permanece sin modificaciones.

El modelo aborda una agenda estática. La asignación de personal es
constructiva y la búsqueda no recorre todos los calendarios factibles.
No se demuestra optimalidad global. La ampliación a tamaños y congestión
mayores se especificará por separado; cancelaciones, urgencias y
replanificación durante la jornada son extensiones pendientes.
