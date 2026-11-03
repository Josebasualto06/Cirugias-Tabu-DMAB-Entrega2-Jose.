# Validación de la Entrega 1 (archivada)

Resultados de la Entrega 1: semillas 20–39, D-MAB con C = 1 y λ = 0,35,
memoria tabú de soluciones y sin números aleatorios comunes. Se conservan sin
cambios porque el informe de la Entrega 1 los cita.

El código actual reproduce estas corridas con `TabuConfig.entrega1()`:

```bash
python -m experiments.audit_replay --directory experiments/results/validation_20_39 --seed 20
```

`experiments.verify_results` compara hashes de código, por lo que solo pasa
sobre este directorio en el commit de la Entrega 1 (`8ce37bc`). La
validación vigente está en [`../validation_40_59/`](../validation_40_59/).
