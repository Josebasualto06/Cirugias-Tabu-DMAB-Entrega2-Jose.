# Informe final (Entrega 3)

`main.tex` contiene ahora el informe completo. La Entrega 3 agrega dos secciones
y corrige la coherencia de las anteriores:

- [`resultados.tex`](resultados.tex): sección 4, Resultados y discusión (3 páginas).
- [`conclusion.tex`](conclusion.tex): sección 5, Conclusión (1 página).
- [`Entrega_3_Tabu_DMAB.pdf`](Entrega_3_Tabu_DMAB.pdf): PDF final, 14 páginas.

La tabla y la figura se generan desde los resultados archivados. Ninguna cifra
se escribe a mano:

```bash
python experiments/scripts/descriptivos_entrega3.py   # descriptivos de congestión
python experiments/scripts/tabla_resultados.py        # tablas/tabla_comparaciones.tex
python experiments/scripts/forest_comparaciones.py    # figuras/forest_comparaciones.pdf
```

Dos verificadores de solo lectura acompañan al texto:

```bash
python -X utf8 informe/verificar_cifras.py   # cada cifra contra su archivo fuente
python -X utf8 informe/verificar_estilo.py   # frases de 25 palabras o más y conectores
```

Para compilar, desde este directorio:

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error \
  -jobname=Entrega_3_Tabu_DMAB main.tex
```

Los PDF de las Entregas 1 y 2 se conservan como se entregaron. El resto de este
archivo describe la Entrega 1.

# Informe de Entrega 1

- Fuente principal: [`main.tex`](main.tex).
- Portada de asignatura: [`Portadas/portada_principal.tex`](Portadas/portada_principal.tex).
- Bibliografía APA/Biber: [`referencias.bib`](referencias.bib).
- PDF final: [`Entrega_1_Tabu_DMAB.pdf`](Entrega_1_Tabu_DMAB.pdf).
- [Correspondencia con la pauta y fuentes](criterios-entrega.md).

Autores: José Basualto, Cristopher Dauros y Carlos Ruz.

## Formato institucional

El informe **usa directamente** `pucv_inf_2024.sty` y el encabezado gráfico
`Portadas/imagenes/encabezado.png` de la plantilla de la Escuela de Ingeniería
Informática PUCV facilitada para el proyecto. Sus copias conservan los mismos
hashes SHA-256 que los archivos originales. La portada para asignaturas se
adaptó con título, autores, ramo y fecha; se corrigió el folio de la portada
para que no aparezca numerada.

Se mantienen papel carta, cuerpo Times de 12 puntos, márgenes de 2,5 cm,
interlineado sencillo, sangría de 1 cm, 10 puntos entre párrafos, títulos del
paquete institucional y folio inferior derecho. El contenido usa numeración
arábiga y la portada no lleva folio.

El informe se titula **Programación de cirugías electivas mediante búsqueda
tabú y selección adaptativa de movimientos** y lleva fecha **2 de octubre de
2026**. El PDF tiene **siete páginas físicas**: cinco de contenido,
una portada institucional y una de referencias. La distribución es:

| Página física | Contenido |
|---|---|
| 1 | Portada institucional. |
| 2 | Resumen y palabras clave, en página propia. |
| 3 | Introducción y síntesis de estudios relacionados. |
| 4 | Problema, restricciones, función objetivo y componentes MH y ML. |
| 5 | Orquestación, datos, controles, evaluación y riesgos metodológicos. |
| 6 | Conclusión en dos párrafos, de cinco oraciones y menos de media página. |
| 7 | Referencias. |

El resumen contiene **165 palabras**, dentro del rango de 150–200. Se explican
las variables debajo de las dos ecuaciones y la comparación se identifica como
**Tabla 1**. El conteo de cinco páginas corresponde al contenido; la portada
institucional y las referencias se contabilizan aparte.

## Alcance de la propuesta

La componente ML interviene en la **evolución de la búsqueda**, seleccionando
el tipo de movimiento con que Tabu genera cada vecino. La cartera final ejecuta
Tabu uniforme y Tabu con D-MAB con 3.030 evaluaciones por camino y conserva
el mejor calendario factible. Ese reparto fijo y la selección final son
deterministas; D-MAB aprende en línea dentro de una de las trayectorias.

El informe contrasta cinco estudios de 2024–2026 y el fundamento de D-MAB
de 2008 en un párrafo de síntesis. Presenta el plan de evaluación con igual
presupuesto, referencias constructivas, dos Tabu independientes y ablación
sin Page–Hinkley. La entrega presenta la arquitectura y el protocolo previsto;
el beneficio de la adaptación se plantea como una hipótesis que deberá
contrastarse durante el semestre.

## Compilación

Se requiere una distribución LaTeX con `biblatex` y Biber. En un entorno con
Biber funcional, desde este directorio:

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error \
  -jobname=Entrega_1_Tabu_DMAB main.tex
```

La compilación manual equivalente es `pdflatex`, `biber` y dos pasadas más de
`pdflatex`, siempre con el nombre de trabajo `Entrega_1_Tabu_DMAB`.

## Fuentes docentes

Se consultaron la pauta OII464, los tres documentos de metodología de
investigación, la presentación del problema, la taxonomía ML → MH del curso
y el [repositorio docente](https://github.com/Saicooh/OII464_Hospitales).
La bibliografía distingue estas fuentes de los seis estudios relacionados.
