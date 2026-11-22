# Guion de la defensa final

Duración objetivo: 13:55, con margen de 1:05 sobre el máximo de 15 minutos.
Los tiempos incluyen señalar cada figura y tabla. El texto leído sin pausas dura
menos, así que hay que cronometrar un ensayo. El reparto de presentadores es una
propuesta: la pauta no exige que presente todo el grupo. Las ocho diapositivas
del apéndice no se presentan; sirven para responder preguntas.

Convención que hay que repetir al mostrar resultados: la diferencia es alternativa
menos referencia, así que un valor negativo favorece a la alternativa.

## Diapositivas

### 1. Portada
**Tiempo:** 0:15 · **Presenta:** [José]

Somos José Basualto, Cristopher Dauros y Carlos Ruz. Presentamos el informe final de
nuestro proyecto sobre programación de cirugías electivas, con sus resultados y
conclusiones.

### 2. Mientras un paciente espera, su sala y su anestesista quedan bloqueados
**Tiempo:** 0:45 · **Presenta:** [José]

Una cirugía electiva tiene dos etapas: anestesia y cirugía. Si la anestesia termina y la
cirugía aún no puede empezar, el paciente espera. Mientras tanto retiene su primera sala
y su anestesista, y ese bloqueo retrasa a los pacientes siguientes.

### 3. El calendario debe terminar antes sin exceder la espera máxima
**Tiempo:** 0:45 · **Presenta:** [José]

Decidimos el orden de los pacientes y sus salas; un planificador asigna al personal e inicia
cada etapa lo antes posible. La espera nunca puede superar el máximo permitido. Minimizamos `f`, que combina el fin de
la jornada, la espera total y la peor espera.

### 4. Faltaba separar el aporte de D-MAB en Tabu con espera estricta
**Tiempo:** 0:50 · **Presenta:** [José]

La literatura ya usa aprendizaje para elegir operadores, pero en otras arquitecturas. En los
trabajos que revisamos no encontramos una evaluación que separe ese aporte del cómputo y de
repetir la búsqueda, en un Tabu con espera estricta y reparación. Por eso preguntamos en qué
condiciones D-MAB mejora a Tabu frente a elegir los mismos movimientos de forma uniforme.

### 5. Una cartera fija corre dos caminos y conserva el mejor calendario
**Tiempo:** 0:50 · **Presenta:** [José]

Nuestra propuesta es una cartera fija. Corre un Tabu uniforme y un Tabu con D-MAB, cada
uno con 3.030 evaluaciones, y conserva el mejor calendario factible. El aprendizaje actúa
solo en la fase de evolución: elige el movimiento de cada vecino.

### 6. D-MAB aprende en línea qué movimiento proponer a Tabu
**Tiempo:** 0:55 · **Presenta:** [José]

Cada movimiento es un brazo. UCB1 combina la recompensa media con un término de
exploración. D-MAB agrega un detector, Page–Hinkley, que reinicia las estadísticas cuando
la recompensa cae. Sin ese detector queda UCB1, que usamos como ablación.

### 7. Cuatro comparaciones separan selección, cómputo y repetición de la búsqueda
**Tiempo:** 1:05 · **Presenta:** [Cristopher]

Cada comparación pone a prueba una explicación alternativa. C1 mide la política de selección,
aunque no prueba que aprender sea la causa: una mezcla fija podría lograr lo mismo. C2 controla
el cómputo, C3 la repetición de la búsqueda y C4 el reinicio. Analizamos medias por instancia,
porque las semillas de una instancia comparten datos. La hipótesis primaria, C1, solo queda
respaldada si cumple tres condiciones fijadas antes de ejecutar.

### 8. El catálogo de congestión tensiona la espera que el original no tensionaba
**Tiempo:** 0:55 · **Presenta:** [Cristopher]

En el catálogo original solo 16 de 240 soluciones tenían espera, así que no podíamos
evaluar el bloqueo. Reducir salas o la espera máxima no bastó. Reducir cirujanos sí:
generamos 48 instancias nuevas, y en ellas 51,8 % de las soluciones terminó con espera.

