# Guion de la defensa final

Duración objetivo: 13:55, con margen de 1:05 sobre el máximo de 15 minutos.
Los tiempos incluyen señalar cada figura y tabla. El texto leído sin pausas dura
menos, así que hay que cronometrar un ensayo. El reparto de presentadores es una
propuesta: la pauta no exige que presente todo el grupo. Las cinco diapositivas
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

Decidimos el orden de los pacientes y sus salas; un planificador asigna al personal. La
espera nunca puede superar el máximo permitido. Minimizamos `f`, que combina el fin de
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

### 7. Cuatro comparaciones separan aprendizaje, cómputo y repetición de la búsqueda
**Tiempo:** 1:05 · **Presenta:** [Cristopher]

Cada comparación descarta una explicación alternativa. C1 aísla el aprendizaje, C2 el
cómputo, C3 la repetición de la búsqueda y C4 el reinicio. Analizamos medias por
instancia, porque las semillas de una instancia comparten datos. La hipótesis primaria,
C1, solo queda respaldada si cumple tres condiciones fijadas antes de ejecutar.

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
mejore, ni que sea equivalente.

### 11. La ganancia de la cartera es compatible con repetir la búsqueda
**Tiempo:** 1:05 · **Presenta:** [Carlos]

La cartera sí superó al Tabu prolongado con el mismo presupuesto: es C2. Esa ventaja aparece
con 25 y 30 cirugías; con 15 y 20 es peor en media. En cambio, frente a dos Tabu independientes
el intervalo incluye el cero: es C3. Además, en 56,9 % de las corridas el Tabu prolongado no
mejoró después de la evaluación 3.030. Por tanto, la ganancia es compatible con repetir la
búsqueda, y no la atribuimos al aprendizaje.

### 12. El reinicio Page–Hinkley no ayudó bajo congestión
**Tiempo:** 1:05 · **Presenta:** [Carlos]

La ablación C4 muestra que D-MAB terminó peor que UCB1 sin reinicio, aunque con 15 cirugías
fue mejor en media. D-MAB reinició sus estadísticas una mediana de 24 veces por corrida.
Nuestra hipótesis es que el detector confunde el estancamiento normal con un cambio entre
operadores: las mejoras escasean, la recompensa cae y el reinicio borra lo aprendido. No
medimos ese mecanismo, así que lo presentamos como hipótesis.

### 13. Una confirmación prerregistrada respaldó a UCB1 frente a Tabu uniforme
**Tiempo:** 1:05 · **Presenta:** [Carlos]

En el estudio anterior, UCB1 frente a Tabu uniforme era solo un contraste exploratorio.
Para afirmarlo registramos un segundo protocolo, con una sola comparación y semillas
nuevas, antes de ejecutar. El resultado fue −2,749, con un intervalo completo bajo cero,
y cumple las tres condiciones. Es un efecto pequeño, 0,92 % del objetivo, y depende del
tamaño: con 15 cirugías no hay ventaja. Además, usa las mismas instancias, así que no
generaliza a otros hospitales.

### 14. Ayuda UCB1 bajo congestión, con costo y sin probar aprendizaje
**Tiempo:** 1:00 · **Presenta:** [José]

¿Cómo se explica? DaCosta y sus coautores ya vieron que, con recompensas binarias, el bandido
sin reinicio ganaba. La reparación no basta como explicación: afectó a 44,0 % de los candidatos
de D-MAB, pero también a los otros métodos. Y UCB1 no prueba que aprender sea la causa: prefirió
el cambio de sala de anestesia, y una mezcla fija podría igualarlo. Además, UCB1 tardó 10,2 % más
y varió más entre semillas. En el catálogo estándar, los signos cambian entre estudios.

### 15. D-MAB completo no mejora de forma concluyente; aporta UCB1 sin reinicio
**Tiempo:** 1:00 · **Presenta:** [José]

Respondemos la pregunta así: no identificamos una condición en que D-MAB completo mejore
de forma concluyente a Tabu uniforme. En el catálogo de congestión sí aporta UCB1 sin reinicio.
Nuestro aporte es metodológico: controles a igual presupuesto y dos protocolos registrados
antes de ejecutar. Queda separar aprendizaje de sesgo con una mezcla fija, recalibrar el
detector y evaluar una cartera con UCB1 en instancias reservadas y a igual tiempo. Gracias.

## Preguntas probables

Cada respuesta usa cifras archivadas. C1–C4 son del estudio con semillas 90–109; E1 es la
confirmación con semillas 120–139. No se mezclan en una misma tabla.

