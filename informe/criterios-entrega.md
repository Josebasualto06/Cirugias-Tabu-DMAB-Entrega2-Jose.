# Revisión de la Entrega 1

Este archivo ayuda al equipo a revisar el informe; la pauta oficial y el PDF
compilado prevalecen si hubiera alguna diferencia.

| Requisito de la pauta | Ubicación en `main.tex` |
|---|---|
| Resumen de 150–200 palabras y palabras clave | Resumen de 165 palabras y cinco palabras clave, en página propia |
| Motivación, problema, pregunta y objetivo | Introducción |
| Síntesis de 3–6 estudios relacionados | Un párrafo comparativo: cinco estudios de 2024–2026 y fundamento de D-MAB de 2008 |
| Gancho de la arquitectura híbrida | Selección online de movimientos con D-MAB en la evolución de Tabu; cartera fija con respaldo |
| Componentes MH, ML, datos y orquestación offline/online | Subsecciones 2.2–2.5; reparto fijo separado del aprendizaje interno |
| Métricas, baselines, ablación y criterio de parada | Subsecciones 2.1, 2.4 y 2.5; Tabla 1; 6.060 evaluaciones totales |
| Datos sensibles, cómputo y riesgos metodológicos | Subsección 2.5: datos sintéticos, registro previsto del costo y controles de cómputo y reparación |
| Conclusión de 3–5 oraciones, máximo media página | Cinco oraciones en dos párrafos y página propia, con limitaciones y pasos del semestre |
| Extensión máxima de cinco páginas sin referencias | Cinco páginas de contenido; portada institucional y referencias aparte. Siete páginas físicas en total |

El documento carga directamente `pucv_inf_2024.sty`, la portada de
asignatura adaptada y el encabezado gráfico de la plantilla institucional:
papel carta, fuente Times de 12 puntos, márgenes de 2,5 cm, interlineado
sencillo, sangría de 1 cm, separación de 10 puntos entre párrafos y folio
inferior derecho. Las variables se definen inmediatamente debajo de las dos
ecuaciones. El resumen y la conclusión tienen páginas propias; la introducción
comienza en la página posterior al resumen.

Para redactar se consultaron los tres documentos de la clase de metodología
de la investigación (`DII9000_Metodología_de_la_Investigación__clase_1` y
sus complementarios 1 y 2), la pauta `OII464__Entrega_1`, la presentación
`Presentación_Hospitales__Optativo_`, la diapositiva de taxonomía ML → MH
y el repositorio docente
[`Saicooh/OII464_Hospitales`](https://github.com/Saicooh/OII464_Hospitales).
Los PDF de clase no se redistribuyen aquí; las seis publicaciones
citadas sí tienen su referencia y enlace persistente en `referencias.bib`.

El taller menciona cuatro instancias JSON, mientras que la propuesta parte
de doce instancias sintéticas del catálogo oficial, distribuidas en archivos
YAML. Las repeticiones con distintas semillas permitirán estudiar la
variación de la búsqueda sobre un conjunto de datos fijo; se considerarán
además instancias reservadas para examinar la generalización. Esta entrega
presenta el diseño y el plan de evaluación, sin resultados experimentales.
