# Registro de desviaciones del protocolo de la Entrega 3

El protocolo congelado es `docs/protocolo-entrega3.md`, commit `05ca74a`. Ese
archivo no se edita. Este registro anota cada cambio, aclaración o incidencia
posterior al congelamiento, en orden cronológico.

## Desviaciones del protocolo

Ninguna. La hipótesis, las semillas, la prueba, el bootstrap, la regla de
decisión y el tamaño se aplicaron como se registraron.

## Incidencias de ejecución

**I1 (2026-11-15). Fallo al imprimir en la consola.** El estudio completó los
960 pares y escribió `runs.csv`, `solutions.jsonl`, `comparisons.csv`,
`descriptive.csv`, `ANALYSIS.md` y el manifiesto con estado `completed`.
Después, la impresión final de `ANALYSIS.md` en la consola de Windows falló,
porque la codificación cp1252 no representa el signo «−». El proceso terminó
con código 1. No se perdió ningún dato y no se re-ejecutó ninguna corrida. El
script no se modificó, para conservar los hashes del manifiesto. Para
ejecutarlo sin ese error se usa `python -X utf8 -m experiments.confirm_ucb1`.

## Notas posteriores a la ejecución

Ninguna cambia hipótesis, semillas, prueba ni regla de decisión.

**N1 (2026-11-15). Comprobación previa del script.** Antes de usar semillas
nuevas, se comprobó que `evaluate_pair` reproducía dos pares archivados de la
Entrega 2: `HOSP-CONG-15-01` con la semilla 91 y `HOSP-CONG-30-07` con la
semilla 104. Los objetivos coincidieron con `entrega2_congestion_90_109`. Esa
comprobación no guardó resultados ni usó las semillas 120–139.

**N2 (2026-11-15). Ejecución.** El estudio corrió con 12 procesos entre las
22:59 y las 23:14, en una sola sesión y antes de la fecha de corte. El
manifiesto registra el commit `dc9dbdf`.

**N3 (2026-11-16). Resultado y auditoría.** La diferencia `UCB1 − uniforme` fue
−2,749, con IC 95 % [−4,069; −1,453] y `p` de Wilcoxon menor que 0,001. Cumple
las tres condiciones, así que H1c queda respaldada. El verificador recalculó
1.920 calendarios finales y repitió la decisión; todo coincidió.

**N4 (2026-11-16). Variabilidad.** La DE de las medias por instancia fue 3,551,
frente a 3,508 en la planificación. La potencia de planificación no cambia de
forma apreciable.

## Efecto en la interpretación

El resultado confirma el contraste exploratorio de las semillas 90–109 en este
catálogo. No mide generalización a otros hospitales ni evalúa una cartera con
UCB1. Tampoco compara UCB1 con Tabu prolongado o con dos Tabu independientes.

## Notas de la revisión final del informe

**N5 (2026-11-22). Re-ejecución de auditoría.** `experiments/scripts/reejecutar_corridas.py`
repitió las corridas archivadas de 3.030 evaluaciones de las semillas 90–109 y 120–139, para
registrar propuestas decodificadas, movimientos y convergencia. No usó semillas, métodos ni
parámetros nuevos, y solo guarda resultados si cada corrida reproduce su valor archivado.
Sus medidas, en `experiments/results/entrega3_revision_reejecucion/`, son descriptivas.

**N6 (2026-11-22). Descriptivos y alcance.** `experiments/scripts/descriptivos_revision.py`
calculó, después de ver los resultados, el efecto de E1 por tamaño, su dispersión y su costo.
También reúne los estudios previos del catálogo estándar, con cualquier signo. No prueban
hipótesis ni cambian H1c. Acotan su lectura: E1 no muestra ventaja con 15 cirugías, no separa
aprender de sesgar movimientos y no se extiende al catálogo estándar.

**N7 (2026-11-22). Trazabilidad de los manifiestos de la revisión.** El `git_head` de la
re-ejecución, `0a50ce0`, es un commit local que no se publicó: solo agregaba una guía interna
sobre `ef60021`, sin cambios de código ni de datos. Para reproducirla sirve `ef60021` más el
script, cuyo hash está en el manifiesto. Además, los hashes de los CSV de origen se tomaron
de la copia de trabajo de Windows. En los CSV que allí usan CRLF, hay que convertir LF a CRLF
antes de comparar el hash con un clon.