**¿Entonces el ML no sirve?**
No es lo que mostramos. D-MAB completo quedó no concluyente frente a Tabu uniforme. En
cambio, UCB1 sin reinicio sí lo superó en una confirmación prerregistrada: −2,749, con
intervalo [−4,069; −1,453]. Lo que no ayudó fue el reinicio.

**¿Por qué C1 no cuenta si p < 0,05?**
La regla se fijó antes de ejecutar y exigía tres condiciones: p de Holm bajo 0,05,
intervalo completo bajo cero y media de a lo sumo −0,25. C1 cumple dos. Su intervalo es
[−1,850; +0,279] e incluye el cero.

**¿Por qué no agregaron más corridas?**
El protocolo prohíbe ampliar la muestra después de ver los resultados, porque eso infla
el error tipo I. Por eso no tocamos las semillas 90–109. Para la pregunta nueva
registramos otro protocolo, con semillas 120–139.

**¿UCB1 es su nueva propuesta?**
Es el componente que la evidencia respalda, no una propuesta completa. Confirmamos que
supera a Tabu uniforme con 3.030 evaluaciones. Falta evaluar una cartera con UCB1 y
compararla con dos Tabu independientes.

**¿Por qué la cartera, si dos Tabu rinde parecido?**
La elegimos en la primera entrega por simplicidad y porque conserva una referencia. Los
datos muestran que supera a prolongar un Tabu, pero no la distinguimos de dos Tabu. Por
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
Tres cosas. Primero, comparar UCB1 con una mezcla fija y recalibrar λ y δ bajo
congestión; en el estándar, λ = 10 ya empeoró. Segundo, evaluar la cartera con UCB1 frente
a dos Tabu. Tercero, usar instancias reservadas, de mayor
tamaño, y comparar a igual tiempo.

**¿Cómo saben que el reinicio actúa por ruido?**
No lo sabemos: es una hipótesis. Tenemos dos datos descriptivos: 24 reinicios por
corrida en mediana y 3,9 % de recompensas positivas en el diagnóstico del catálogo
estándar. Probarlo exige variar el umbral λ.

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
superioridad. Por eso la conclusión vale solo para el catálogo de congestión. Está en el apéndice.

**¿Eligieron el catálogo de congestión para que ganara su método?**
No. La celda se eligió por la proporción de soluciones con espera, con una regla previa y con
instancias de desarrollo excluidas. La diferencia entre métodos no participó, y de hecho la
hipótesis primaria no quedó respaldada en ese catálogo.

**¿En qué tamaños funciona?**
En E1, con 15, 20, 25 y 30 cirugías la diferencia fue +0,12; −2,96; −3,91 y −4,25. Con 15 no
hay ventaja. Una causa posible, que no medimos, es que un espacio menor deja menos que aprender.

**¿Cómo saben que UCB1 aprende y no que hay un operador mejor?**
No lo sabemos. UCB1 dedicó cerca del doble de evaluaciones que el uniforme al cambio de sala
de anestesia. La ablación que falta es una mezcla fija con esas mismas frecuencias.

**¿Es justa la comparación si los duplicados no cuentan?**
Es justa en evaluaciones, no del todo en cómputo. UCB1 decodificó 10,1 % más propuestas y
tardó 10,2 % más. En el piloto a igual tiempo, que no incluyó UCB1, D-MAB fue peor en tres de
los cuatro tamaños, con solo cinco semillas por tamaño.

**¿Por qué el p y el intervalo de C1 no coinciden?**
El bootstrap remuestrea semillas dentro de medias que ya contienen ese ruido: su error
estándar es 1,62 veces el de esas medias. Es conservador, pero se fijó antes. Cambiarlo
después de ver el resultado sería elegir el análisis según la conclusión.

**¿Qué tan lejos están del óptimo?**
No lo sabemos, porque no hay cotas para estas instancias. El RPD se mide contra el mejor valor
propio. Proponemos cotas exactas con 15 cirugías como trabajo futuro.

**¿Un efecto de 0,92 % importa en un hospital?**
No lo afirmamos. Los datos son sintéticos y el objetivo es ponderado. Mostramos que el efecto
es reproducible en este catálogo, no que sea clínicamente relevante.

**¿Cómo se puede comprobar que los protocolos son previos?**
Están en los commits a0da669 y 05ca74a, y cada manifiesto guarda el hash del protocolo. Es un
registro en Git, no en una plataforma externa, y lo reconocemos.
