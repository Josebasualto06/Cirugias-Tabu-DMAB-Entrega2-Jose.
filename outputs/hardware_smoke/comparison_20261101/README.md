# Comparación de tiempos: Mac local y Colab CPU

Prueba completada: doce instancias, cinco semillas (2100-2104), dos métodos
y 6.060 evaluaciones por corrida. Son 120 corridas y 727.200 evaluaciones
en cada entorno. Las dos búsquedas se ejecutaron secuencialmente.

**Contexto de Colab:** CPU estándar en cuenta Pro, según registro de la ejecución.
Esta observación no mide el efecto de pagar Pro ni garantiza el rendimiento
de otra sesión gratuita o de pago.

| Entorno | Búsquedas observadas | Bucle, incluida escritura | Preparación + calentamiento + bucle |
|---|---:|---:|---:|
| Mac local | 364.01 s (6.07 min) | 364.02 s (6.07 min) | 364.36 s (6.07 min) |
| Colab CPU | 1499.66 s (24.99 min) | 1499.68 s (24.99 min) | 1501.00 s (25.02 min) |

El cociente Colab/local del tiempo total de búsqueda fue **4.120**.
Un cociente mayor que uno indica que Colab tardó más en esta prueba.
Las duraciones de búsqueda incluyen inicialización, búsqueda y validación
estricta final; excluyen instalación, importación, carga de datos y calentamiento.

## Reproducibilidad y entorno

Coincidieron **120 de 120** parejas
en objetivo inicial/final, makespan y esperas con tolerancia absoluta 1e-9.
Se verificaron cobertura, claves únicas, 6.060 evaluaciones factibles por corrida,
configuración, semillas, versiones de NumPy/PyYAML y hashes del código y datos.
La validación estricta corresponde al motor en cada corrida; este análisis
no volvió a reconstruir todos los calendarios.

| Entorno | Procesador | CPU lógicas | RAM declarada (GiB) | Python |
|---|---|---:|---:|---|
| Mac local | Apple M5 | 10 | 24.00 | 3.12.14 |
| Colab CPU | Intel(R) Xeon(R) CPU @ 2.20GHz | 2 | 12.67 | 3.13.18 |

Diferencias de versiones registradas:
- matplotlib: local 3.11.2; Colab 3.10.0.
- python: local 3.12.14; Colab 3.13.18.
- scipy: local 1.18.1; Colab 1.16.3.

Se comparan entornos completos, con una sesión por entorno. Las diferencias
de hardware, Python, virtualización y carga no permiten atribuir todo el
cociente observado a un solo factor.

## Estimación de la campaña completa

**Estas cifras son estimaciones, no ejecuciones de la campaña de 720 corridas.**
La principal escala el tiempo observado por seis. La secundaria añade su
cuota nominal de 720 × 10 segundos, sin haber ejecutado aquí el runner temporal.

| Entorno | Principal: 720 corridas | Principal + secundaria nominal |
|---|---:|---:|
| Mac local | 2184.07 s (36.40 min) | 9384.07 s (156.40 min) |
| Colab CPU | 8997.96 s (149.97 min) | 16197.96 s (269.97 min) |

El escalamiento supone una mezcla de instancias y rendimiento similares.
No incluye instalación, análisis, almacenamiento ni sobrepasos y validación
adicional de la fase temporal.

## Evidencia

- [Resultados emparejados](comparison.csv).
- [Resumen por método y tamaño](timing_summary.csv).
- [Cálculos, comprobaciones y fuentes](comparison.json).
- [Figura de tiempos](tiempos_smoke.png).
- [Mac local: manifest.json](../local_20261101_complete/manifest.json).
- [Mac local: summary.json](../local_20261101_complete/summary.json).
- [Mac local: runs.csv](../local_20261101_complete/runs.csv).
- [Colab CPU: manifest.json](../colab_20261101_complete/manifest.json).
- [Colab CPU: summary.json](../colab_20261101_complete/summary.json).
- [Colab CPU: runs.csv](../colab_20261101_complete/runs.csv).