### 9. Dos protocolos fijaron semillas, tamaño y regla antes de ejecutar
**Tiempo:** 0:55 · **Presenta:** [Cristopher]

Cada estudio usó un rango propio de semillas, y registramos hipótesis, pruebas y regla
antes de correr. El tamaño quedó fijo en 960 pares. La potencia simulada era 0,87, pero
la variabilidad real casi duplicó la supuesta y la potencia aproximada bajó a 0,32. Por
eso, un resultado no significativo no prueba equivalencia.

### 10. La hipótesis primaria no queda respaldada: el intervalo de C1 incluye el cero
**Tiempo:** 1:25 · **Presenta:** [Carlos]

Este gráfico resume el estudio. Cada fila es una diferencia con su intervalo de 95 %; a
la izquierda del cero gana la alternativa. El escenario fue válido: 960 pares sin fallos
y 5.760 calendarios auditados. En C1, D-MAB frente a Tabu uniforme, la media es −0,793 y
el p de Holm es 0,041. Sin embargo, el intervalo cruza el cero. La regla exigía tres
condiciones y C1 cumple dos. Por eso decimos no concluyente: no afirmamos que D-MAB
mejore, ni que sea equivalente. Un reanálisis exploratorio con las 12 bases como unidad
tampoco la respalda.

### 11. La ganancia de la cartera es compatible con repetir la búsqueda
**Tiempo:** 1:05 · **Presenta:** [Carlos]

La cartera sí superó al Tabu prolongado con el mismo presupuesto: es C2. Pero esa ventaja
pierde significación si analizamos por instancia base, y solo aparece con 25 y 30 cirugías; con
15 y 20 es peor en media. En cambio, frente a dos Tabu independientes
el intervalo incluye el cero: es C3. Además, en 56,9 % de las corridas el Tabu prolongado no
mejoró después de la evaluación 3.030. Por tanto, la ganancia es compatible con repetir la
búsqueda, y no la atribuimos al aprendizaje.

### 12. El reinicio Page–Hinkley no ayudó bajo congestión
**Tiempo:** 1:05 · **Presenta:** [Carlos]

La ablación C4 muestra que D-MAB terminó peor que UCB1 sin reinicio, aunque con 15 cirugías
fue mejor en media, y por base la diferencia no es significativa. D-MAB reinició sus estadísticas
una mediana de 24 veces por corrida. Un diagnóstico exploratorio apunta a falsas alarmas. La
recompensa media baja al comienzo, donde reinicia algo más, y luego se estabiliza. Pero 59,3 %
de los reinicios ocurre después del primer tercio. Y si simulamos recompensas que no cambian, el detector reinicia
25 veces igual: basta el ruido. Además, el brazo líder dispara 96,8 % de los reinicios, así que
el bandido borra lo que había aprendido.

### 13. Una confirmación prerregistrada respaldó a UCB1 frente a Tabu uniforme
**Tiempo:** 1:05 · **Presenta:** [Carlos]

En el estudio anterior, UCB1 frente a Tabu uniforme era solo un contraste exploratorio.
Para afirmarlo registramos un segundo protocolo, con una sola comparación y semillas
nuevas, antes de ejecutar. El resultado fue −2,749, con un intervalo completo bajo cero,
y cumple las tres condiciones, también al reanalizar por base. Es un efecto pequeño, 0,92 % del objetivo, y depende del
tamaño: con 15 cirugías no hay ventaja. Además, usa las mismas instancias, así que no
generaliza a otros hospitales.

### 14. Ayuda UCB1 bajo congestión, con costo y sin probar aprendizaje
**Tiempo:** 1:00 · **Presenta:** [José]

¿Cómo se explica? DaCosta y sus coautores ya vieron que, con recompensas binarias, el bandido
sin reinicio ganaba. La reparación no basta como explicación: afectó a 44,0 % de los candidatos
de D-MAB, pero también a los otros métodos. Y UCB1 no prueba que aprender sea la causa: prefirió
el cambio de sala de anestesia, y una mezcla fija podría igualarlo. Además, UCB1 tardó 10,2 % más
y varió más entre semillas. La conclusión vale solo con inicios lo antes posible. En el catálogo estándar,
los signos cambian entre estudios, aunque allí la cartera supera a las reglas simples.

