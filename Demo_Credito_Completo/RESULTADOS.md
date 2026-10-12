# Resultados — comparación de modelos

Los tres modelos se evalúan con el mismo protocolo de validación cruzada
(`StratifiedKFold`, 5 pliegues, semilla 42) sobre las 1,000 solicitudes de
`datos/credit_g.csv`. "Malos detectados" es el recall sobre la clase `bad`
(créditos malos), es decir: de todos los créditos malos reales, qué
proporción marca el modelo como malos.

| Modelo        | Exactitud media | Desviación | Malos detectados |
|---------------|-----------------|------------|-------------------|
| Árbol         | 0.698           | 0.017      | 0.530             |
| Random Forest | 0.759           | 0.006      | 0.377             |
| Boosting      | 0.752           | 0.021      | 0.490             |

## Lectura de los resultados

- **Línea base "siempre bueno":** predecir siempre `good` acierta el 70.0%
  de las veces (proporción de clases del dataset). El **Árbol** sin límite
  de profundidad queda por debajo de esa línea (0.698), es decir, no aporta
  nada frente a no usar ningún modelo.
- **Random Forest** tiene la exactitud media más alta y, con diferencia, la
  desviación más baja (0.006): es el modelo más estable entre pliegues.
  Sin embargo, es el que **menos créditos malos detecta** (37.7%): tiende a
  predecir `good` con más frecuencia, lo cual conviene poco si el objetivo
  del negocio es no dar crédito a quien no pagará.
- **Boosting** queda muy cerca de Random Forest en exactitud (0.752) pero
  detecta considerablemente más créditos malos (49.0%), con una desviación
  algo mayor (0.021). Es el mejor compromiso entre exactitud y detección de
  riesgo de los tres.
- En conjunto, la exactitud por sí sola es una métrica engañosa en este
  dataset desbalanceado (70/30): hay que mirarla junto con la proporción de
  malos detectados antes de elegir un modelo para producción.
