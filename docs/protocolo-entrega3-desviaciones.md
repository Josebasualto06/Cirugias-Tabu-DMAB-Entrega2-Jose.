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

**N8 (2026-11-22). Diagnóstico exploratorio del reinicio.**
`experiments/scripts/diagnostico_revision.py` repitió con observadores las corridas archivadas
de Tabu uniforme y D-MAB de las semillas 90–109, sin discrepancias, y alimentó el bandido con
recompensas estacionarias. Ese banco no programa cirugías ni usa semillas de búsqueda. Con cinco
brazos idénticos dio una mediana de 25 reinicios, frente a 24 observados.
`experiments/scripts/diagnostico_recompensa.py` repitió además una muestra, las semillas 90–93.
Allí la recompensa media baja al comienzo y luego se estabiliza. D-MAB reinicia más al comienzo
(40,7 % de los reinicios en el primer tercio), pero 59,3 % ocurre después, con la media estable.
El informe publicado en `3eb2bc0` proponía, como explicación
plausible, que el detector confundía el agotamiento de la búsqueda con un cambio. Era incompleta:
existe una caída inicial, pero la mayoría de los reinicios ocurre después y el ruido basta para
producir tantos como los observados. Es descriptivo: no prueba hipótesis ni cambia C1–C4 o E1.

**N9 (2026-11-22). Regla de salas.** El planificador libera la sala de anestesia al comenzar la
cirugía si las salas difieren, como dice la formulación de clase. El simulador estricto del
repositorio docente (`ecd30e3`, función `schedule_instance_solution` de `simulation/scheduler.py`)
la retiene hasta el final de la cirugía. Su evaluador antiguo, `_fitness_for_context`, no la
retiene hasta el final, aunque difiere en otros aspectos. Esa diferencia no se había declarado.
La regla estricta se reimplementó a partir de la lectura de ese código; el simulador docente no se
ejecutó. Con esa regla, 83,4 % de los calendarios finales archivados sería infactible. No se
evaluó si las conclusiones se mantienen al buscar con esa regla.

**N10 (2026-11-22). Reanálisis exploratorio por instancia base.** El protocolo fija la instancia
como unidad. Después de ver los resultados se repitió E1 con las 12 bases como unidad, sin
cambiar la prueba, el bootstrap ni la regla, junto con C1–C4 (nota N7 de la Entrega 2). Según
`experiments/results/entrega3_sensibilidad_bases/`, E1 sigue cumpliendo la regla: IC
[−4,335; −1,191] y p = 0,005. No es una confirmación adicional, no mide generalización y no
cambia la decisión registrada.

**N11 (2026-11-22). Cierre del informe.** Según `experiments/results/entrega3_cierre/`,
calculado después de ver los resultados y sin búsquedas nuevas, E1 tiene r = −0,64. Con la
anestesia retrasada (nota N9 de la Entrega 2), su diferencia pasa de −2,749 a −1,656: H1c sigue
respaldada según su protocolo, pero solo con inicios lo antes posible. La misma salida compara,
de forma exploratoria, la cartera archivada de las semillas 60–79 con FIFO, SPT y LPT en las 12
instancias oficiales: gana en las 12, con 5,89 % menos del objetivo, y en 10 al sumar la
penalización de clase por desequilibrio. Dos Tabu logran 5,90 %, así que no se atribuye al
aprendizaje. No se usó el simulador docente ni su regla de salas.