### 15. D-MAB completo no mejora de forma concluyente; aporta UCB1 sin reinicio
**Tiempo:** 1:00 · **Presenta:** [José]

Respondemos la pregunta así: no identificamos una condición en que D-MAB completo mejore
de forma concluyente a Tabu uniforme. Bajo congestión y con inicios lo antes posible, sí aporta
UCB1 sin reinicio,
y es el único resultado que resiste el reanálisis por instancia base.
Nuestro aporte es metodológico: controles a igual presupuesto y dos protocolos registrados
antes de ejecutar. Queda separar aprendizaje de sesgo con una mezcla fija, recalibrar el
detector y evaluar una cartera con UCB1 en instancias reservadas y a igual tiempo. Gracias.

## Preguntas probables

Cada respuesta usa cifras archivadas. C1–C4 son del estudio con semillas 90–109; E1 es la
confirmación con semillas 120–139. No se mezclan en una misma tabla.

**¿Entonces el ML no sirve?**
No es lo que mostramos. D-MAB completo quedó no concluyente frente a Tabu uniforme. En
cambio, UCB1 sin reinicio sí lo superó en una confirmación prerregistrada: −2,749, con
intervalo [−4,069; −1,453]. Bajo congestión, quitar el reinicio ayudó en media, aunque esa
ventaja sobre D-MAB es frágil al analizar por base. No probamos que
la ventaja de UCB1 venga de aprender y no de favorecer un operador.

**¿Por qué C1 no cuenta si p < 0,05?**
La regla se fijó antes de ejecutar y exigía tres condiciones: p de Holm bajo 0,05,
intervalo completo bajo cero y media de a lo sumo −0,25. C1 cumple dos. Su intervalo es
[−1,850; +0,279] e incluye el cero.

**¿Por qué no agregaron más corridas?**
El protocolo prohíbe ampliar la muestra después de ver los resultados, porque eso infla
el error tipo I. Por eso no tocamos las semillas 90–109. Para la pregunta nueva
registramos otro protocolo, con semillas 120–139.

**¿UCB1 es su nueva propuesta?**
Es la política que la evidencia favorece bajo congestión, no una propuesta completa. Confirmamos
que supera a Tabu uniforme con 3.030 evaluaciones. Falta evaluar una cartera con UCB1 y
compararla con dos Tabu independientes.

**¿Por qué la cartera, si dos Tabu rinde parecido?**
La elegimos en la primera entrega por simplicidad y porque conserva una referencia. Los
datos muestran que supera a prolongar un Tabu, con una ventaja frágil por base, y no la
distinguimos de dos Tabu. Por
eso decimos que su ganancia es compatible con repetir la búsqueda.

**¿Por qué comparar por evaluaciones y no por tiempo?**
El tiempo de pared varió entre sesiones del mismo equipo, y las evaluaciones son
reproducibles. Corrimos un piloto a igual tiempo, pero es solo descriptivo. La
comparación a igual tiempo queda como trabajo futuro.

**¿Sus resultados generalizan a otros hospitales?**
No. Las semillas nuevas sobre el mismo catálogo miden variación de la búsqueda, no
generalización. Además, el catálogo de congestión es sintético y remuestrea el catálogo
estándar.

**¿Qué harían con un semestre más?**
Tres cosas. Primero, comparar UCB1 con una mezcla fija, premiar mejoras del mejor global y
calibrar λ con recompensas que no cambian; en el estándar, λ = 10 ya empeoró, así que hay que
validarlo bajo congestión. Segundo, evaluar la cartera con UCB1 frente a dos Tabu. Tercero,
usar instancias de bases nuevas, de mayor tamaño, y comparar a igual tiempo.

