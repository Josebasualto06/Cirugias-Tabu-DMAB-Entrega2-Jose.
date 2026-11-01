> **Protocolo histórico sustituido.** La versión vigente es [entrega2_v2](../entrega2_v2/README.md), centrada en TS-U frente a TS-DMAB completo. Esta versión se conserva como especificación anterior; su campaña no se ejecutó.

# Protocolo experimental de la segunda entrega

Versión 1.0.0, 1 de noviembre de 2026. El diseño se fija antes de ejecutar su
campaña. La especificación legible por máquina está en
[protocolo.json](protocolo.json) y el inventario de datos en
[instancias.csv](instancias.csv).

## Alcance y trazabilidad

La propuesta conserva la función objetivo, representación, factibilidad y
arquitectura de la primera entrega: selección de movimientos de Tabu mediante
D-MAB y cartera fija con selección final determinista. El código de referencia
es la revisión 35a8344. La campaña de este protocolo no se ha ejecutado.

El catálogo contiene doce instancias sintéticas oficiales, tres de cada tamaño
15, 20, 25 y 30. La procedencia registrada es el repositorio
[OII464_Hospitales](https://github.com/Saicooh/OII464_Hospitales), revisión
ecd30e3dbc1962d856c09b3470d1870c3b139a9a. El inventario fija los SHA-256 de
los archivos usados. Se comprobarán las huellas antes de cada campaña.

La evaluación sobre este catálogo mide variación de búsqueda condicionada a
problemas conocidos. La extensión a 50, 100 y 150 cirugías tendrá una
especificación posterior de generación, número de casos y admisión anterior
a la comparación de métodos. Esas instancias no se usarán para calibrar
la configuración que luego se evalúe en ellas.

## Configuraciones

| Bloque | ID | Configuración | Presupuesto |
|---|---|---|---:|
| A | U | Tabu uniforme | 3.030 |
| A | M | Tabu con D-MAB | 3.030 |
| A | Q | Tabu con UCB1 sin Page-Hinkley | 3.030 |
| B | T | Tabu uniforme prolongado | 6.060 |
| B | R | Dos Tabu uniformes independientes | 3.030 + 3.030 |
| B | H | Cartera Tabu uniforme y Tabu con D-MAB | 3.030 + 3.030 |

R conserva el mejor calendario de sus dos reinicios. H conserva el de menor
objetivo de sus componentes; desempata por makespan y luego por el componente
uniforme. Ambas ejecuciones son secuenciales. El reparto de H es fijo.

Se realizarán treinta repeticiones por configuración e instancia, semillas
80-109. R usa s y s+1.000.000; H usa s en ambos caminos. El inicio compartido
fundamenta el pareamiento; los consumos aleatorios posteriores pueden divergir.

Los parámetros fijos son treinta soluciones iniciales (FIFO, SPT, LPT y
veintisiete alternativas aleatorias), quince candidatos por lote, memoria
de siete soluciones, C=0,1, delta=0,01 y lambda=1. Q y M difieren por la
activación del detector. Se mantiene la prioridad de pacientes con espera
del motor de referencia. FIFO, SPT y LPT se evaluarán una vez por instancia
como referencias deterministas.

## Presupuesto y tamaño de la campaña

La unidad es una valoración de candidato, incluidas las treinta iniciales
por camino. La reparación constructiva no calcula la función objetivo
completa. Los duplicados descartados sin valoración no consumen otra
evaluación; sí quedan registrados los intentos y su costo. Los candidatos
repetidos entre lotes que se vuelvan a valorar sí consumen presupuesto.
Las valoraciones de la población inicial siempre cuentan, aunque alguna
solución coincida tras la reparación. La revalidación del mejor final se
registra aparte, con su costo incluido en el tiempo total.

La campaña principal prevé:

- 2.160 registros de configuraciones: 12 × 30 × 6.
- 2.880 trayectorias de búsqueda: U, M, Q y T tienen una; R y H, dos.
- 9.817.200 valoraciones presupuestadas de candidatos.
- Todas las comparaciones inferenciales se realizan dentro de su presupuesto.

No se equiparará una iteración de búsqueda a una evaluación.

## Comparación secundaria por tiempo

Se compararán T, R y H en las doce instancias y las mismas treinta semillas:
1.080 registros adicionales. La parada temporal sustituye a la parada por
número de evaluaciones:

- T: diez segundos de búsqueda.
- R y H: dos cuotas nominales de cinco segundos, sin transferencia de sobrantes.
- Inicio de búsqueda: antes de construir las soluciones iniciales.
- Reloj monotónico; comprobación antes de generar cada nuevo candidato.
- La unidad atómica comprende generación, reparación y valoración de un candidato.
- Plazo global t0+10. Primera cuota hasta t0+5.
- La segunda cuota termina en min(inicio_real_segundo+5, t0+10).
- Un sobrepaso del primer camino se descuenta de la segunda cuota.
- Se registra cualquier sobrepaso de la última unidad atómica.
- La última unidad iniciada dentro del plazo puede finalizar y aportar
  su resultado; ese sobrepaso autorizado no constituye un fallo de cuota
  y no habilita otro candidato.
- Si el primer camino agota todo el plazo, el segundo no inicia otro candidato.
- Inicializaciones incompletas y fallos quedan explícitos en los registros.
- Se reportan tiempo de búsqueda y tiempo total, incluida la validación final.

Diez segundos es un presupuesto fijado a priori, no una duración observada.
La puesta a punto del criterio temporal es una tarea previa a ejecutar
esta fase. Si no fuera viable completar la inicialización, se declarará
una enmienda antes de una nueva campaña, preservando los registros existentes.

Las comparaciones H-T y H-R son una familia secundaria exploratoria de dos
pruebas, con Holm; no se mezclan con los contrastes principales por evaluaciones.

## Métricas y efecto mínimo relevante

La primaria es el objetivo ponderado f del informe. Sus coeficientes
son 1 para makespan, 0,000001 para la suma de inicios de reserva, 0,5 para
espera total y 1,4 para espera máxima. Menor f es mejor.

Se informan aparte makespan con limpieza, esperas total y máxima, factibilidad,
tiempo, evaluaciones, convergencia, dispersión entre semillas y comportamiento
de operadores/reparación/detector. Las curvas se alinean por porcentaje del
presupuesto, con puntos 10, 50 y 100%.

Para cada instancia i, m_c y m_a son las medianas de treinta corridas del
control y de la alternativa. La ganancia interpretable es
g_i = 100 × (m_c − m_a) / m_c. Positiva favorece a la alternativa.

El efecto mínimo relevante es **1% de reducción del objetivo ponderado**.
No equivale a 1% del makespan. Se publicarán por separado la estimación,
su intervalo, el contraste estadístico y si alcanza ese umbral. Una
estimación puntual de al menos 1% cumple el umbral práctico; un límite
inferior del IC de al menos 1% respalda una afirmación más fuerte.

La tolerancia numérica 1e-9 se aplica a diferencias y empates. Se conservan
objetivos crudos; no se transforman valores pequeños en óptimos ni
diferencias menores al EMR en empates estadísticos.

## Inferencia planificada

Se fija alfa=0,05 bilateral. La unidad global es la instancia; se usan doce
pares de medianas, no 360 observaciones supuestamente independientes.

Para los contrastes se usa la diferencia simétricamente normalizada:
d_i = (m_c − m_a) / max(m_c, m_a). El denominador es invariante al intercambio
de etiquetas. g_i se conserva como medida interpretable de relevancia.

### Familia principal por evaluaciones: cuatro contrastes globales

1. M-U: selección aprendida.
2. H-T: cartera frente a prolongar Tabu.
3. M-Q: detector Page-Hinkley.
4. H-R: control de dos reinicios.

Se aplicará Wilcoxon bilateral a d_i, con Holm conjunto sobre los cuatro
valores p. Su hipótesis nula requiere simetría alrededor de cero.
Los ceros, empates y redondeo se tratarán explícitamente; se usará la
convención Pratt. Con doce bloques se enumerarán las permutaciones de
signos de las diferencias no nulas. La prueba de signos se fija como
sensibilidad ante asimetría y no reemplazará la principal por conveniencia.
Si todas las diferencias son cero, se fijan estadístico cero y p=1,
conservando el contraste en su familia de Holm; la sensibilidad también
devuelve p=1 cuando no hay diferencias no nulas.

### Análisis exploratorio por instancia

Se repiten los cuatro contrastes con las treinta repeticiones emparejadas,
normalizando simétricamente cada diferencia. Los 48 contrastes forman una
familia con Holm. Para la distribución por permutaciones se fija un máximo
de 99.999 remuestreos y semillas independientes de la búsqueda.

### Análisis contextual de tres métodos

Friedman se aplicará por separado a U/M/Q y T/R/H, usando rangos con
corrección de empates sobre las medianas por instancia. La distribución
nula se aproximará con 100.000 permutaciones de etiquetas de métodos
dentro de cada instancia. Se calculará p=(b+1)/(100000+1), donde b cuenta
estadísticos tan o más extremos que el observado. No se llamará cálculo exacto.
Si todos los métodos empatan en todas las instancias, se fijan estadístico
cero y p=1, evitando una corrección de empates con denominador cero.

Los dos ómnibus se corrigen con Holm. Solo ante rechazo del ómnibus ajustado
se interpretan las tres parejas post hoc de su bloque, con Holm. No
se escogerá entre esta ruta y la familia principal para sustentar una
conclusión favorable: responden preguntas y roles declarados distintos.

### Efectos e intervalos

Se informará la mediana de g_i y su IC95% mediante 5.000 remuestreos
jerárquicos: instancias con reposición y semillas emparejadas dentro de cada
instancia, conservando todos los métodos juntos. Se recalculan las medianas.
Por instancia se remuestrean parejas de repeticiones.

A12 se ofrecerá como descriptivo marginal: proporción de todos los duelos
en que la alternativa obtiene menor objetivo, más medio peso para empates.
A12>0,5 favorece a la alternativa; no es la proporción de victorias del
pareo de igual semilla. Su bootstrap conservará la dependencia del diseño.

Las semillas estadísticas base son 55.000 (Wilcoxon), 55.001 (Friedman) y
55.002 (bootstrap). Se derivará un generador por papel, contraste e instancia
con SeedSequence; el orden de ejecutar análisis no cambiará sus sorteos.

No rechazar una hipótesis no demuestra equivalencia. Treinta repeticiones
no garantizan potencia de 80% para detectar 1%; la inferencia global
dispone de doce instancias y su incertidumbre debe acompañar las conclusiones.

## Fallos, integridad y publicación de registros

Cada contraste exige las treinta corridas válidas de los métodos comparados
en las doce instancias. Friedman exige completar su bloque. Una violación
de restricciones, un valor no finito, una cuota incumplida o un error técnico
no se omiten ni se reemplazan por otra semilla. Se informará cobertura,
causa y tasa de fallos, y el contraste correspondiente quedará no evaluable
bajo el protocolo fijado si falta alguna celda.
Incumplir la cuota significa iniciar otro candidato fuera de plazo,
transferir tiempo sin autorización o ignorar el plazo global; el sobrepaso
atómico final permitido y registrado no es un fallo.

Las correcciones se documentarán como enmiendas/versiones, preservando la
evidencia original. No se emitirá una conclusión global sobre un subconjunto
seleccionado por sus resultados.

El entorno de referencia es macOS/arm64, Python 3.12.14, NumPy 2.3.5,
SciPy 1.18.1, PyYAML 6.0.3 y Matplotlib 3.11.2. Antes de la ejecución se
registrarán CPU, memoria, versiones efectivas y revisión del código.
Se ejecutará un único proceso de búsqueda a la vez, sin otras cargas de cálculo.
El orden se balanceará por rotación de los tres métodos de cada bloque,
según la repetición, y se conservará en el registro.

Se guardarán CSV de corridas, calendarios finales, trazas, eventos del
controlador, huellas recursivas del código ejecutado y manifiesto del entorno.
Se comprobarán cobertura, claves únicas, presupuesto y factibilidad antes
del análisis. Las salidas de esta campaña tendrán un directorio propio y no
sobrescribirán las de otros protocolos.

## Relación con el informe

La sección [Configuración experimental](../../../informe/entrega_2/secciones/configuracion_experimental.tex)
resume este protocolo en el informe de segunda entrega. Su PDF no presenta
resultados experimentales; la ejecución de la campaña y las diapositivas son
trabajos posteriores.
