# Prueba de rendimiento en Colab y CPU local

El [notebook ejecutado](Hospitales_Smoke_Local_Colab_ejecutado.ipynb)
conserva tres celdas de código ejecutadas en orden y sus salidas.
La [copia en Colab](https://colab.research.google.com/drive/1xzeAKaxf9y65nf52-4YYx368LiLUQj8J)
corresponde a la sesión de CPU estándar de la prueba.

## Repetir en Colab

1. Abrir una copia del notebook y conectar una CPU estándar, sin GPU.
2. Descargar [oii464-smoke.zip](oii464-smoke.zip) y subirlo al almacenamiento
   de la sesión, en /content/oii464-smoke.zip.
3. Ejecutar las tres celdas en orden: verificar paquete e instalar NumPy 2.3.5
   y PyYAML 6.0.3; ejecutar búsquedas; descargar los registros completos.

El paquete contiene únicamente el motor, las doce instancias sintéticas
y el script de medición. No requiere credenciales del repositorio.
Su SHA-256 es
8b17719663e3a24ae015459e4bdb11057e9f952384556da0212a8a4f069b46ed.
Para repetir dentro de la misma sesión se debe elegir otro directorio
de salida, conservando la ejecución anterior.

## Repetir localmente

Desde la raíz del repositorio y con el paquete instalado:

    python -m experiments.hardware_smoke --label local \
      --output outputs/hardware_smoke/nueva_ejecucion_local

Ambos entornos realizan 120 corridas: doce instancias, cinco semillas
(2100-2104), dos métodos y 6.060 evaluaciones por corrida. El calentamiento
está excluido. Se alterna el orden de los métodos y se usa un solo proceso.

El entorno medido en Colab tenía Python 3.13.18; el local, Python 3.12.14.
Se registran hardware y versiones efectivas, sin atribuir la diferencia
de tiempo a un único componente ni al tipo de suscripción.

La [comparación verificada](../../outputs/hardware_smoke/comparison_20261101/README.md)
incluye datos, figura y proyección del protocolo de 720 corridas.
Esta prueba de rendimiento se mantiene separada de la campaña de calidad.
