# Segunda entrega: configuración experimental

## Documento y fuentes

- [Informe completo](Entrega_2_Tabu_DMAB.pdf).
- [Fuente principal](main.tex).
- [Configuración experimental](secciones/configuracion_experimental.tex).
- [Protocolo vigente v2](../../experiments/protocols/entrega2_v2/README.md).
- [Parámetros y reglas](../../experiments/protocols/entrega2_v2/protocolo.json).
- [Inventario de instancias](../../experiments/protocols/entrega2_v2/instancias.csv).
- [Comprobaciones de formato y coherencia](verificacion.json).

El informe completo tiene diez páginas físicas: portada, resumen,
introducción, dos páginas de propuesta, tres de configuración experimental,
conclusión y referencias. La sección nueva ocupa las páginas físicas 6-8,
con folios 5-7, dentro del máximo de tres páginas de la pauta.

Se mantiene el formato institucional: papel carta, Times de 12 puntos,
márgenes de 2,5 cm e interlineado sencillo. La portada conserva título,
autores y fecha 2 de noviembre de 2026. Resumen e introducción comienzan
en hojas diferentes y la conclusión ocupa una hoja propia, en dos párrafos
y menos de media página.

## Propuesta vigente y siglas

| Sigla | Experimento | Evaluaciones por corrida |
|---|---|---:|
| TS-U | Tabu Search con selección uniforme de los cinco movimientos. | 6.060 |
| TS-DMAB | Tabu Search con UCB1 y Page-Hinkley, componentes del controlador D-MAB completo. | 6.060 |

La tabla de siglas también aparece en la sección experimental del informe.
Cada configuración realiza una búsqueda y devuelve su propio mejor calendario.
El aprendizaje actúa en la evolución de Tabu, al seleccionar el tipo de movimiento.
UCB1 aprende de las recompensas; Page-Hinkley detecta caídas y reinicia las
estimaciones del bandido, conservando la solución y la memoria de Tabu.
Los eventos del detector serán descriptivos: no aislarán su efecto causal.

La comparación principal utiliza doce instancias, treinta repeticiones,
semillas 80-109 y 720 corridas. El presupuesto incluye las treinta soluciones
iniciales. Se fija 1% del objetivo ponderado como mejora mínima relevante;
makespan y esperas se reportan aparte. La comparación temporal secundaria
asigna diez segundos por método, en otras 720 corridas.

El análisis principal será Wilcoxon bilateral sobre doce pares de medianas,
sin corrección múltiple al existir un único contraste global. Las doce
comparaciones exploratorias por instancia usarán Holm. Se incluyen intervalos,
medidas de efecto, sensibilidad, reglas de empates, integridad y fallos.

**Estado:** diseño especificado; campañas pendientes de ejecución.
El criterio temporal y el análisis deben implementarse y verificarse antes
de ejecutar la campaña correspondiente. El informe no presenta resultados
preliminares ni prepara la presentación oral.

## Versiones

El protocolo v2 sustituye al [protocolo v1](../../experiments/protocols/entrega2_v1/README.md)
antes de ejecutar su campaña. Los archivos de la
[primera entrega](../README.md) permanecen como documento histórico.
El informe actual actualiza resumen, introducción, propuesta, configuración
experimental y conclusión para describir la comparación TS-U/TS-DMAB.
La cartera y la variante sin detector no forman parte del diseño vigente.

## Compilación

Desde este directorio, en una distribución con LaTeX y Biber:

~~~bash
latexmk -pdf -interaction=nonstopmode -halt-on-error \
  -jobname=Entrega_2_Tabu_DMAB main.tex
~~~

La carpeta es un proyecto LaTeX autónomo con estilo institucional, portada,
imagen, sección incluida y bibliografía. El estilo y la imagen conservan
los archivos de la plantilla institucional.

## Revisión

Se comprueban extensión de la sección, coherencia de parámetros y presupuestos,
definiciones de variables bajo las ecuaciones, legibilidad de tablas y citas,
ausencia de resultados atribuidos a campañas no ejecutadas y correspondencia
entre informe, protocolo e inventario.
