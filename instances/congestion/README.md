# Catálogo de congestión (`congestion-v1`)

Estas 48 instancias son **sintéticas**. No contienen datos de pacientes ni
representan un hospital real. Tienen 15, 20, 25 y 30 cirugías, con doce
instancias por tamaño.

## Generación

`experiments/generate_congestion.py` crea cada instancia en tres pasos:

1. Remuestrea con reemplazo pacientes de una instancia estándar del mismo tamaño.
2. Multiplica cada tiempo por ruido lognormal de `sigma=0,10` y redondea a 0,5 min.
3. Aplica los factores de congestión y redibuja la elegibilidad de personal.

La semilla de cada instancia es `800000 + 100 × tamaño + índice`. Se registra en el
YAML y en `experiments/results/entrega2_catalogo_congestion/manifest.json`. El
manifiesto guarda además el SHA-256 de cada archivo. Ningún sorteo fue rechazado.

## Factores

| Factor | Valor | Efecto |
|---|---:|---|
| `rho_S` | 0,40 | Reduce el número de cirujanos al 40 % de la instancia base. |
| `rho_R` | 1,00 | Mantiene el número de salas. |
| `rho_W` | 1,00 | Mantiene la escala de `max_wait`. |

La calibración eligió estos valores con la regla pre-registrada, sobre instancias
de desarrollo que no integran este catálogo. Reducir salas o ajustar `max_wait`
no bastó: ver `experiments/results/entrega2_calibracion_congestion_85_89/`.

`setup` y `transition` de cirugía siguen en cero. Un valor positivo crearía una
espera constante, que no mediría congestión.

## Comprobaciones

- Las 48 instancias pasan `load_instance` y `load_catalog`.
- FIFO, SPT y LPT encuentran solución factible en todas.
- Todos los tiempos son múltiplos de 0,5 min.

## Alcance

Las instancias son nuevas para la búsqueda, pero comparten el perfil de duraciones
del catálogo estándar. No constituyen un dominio independiente.

```bash
python -m experiments.generate_congestion --rho-rooms 1.0 --rho-surgeons 0.4 \
  --rho-wait 1.0 --per-size 12
```

El comando se niega a reemplazar un catálogo ya existente.
