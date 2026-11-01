# Protocolo experimental de la segunda entrega

Versión 2.0.0, 1 de noviembre de 2026. Esta versión sustituye el
[protocolo v1](../entrega2_v1/README.md) antes de ejecutar la campaña.
La especificación de parámetros y reglas está en
[protocolo.json](protocolo.json) y el inventario en
[instancias.csv](instancias.csv).

## Pregunta, alcance y trazabilidad

Se evaluará si seleccionar movimientos mediante el controlador D-MAB completo
mejora Tabu Search frente a elegir los mismos movimientos uniformemente,
bajo igual presupuesto, representación, inicialización, planificador y
función objetivo. El controlador combina UCB1 escalado y Page-Hinkley.
El aprendizaje actúa en la evolución de la búsqueda: la elección del tipo
de movimiento con que se genera cada vecino.

La comparación utiliza una trayectoria por método. La cartera, los dos
reinicios uniformes y la variante sin detector no forman parte de esta
campaña. Los eventos de Page-Hinkley describirán su comportamiento, pero
no permitirán aislar su contribución causal sin una ablación independiente.
El estudio evalúa el controlador completo, sin anticipar su superioridad.
El código de referencia es la revisión 8817a5f. **La campaña de este
protocolo no se ha ejecutado.**

Se conservan doce instancias sintéticas oficiales, tres de cada tamaño
15, 20, 25 y 30, obtenidas de
[OII464_Hospitales](https://github.com/Saicooh/OII464_Hospitales), revisión
ecd30e3dbc1962d856c09b3470d1870c3b139a9a. El inventario registra los SHA-256
de los archivos usados. Se comprobarán esas huellas antes de cada campaña.
El repositorio oficial se utiliza como fuente y no se modifica.

El catálogo ya es conocido por el proyecto. Nuevas semillas miden variación
de búsqueda condicionada a estos problemas, no generalización a instancias
no vistas. La extensión a 50, 100 y 150 cirugías tendrá una especificación
separada de generación, número de casos y admisión anterior a la comparación
de métodos; esas instancias se reservarán de la calibración posterior.

## Siglas y configuraciones

| Sigla | Experimento | Decisión sobre movimientos | Evaluaciones |
|---|---|---|---:|
| **TS-U** | Tabu Search con selección uniforme | Selecciona cada uno de los cinco movimientos con igual probabilidad. | 6.060 |
| **TS-DMAB** | Tabu Search con bandido multibrazo dinámico | UCB1 aprende qué movimientos elegir; Page-Hinkley detecta caídas de recompensa y reinicia las estimaciones. | 6.060 |

TS significa Tabu Search; U, selección uniforme; y DMAB, Dynamic Multi-Armed
Bandit. Page-Hinkley conserva el calendario, la memoria y el archivo de
Tabu: solo reinicia las estimaciones del controlador. Detecta cambios en
las recompensas y no certifica la presencia de un óptimo local.

Cada configuración tendrá treinta repeticiones por instancia, con semillas
80-109. Una pareja usa la misma instancia, semilla y treinta soluciones
iniciales: FIFO, SPT, LPT y veintisiete alternativas aleatorias. Los sorteos
posteriores pueden divergir según los movimientos generados. El pareamiento
se fundamenta en el inicio y la instancia compartidos; no se presupone
sincronización perfecta de todos los números aleatorios.

Se fijan quince candidatos por lote, memoria de siete soluciones y prioridad
de pacientes con espera del motor de referencia (probabilidad 0,65).
TS-DMAB utiliza C=0,1, delta=0,01 y lambda=1. No se ajustarán esos parámetros
con las semillas de evaluación. Cualquier calibración posterior empleará
datos de desarrollo y una versión distinta del protocolo. FIFO, SPT y LPT
se calcularán una vez por instancia como referencias deterministas,
además de integrar la inicialización; no son configuraciones aleatorias
adicionales ni forman parte del contraste principal.

## Presupuesto y tamaño de la campaña

La unidad es una valoración de candidato, incluidas las treinta iniciales
de cada corrida. La reparación constructiva no calcula la función objetivo
completa. Los duplicados descartados sin valoración no consumen otra
evaluación; sí se registrarán los intentos y su costo. Si se vuelve a valorar
un candidato repetido entre lotes, esa llamada consume presupuesto.
Las treinta valoraciones iniciales siempre cuentan, incluso si algunas
soluciones coinciden tras la reparación. La revalidación del mejor calendario
final se registra aparte y su costo se incluye en el tiempo total.

La campaña principal prevé:

- **720 registros:** 12 instancias × 30 repeticiones × 2 configuraciones.
- **720 trayectorias:** una por registro.
- **4.363.200 valoraciones:** 720 × 6.060.
- Parada exacta por el presupuesto de 6.060 valoraciones de cada método.

Una iteración de búsqueda no equivale a una evaluación. En ambas
configuraciones se mantienen los cinco movimientos, la reparación y las
restricciones estrictas, incluida la espera máxima y la limpieza.

## Comparación secundaria por tiempo

Se compararán TS-U y TS-DMAB con diez segundos de búsqueda por corrida,
en las mismas doce instancias y treinta semillas: **720 registros
adicionales**. Esta campaña será separada; la parada temporal sustituye
a la parada por número de evaluaciones.

- El reloj monotónico inicia antes de construir las soluciones iniciales.
- Se comprueba el plazo antes de generar cada candidato, incluidos los iniciales.
- La unidad atómica comprende generación, reparación y valoración del candidato.
- Cada corrida tiene un plazo propio t0+10 segundos y una sola trayectoria.
- La última unidad iniciada dentro del plazo puede finalizar y aportar su
  resultado; se registra el sobrepaso y no comienza otro candidato.
- Ese sobrepaso atómico permitido no constituye un fallo de cuota.
- Se registran inicializaciones incompletas, tiempo de búsqueda y tiempo
  total, incluida la validación final.

Diez segundos es un presupuesto fijado a priori, no una duración observada.
La implementación del criterio temporal debe verificarse antes de ejecutar
su campaña. Si no fuera viable completar la inicialización, cualquier
modificación del plazo requerirá una enmienda previa a una nueva campaña,
preservando los registros existentes.

El único contraste temporal TS-DMAB frente a TS-U será secundario y
exploratorio, sin corrección por comparaciones múltiples al existir una
sola comparación en esa familia. No reemplazará el contraste principal
por evaluaciones si su resultado fuera más favorable.

## Métricas y efecto mínimo relevante

La métrica primaria es el objetivo ponderado f del informe, con coeficientes
1 para makespan, 0,000001 para la suma de inicios de reserva, 0,5 para espera
total y 1,4 para espera máxima. Menor f es mejor.

Se reportarán aparte makespan con limpieza, esperas total y máxima,
factibilidad, tiempo, evaluaciones, convergencia, dispersión entre semillas
y frecuencias de operadores, reparaciones y reinicios del controlador.
Las curvas usarán puntos comunes del presupuesto: 10, 50 y 100%.

Para cada instancia i, m_c y m_a son las medianas de las treinta corridas
de TS-U y TS-DMAB, respectivamente. La ganancia interpretable es
g_i = 100 × (m_c - m_a) / m_c; un valor positivo favorece a TS-DMAB.

El efecto mínimo relevante es **1% de reducción del objetivo ponderado**;
no equivale a 1% del makespan. Se reportarán la estimación, su intervalo,
el contraste estadístico y si alcanza ese umbral. Una estimación puntual
de al menos 1% cumple el umbral práctico; un límite inferior del intervalo
de al menos 1% respalda una afirmación más fuerte.

La tolerancia numérica 1e-9 se aplica a diferencias y empates; se conservan
los objetivos crudos. No se transforman valores pequeños en óptimos ni
diferencias menores al efecto mínimo relevante en empates estadísticos.

## Inferencia planificada

Se fija alfa=0,05 bilateral. La unidad global es la instancia: doce pares
de medianas, sin tratar las 360 corridas de un método como problemas
independientes. Para inferencia se usará la diferencia simétricamente
normalizada d_i = (m_c - m_a) / max(m_c, m_a). El denominador es invariante
al intercambio de etiquetas; g_i se conserva para interpretar la relevancia.

### Único contraste principal: TS-DMAB frente a TS-U

Se aplicará Wilcoxon bilateral sobre d_i. Su hipótesis nula requiere
simetría de las diferencias alrededor de cero. Al fijar un solo contraste
global, no corresponde aplicar Holm a esta familia. Se tratarán ceros
y empates con la convención Pratt; se enumerarán todas las permutaciones
de signos de las diferencias no nulas (como máximo 4.096).

Se fija la prueba binomial bilateral de signos como sensibilidad ante
asimetría; se reportarán ambas sin escoger la que dé menor valor p.
Si todas las diferencias son cero tras la tolerancia, se registrarán
estadístico cero y p=1; la sensibilidad también devuelve p=1 sin llamar
a una prueba binomial con n=0. Esto describe ausencia de diferencias
observadas y no demuestra equivalencia.

### Comparaciones exploratorias por instancia

Se aplica el mismo contraste a las treinta repeticiones emparejadas de
cada instancia, normalizando simétricamente cada diferencia. Las doce
pruebas forman una familia exploratoria con corrección de Holm. Para
las permutaciones se fijan 99.999 remuestreos, con semillas independientes
de la búsqueda.

Friedman y sus comparaciones post hoc no se aplican al diseño vigente,
porque solo se comparan dos métodos. La variante sin Page-Hinkley puede
estudiarse con un protocolo posterior, sin incorporarla a esta campaña.

### Efectos e intervalos

Se informará la mediana de g_i y su intervalo de confianza de 95% mediante
5.000 remuestreos jerárquicos: instancias con reposición y, dentro de ellas,
semillas emparejadas, manteniendo juntos ambos métodos y recalculando
las medianas. Por instancia se remuestrean parejas de repeticiones.

A12 será un descriptivo marginal opcional: proporción de todos los duelos
en que TS-DMAB obtiene menor objetivo que TS-U, más medio peso para empates.
A12>0,5 favorece a TS-DMAB; no representa la proporción de victorias de
igual semilla. Su bootstrap conservará la dependencia del diseño.

Las semillas estadísticas base son 55.000 para Wilcoxon y 55.002 para
bootstrap. Se derivará un generador por papel, contraste e instancia con
SeedSequence, usando orden canónico de identificadores; el orden del análisis
no cambiará los sorteos. No rechazar una hipótesis no demuestra equivalencia.
Treinta repeticiones no garantizan potencia de 80% para detectar 1%:
la inferencia global dispone de doce instancias.

## Fallos, integridad y publicación de registros

El contraste global exige treinta corridas válidas de ambos métodos en
las doce instancias. Las restricciones incumplidas, los valores no finitos,
los errores técnicos y los fallos de cuota no se omiten ni se reemplazan
por otra semilla. Se informarán cobertura, causa y tasa de fallos; si falta
alguna celda, la comparación correspondiente quedará incompleta y no evaluable
bajo esta versión. No se emitirá una conclusión global sobre un subconjunto
seleccionado por sus resultados.

El fallo temporal consiste en iniciar otro candidato fuera de plazo o
ignorar el límite de su corrida. El sobrepaso atómico final permitido y
registrado no es un fallo. Las correcciones se documentarán como enmiendas
o versiones, preservando los registros originales.

El entorno de referencia será macOS/arm64, Python 3.12.14, NumPy 2.3.5,
SciPy 1.18.1, PyYAML 6.0.3 y Matplotlib 3.11.2. Antes de ejecutar se
registrarán CPU, memoria, versiones efectivas y revisión del código.
Se utilizará un único proceso de búsqueda a la vez, sin otras cargas de
cálculo concurrentes. El orden de los dos métodos se alternará por repetición:
cada método se ejecutará primero quince veces por instancia, y el orden
real quedará registrado.

Se guardarán CSV de corridas, calendarios finales, trazas, eventos del
controlador, huellas recursivas de los archivos ejecutados y manifiesto del
entorno. Antes del análisis se verificarán cobertura, claves únicas,
presupuesto y factibilidad. Las salidas tendrán un directorio propio y no
sobrescribirán los resultados de protocolos anteriores.

## Relación con el informe

La sección [Configuración experimental](../../../informe/entrega_2/secciones/configuracion_experimental.tex)
resume este protocolo. El informe no presenta resultados preliminares.
La ejecución de las campañas y las diapositivas corresponden a etapas
posteriores; los algoritmos existentes no se modifican en esta revisión.