**¿Cómo saben que el reinicio actúa por ruido?**
Es un diagnóstico exploratorio, no una prueba causal. Alimentamos el mismo bandido con recompensas
que no cambian y cinco brazos idénticos: reinició 25 veces en mediana, frente a 24 reales. Sí hay
una caída inicial de la recompensa, y allí reinicia algo más. Pero 59,3 % de los reinicios ocurre
después del primer tercio, con la media ya estable (muestra de las semillas 90–93). No descarta
cambios breves: muestra que el ruido basta para producir tantos reinicios como los observados.

**¿Confirmar UCB1 no es elegir al ganador después de mirar?**
Ese es el riesgo, y por eso usamos semillas nuevas y un protocolo previo. El contraste
exploratorio fue −2,617 y la confirmación dio −2,749. La planificación consideró además
que el efecto real fuera la mitad del observado.

**¿Por qué el umbral mínimo es 0,25?**
Los tiempos son múltiplos de 0,5 minutos, y un paso de espera total mueve `f` en 0,25.
Una diferencia menor no representa un paso en ningún componente del calendario. Es un
umbral de resolución: no lo presentamos como relevancia clínica.

**¿La mejora de D-MAB en C1 no es real, si la media es negativa?**
La media favorece a D-MAB, pero el intervalo va de −1,850 a +0,279. Los datos son
compatibles con un beneficio, con un efecto nulo y con un perjuicio algo mayor que el umbral
de 0,25. Además, la potencia aproximada fue 0,32.

**¿Qué pasó con las 12 instancias oficiales?**
Los signos no son consistentes. Con la configuración anterior (semillas 20–39), UCB1 menos
uniforme dio −0,455; con la vigente (40–59), +1,182. Son descriptivos y ninguno sustenta una
superioridad entre políticas. Por eso la conclusión vale solo para el catálogo de congestión.
Frente a las reglas simples, en cambio, la cartera sí gana. Ambos resultados están en el
apéndice.

**¿Eligieron el catálogo de congestión para que ganara su método?**
No. La celda se eligió por la proporción de soluciones con espera, con una regla previa y con
instancias de desarrollo excluidas. La diferencia entre métodos no participó, y de hecho la
hipótesis primaria no quedó respaldada en ese catálogo.

**¿En qué tamaños funciona?**
En E1, con 15, 20, 25 y 30 cirugías la diferencia fue +0,12; −2,96; −3,91 y −4,25. Con 15 no
hay ventaja. Una causa posible, que no medimos, es que un espacio menor deja menos que aprender.

**¿Cómo saben que UCB1 aprende y no que hay un operador mejor?**
No lo sabemos, y de hecho hay un operador destacado: el cambio de sala de anestesia lideró
los premios en los tres tercios de la búsqueda en 47 de 48 instancias. En E1, UCB1 le dedicó 38,5 % de las
evaluaciones, frente a 19,6 % del uniforme. La ablación que falta es una mezcla fija con esas
mismas frecuencias.

**¿Es justa la comparación si los duplicados no cuentan?**
Es justa en evaluaciones, no del todo en cómputo. UCB1 decodificó 10,1 % más propuestas y
tardó 10,2 % más. En el piloto a igual tiempo, que no incluyó UCB1, D-MAB fue peor en tres de
los cuatro tamaños, con solo cinco semillas por tamaño.

**¿Por qué el p y el intervalo de C1 no coinciden?**
El bootstrap remuestrea semillas dentro de medias que ya contienen ese ruido: su error
estándar es 1,62 veces el de esas medias. Es conservador frente a ese ruido, pero se fijó antes.
Reemplazarlo después de ver el resultado sería elegir el análisis según la conclusión.

**¿Qué tan lejos están del óptimo?**
No lo sabemos, porque no hay cotas para estas instancias. El RPD se mide contra el mejor valor
propio. Proponemos cotas exactas con 15 cirugías como trabajo futuro.

**¿Un efecto de 0,92 % importa en un hospital?**
No lo afirmamos. Los datos son sintéticos y el objetivo es ponderado. Mostramos que el efecto
es reproducible en este catálogo, no que sea clínicamente relevante.

