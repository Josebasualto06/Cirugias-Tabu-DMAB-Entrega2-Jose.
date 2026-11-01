# Segunda entrega: configuración experimental

## Documento para revisión

- [Informe completo](Entrega_2_Tabu_DMAB.pdf).
- [Fuente principal](main.tex).
- [Sección nueva](secciones/configuracion_experimental.tex).
- [Protocolo detallado](../../experiments/protocols/entrega2_v1/README.md).
- [Especificación de parámetros y reglas](../../experiments/protocols/entrega2_v1/protocolo.json).
- [Inventario de instancias](../../experiments/protocols/entrega2_v1/instancias.csv).
- [Comprobaciones de extensión, formato y preservación del texto](verificacion.json).

La sección **Configuración experimental** ocupa tres páginas, las páginas
físicas 6–8 del PDF, con folios 5–7. El documento completo tiene diez páginas:
portada, resumen, introducción, propuesta, sección experimental, conclusión
y referencias.

Se reutilizan el texto entregado y el formato institucional de la Escuela.
Resumen, introducción y conclusión conservan literalmente sus fuentes;
la conclusión pasa a numerarse como sección 4 al insertar la nueva sección 3.
La portada identifica el segundo informe, con fecha 2 de noviembre de 2026.
Los archivos de la primera entrega se conservan como versión independiente.

## Diseño fijado

El protocolo especifica dos bloques de tres métodos, con 3.030 y 6.060
evaluaciones respectivamente, doce instancias, treinta repeticiones y
semillas 80–109. El efecto mínimo relevante es 1% del objetivo ponderado.

La comparación secundaria por tiempo fija 10 segundos para cada configuración
completa del bloque B, con cuotas nominales 5+5 para las carteras y un plazo
global común. Sus reglas de parada y análisis están separadas de la campaña
por evaluaciones.

El análisis global toma las instancias como bloques, con Holm para cuatro
contrastes prefijados. Se incluyen intervalos, medidas de efecto,
tratamiento de empates, un análisis contextual Friedman por permutaciones
y reglas explícitas de integridad y fallos. Se registrará el entorno y
se comprobarán los calendarios finales.

**Estado:** diseño especificado; campañas pendientes de ejecución.
El informe no presenta resultados experimentales. La implementación del
criterio temporal y del análisis especificado debe verificarse antes de ejecutar
su campaña.

## Compilación

Desde este directorio, en una distribución con LaTeX y Biber:

~~~bash
latexmk -pdf -interaction=nonstopmode -halt-on-error \
  -jobname=Entrega_2_Tabu_DMAB main.tex
~~~

La carpeta es un proyecto LaTeX autónomo con main.tex, estilo institucional,
portada, imagen, sección incluida y bibliografía. El estilo y la imagen
son copias sin alteración de la plantilla institucional.

## Comprobación de alcance

La revisión debe comprobar:

- Sección experimental entre 1 y 3 páginas.
- Correspondencia con el protocolo versionado y el inventario.
- Objetivo, arquitectura, restricciones y parámetros consistentes.
- Variables de la ecuación nueva explicadas inmediatamente debajo.
- Texto de resumen, introducción y conclusión idéntico al de la primera entrega.
- Ausencia de resultados preliminares y de afirmaciones de superioridad demostrada.
- Tablas, citas, bibliografía y folios legibles.
