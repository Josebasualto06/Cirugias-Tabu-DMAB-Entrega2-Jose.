# Medición de rendimiento: Mac y Colab

Se midieron dos bloques completos de 120 corridas, uno por entorno.
Cada bloque usa las doce instancias, las semillas 2100-2104 y ambos métodos
con 6.060 evaluaciones. No forma parte de las semillas 80-109 de la
campaña experimental del informe.

- [Comparación, figura y estimación de la campaña completa](comparison_20261101/README.md).
- [Mac: resumen](local_20261101_complete/summary.json) y [registros](local_20261101_complete/runs.csv).
- [Colab: resumen](colab_20261101_complete/summary.json) y [registros](colab_20261101_complete/runs.csv).
- [Notebook ejecutado y reproducción](../../experiments/colab/README.md).

El primer intento local, en la carpeta local_20261101, se interrumpió
tras 73 corridas al reiniciar la aplicación. Su manifiesto declara la
interrupción y exclusión de la comparación. Se conserva sin mezclar sus
tiempos con los del bloque completo posterior.

Se comprobaron hashes del motor y datos, versiones de NumPy/PyYAML,
configuraciones y cobertura. Las 120 parejas coinciden exactamente en
objetivo inicial/final, makespan y esperas. Los archivos de soluciones
finales también son idénticos.

Para repetir el análisis:

    python -m experiments.compare_hardware_smoke \
      --local outputs/hardware_smoke/local_20261101_complete \
      --colab outputs/hardware_smoke/colab_20261101_complete \
      --output outputs/hardware_smoke/nueva_comparacion

Las proyecciones corresponden a las doce instancias actuales: seis veces
el smoke para las 720 corridas principales, más 720 × 10 segundos nominales
para la campaña temporal. No incluyen instalación, análisis, almacenamiento
ni sobrepasos y validación adicional de la fase temporal. No se extrapolan
a 50, 100 o 150 cirugías.