**¿Cómo se puede comprobar que los protocolos son previos?**
Están en los commits a0da669 y 05ca74a, y cada manifiesto guarda el hash del protocolo. Es un
registro en Git, no en una plataforma externa, y lo reconocemos.

**¿Por qué el aprendizaje mejora tan poco?**
Tenemos tres indicios medidos, no una prueba causal. El detector reinicia incluso con puro ruido
y borra lo aprendido. La recompensa está desalineada: solo 8,5 % de las propuestas recompensadas
mejora el mejor global. Y el operador con más premios casi no cambia, así que podría bastar una
preferencia fija. Además, la búsqueda se estanca, y elegir mejor el movimiento no asegura salir
de ahí.

**¿Su planificador es el del repositorio del profesor?**
No es idéntico. Seguimos la formulación de clase: las etapas pueden usar salas distintas y la
primera queda retenida hasta que la cirugía pueda comenzar. El simulador estricto del repositorio
la retiene hasta el final de la cirugía; su evaluador antiguo, no. Reimplementamos la regla
estricta, sin ejecutar ese simulador: con ella, 83,4 % de nuestros calendarios finales sería
infactible, así que los valores no son comparables. No evaluamos si las conclusiones se mantienen
al buscar con esa regla, y lo declaramos en las amenazas.

**¿Las 48 instancias son independientes?**
No. Derivan de las 12 oficiales, cuatro de cada una. Por eso repetimos el análisis, de forma
exploratoria, con la base como unidad. C1 sigue sin cumplir: su p de Holm baja a 0,010, pero el
intervalo incluye el cero. C2 y C4 pierden significación, ambas con p de Holm 0,192. E1 se
mantiene. Con 12 unidades hay menos potencia, así que eso no prueba ausencia de efecto. A futuro
hacen falta bases independientes o modelar esa agrupación en el protocolo.

**¿Reanalizar después de ver los resultados no es elegir a conveniencia?**
Lo sería si reemplazara la decisión registrada o mostráramos solo lo favorable. Cambiamos una
sola cosa, la unidad, y lo informamos completo y como exploratorio: debilita dos de nuestros
resultados y no respalda H1. Reconocemos que se decidió después de ver los datos, y está anotado
en los registros de desviaciones.

**¿Por qué Tabu termina más tarde que FIFO?**
Porque no minimizamos solo el makespan. Las reglas terminan antes, pero su espera total es más
de diez veces la de Tabu, y el objetivo del curso penaliza la espera total y la máxima. Esa
espera depende de iniciar la anestesia lo antes posible.

**¿Superan a FIFO, SPT y LPT?**
En las 12 oficiales, sí: con las semillas 60–79 la cartera superó a la mejor de las tres en las 12,
con 5,89 % menos del objetivo. En makespan, y también con la penalización de clase por
desequilibrio, ganó en 10. Dos Tabu logran 5,90 %, así que no lo atribuimos al aprendizaje. Es
exploratorio y usa nuestro planificador, no el simulador docente.

**¿Por qué no retrasan la anestesia para que nadie espere?**
Porque seguimos al simulador: el algoritmo entrega secuencia y salas, y los inicios se calculan
lo antes posible. El modelo matemático de clase sí trata el inicio como variable. Lo revisamos de
forma exploratoria: al retrasarla, la espera queda en cero y la mejor regla supera la media de cada
método en las 48 instancias de congestión. La ventaja de UCB1 baja a 1,656 en E1 y a 0,093 en las
semillas 90–109. No repetimos la búsqueda, así que nuestras conclusiones valen solo con la regla
actual. Qué regla corresponde es una pregunta para el profesor.

**¿Cuál es el tamaño de efecto?**
Usamos r = Z/√n de Wilcoxon, con 48 instancias; negativo favorece a la alternativa. En C1 fue
−0,33; en C2, −0,43; en C3, −0,28; en C4, +0,46; y en E1, −0,64. Es exploratorio: un r moderado
en C1 no cambia que su intervalo incluya el cero.
