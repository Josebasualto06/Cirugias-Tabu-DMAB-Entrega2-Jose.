# Guion de la defensa

Duración objetivo: 8:15, con margen de 1:45 sobre el máximo de 10 minutos.
Los tiempos incluyen señalar cada figura y tabla. El texto leído sin pausas dura cerca
de 4 minutos, así que hay que cronometrar un ensayo. El reparto de presentadores es una
propuesta.

## Diapositivas

### 1. Portada
**Tiempo:** 0:15 · **Presenta:** [José]

Somos José Basualto, Cristopher Dauros y Carlos Ruz. Presentamos la configuración
experimental de nuestro proyecto sobre programación de cirugías electivas.

### 2. Mientras un paciente espera, su sala y su anestesista quedan bloqueados
**Tiempo:** 0:40 · **Presenta:** [José]

Una cirugía electiva tiene dos etapas: anestesia y cirugía. Si la anestesia termina y la
cirugía aún no puede empezar, el paciente espera. Mientras tanto, retiene su primera sala
y su anestesista. Ese bloqueo retrasa a los pacientes siguientes.

### 3. El calendario debe terminar antes sin exceder la espera máxima
**Tiempo:** 0:45 · **Presenta:** [José]

Decidimos el orden de los pacientes y sus salas; un planificador asigna al personal. La
espera nunca puede superar `max_wait`. Minimizamos `f`, que combina fin de jornada, espera
total y peor espera. El término pequeño solo desempata.

### 4. Falta medir si D-MAB aporta a Tabu con espera estricta
**Tiempo:** 0:45 · **Presenta:** [José]

La literatura ya usa aprendizaje para elegir operadores, pero en otras arquitecturas. Nadie
ha medido D-MAB en este Tabu, con dos etapas, espera estricta y reparación. Por eso nuestra
pregunta no es si funciona siempre, sino en qué condiciones mejora.

### 5. Una cartera fija corre dos caminos y conserva el mejor calendario
**Tiempo:** 0:45 · **Presenta:** [José]

Corremos un Tabu uniforme y un Tabu con D-MAB, cada uno con 3.030 evaluaciones. Conservamos
el mejor calendario factible. El aprendizaje actúa solo en la fase de evolución: elige el
movimiento de cada vecino. La cartera no empeora al Tabu de 3.030 de su semilla, pero gasta
el doble.

### 6. D-MAB aprende en línea qué movimiento proponer a Tabu
**Tiempo:** 0:50 · **Presenta:** [Cristopher]

Cada movimiento es un brazo. UCB1 combina la recompensa media con un término de exploración.
La recompensa mide cuánto mejora un candidato frente al estado local previo. Page–Hinkley
detecta caídas y reinicia las estadísticas del bandido, nunca la búsqueda.

### 7. Las etapas usan semillas separadas y el protocolo quedó registrado antes
**Tiempo:** 0:40 · **Presenta:** [Cristopher]

Cada etapa tiene su propio rango de semillas, y calibrar nunca toca la validación.
Registramos hipótesis, pruebas y semillas antes de ejecutar. Aclaramos un límite: semillas
nuevas sobre un mismo catálogo no miden generalización.

### 8. Cuatro comparaciones separan aprendizaje, cómputo y repetición de la búsqueda
**Tiempo:** 0:50 · **Presenta:** [Cristopher]

Cada comparación descarta una explicación alternativa. C1 aísla el aprendizaje, C2 el
cómputo, C3 la repetición y C4 el reinicio. Analizamos medias por instancia, porque las
semillas de una instancia comparten datos. Un valor negativo favorece a la alternativa.

### 9. El catálogo original no ejercía presión sobre la espera
**Tiempo:** 0:55 · **Presenta:** [Cristopher]

Solo 16 de 240 soluciones tenían espera, así que no podíamos evaluar el bloqueo. Probamos 18
combinaciones. Reducir salas o `max_wait` dejó 10 % o menos, como predijimos antes de medir.
Reducir cirujanos sí funcionó. El catálogo final tiene 48 instancias y 51,8 % de soluciones
con espera.

### 10. 240 pares no podían detectar el efecto; la regla previa fijó 960
**Tiempo:** 1:00 · **Presenta:** [Carlos]

Antes de correr, calculamos que detectar 0,65 exigía 922 pares, y teníamos 240. Una regla
pre-registrada fijó 48 instancias por 20 semillas: 960 pares. Sin embargo, la desviación real
casi duplicó la supuesta, y la potencia aproximada quedó en 0,32. No agregamos corridas: el
protocolo lo prohíbe tras ver resultados.

### 11. El diseño fija de antemano cómo atribuir una mejora al aprendizaje
**Tiempo:** 0:50 · **Presenta:** [Carlos]

En resumen, el diseño fija tres cosas antes de ver resultados: dos catálogos, cinco controles
con igual presupuesto y una regla de decisión registrada. En la próxima entrega informaremos
los resultados de C1 a C4. Toda confirmación posterior usará semillas desde la 120 y un
pre-registro nuevo. Gracias.

## Preguntas probables

Esta entrega presenta solo la configuración experimental. Si preguntan por resultados,
las respuestas siguientes usan cifras del estudio 90–109 y su calificativo obligatorio.

**¿Entonces el ML no sirve?**
No podemos afirmarlo. C1 es no concluyente y su potencia es baja, y la falta de significación
no prueba equivalencia. UCB1 frente a uniforme da una señal, pero es exploratoria.

**¿Por qué no agregaron corridas si la potencia era baja?**
El protocolo prohíbe ampliar la muestra después de ver los resultados. Hacerlo inflaría el
error tipo I. Cualquier confirmación usará semillas desde la 120 y un pre-registro nuevo.

**¿Por qué C1 no cuenta si p < 0,05?**
La regla exige además un IC bajo cero y una media de a lo sumo −0,25, y se fijó antes de
ejecutar. El intervalo de C1 es [−1,850; +0,279] e incluye cero.

**¿UCB1 es su nueva propuesta?**
Todavía no. C4 muestra que superó a D-MAB, pero UCB1 frente a uniforme es exploratorio. Primero
hay que confirmarlo con semillas nuevas.

**¿Por qué la cartera si dos Tabu rinde parecido?**
La elegimos por simplicidad y porque conserva una referencia. Bajo congestión, C3 no es
significativa, así que no afirmamos que supere a dos Tabu. Ese control sigue obligatorio.

**¿Por qué no comparan a igual tiempo?**
El tiempo de pared varió entre sesiones del mismo equipo, sin causa identificada. Por eso el
control principal son las evaluaciones. Corrimos un piloto de 40 corridas, solo descriptivo.

**¿Por qué bajaron cirujanos y no salas?**
Con la misma sala en ambas etapas, la espera depende del cirujano. Menos salas alargan la cola
antes de la anestesia. La calibración confirmó esa predicción, registrada antes de medir.

**¿Por qué el umbral es 0,25?**
Los tiempos son múltiplos de 0,5 minutos, y un paso de espera total mueve `f` en 0,25. Una
diferencia menor no representa un paso en ningún componente del calendario.

**¿El catálogo de congestión mide generalización?**
No. Sus instancias son nuevas para la búsqueda, pero comparten el perfil de duraciones del
catálogo estándar. No es un dominio independiente.

**¿Es un Tabu asistido por población?**
No en la práctica. Retirar el archivo de 30 soluciones dejó idénticas 120 corridas, así que
esas soluciones solo aportan el punto de partida.
