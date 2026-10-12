# Reporte de auditoría — modelos de crédito (German Credit)

Auditoría de solo lectura sobre el código entregado por el ingeniero de modelos
(`modelos.py`, `validacion.py`, `busqueda.py`, `auditoria.py`, `main.py`) y sobre
`RESULTADOS.md`. No se modificó ningún archivo del proyecto.

## Resumen de veredictos

| # | Revisión | Veredicto |
|---|----------|-----------|
| 1 | Fuga de datos — codificación dentro del Pipeline | **PASA** |
| 2 | Partición — comparación partición única vs. validación cruzada | **PASA** |
| 3 | Partición — búsqueda de hiperparámetros con prueba reservada | **PASA** |
| 4 | Subgrupos — `housing` y `personal_status` (estado civil) | **PASA**, con disparidad a vigilar |
| 5 | Subgrupos — `age` (edad) | **FALLA** |

*(Actualizado tras completarse los `TODO 7`–`TODO 12`; los puntos 3 y 4 ya se pudieron ejecutar y re-auditar con resultados reales.)*

---

## 1. Fuga de datos: ¿la codificación va dentro del Pipeline? — PASA

**Evidencia:** [modelos.py:9-15](modelos.py#L9-L15) construye `crear_pipeline` como
`Pipeline([("prep", prep), ("modelo", modelo)])`, donde `prep` es el
`ColumnTransformer` con el `OrdinalEncoder`. Al ser un paso del `Pipeline` (y no una
transformación aplicada antes de separar datos), `prep` se ajusta de nuevo en cada
llamada a `.fit()`, por lo que en validación cruzada (`cross_val_score`,
`cross_val_predict` en [validacion.py:10](validacion.py#L10) y
[validacion.py:16](validacion.py#L16)) y en partición única
([validacion.py:27](validacion.py#L27)) el encoder solo ve el pliegue/partición de
entrenamiento correspondiente. No hay ajuste previo sobre `X` completo en ningún
punto del flujo ([main.py](main.py)).

Esto está además verificado por una prueba automática ya escrita:
[tests/test_modelo.py:25-27](tests/test_modelo.py#L25-L27)
(`test_codificacion_dentro_del_pipeline`), que confirma que `"prep"` es un paso
nombrado del pipeline.

**Veredicto: PASA.**

## 2. Partición: partición única (75/25) vs. validación cruzada — PASA

**Evidencia:** [validacion.py:20-29](validacion.py#L20-L29) (`particion_unica`) usa
`train_test_split(..., stratify=y)` con 10 semillas distintas, clona un pipeline sin
ajustar en cada repetición (`clone(pipeline)`) y evalúa con `.score()` solo sobre el
conjunto de prueba de esa repetición. No se reutiliza un pipeline ya ajustado entre
semillas, y el reparto es estratificado (conserva la proporción 70/30 de clases). El
mismo esquema `cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)`
definido una sola vez en [datos.py:12](datos.py#L12) se reutiliza para los tres
modelos ([main.py:14-18](main.py#L14-L18)), lo que hace el protocolo comparable
entre modelos, como describe [RESULTADOS.md](RESULTADOS.md).

**Veredicto: PASA**, para la parte ya implementada (sección 2 de `main.py`).

## 3. Partición: búsqueda de hiperparámetros con prueba reservada — PASA

**Evidencia:** `buscar_con_prueba` en [busqueda.py:21-28](busqueda.py#L21-L28)
reserva el 20% con `train_test_split(..., stratify=y, random_state=1)` **antes**
de construir el `GridSearchCV`, y el `.fit()` de la búsqueda solo recibe
`X_ent, y_ent` (el 80%); el conjunto reservado (`X_pru, y_pru`) se usa una única
vez, al final, con `busqueda.score(X_pru, y_pru)`. No hay ningún punto donde el
20% reservado participe en la elección de hiperparámetros.

Resultado real al ejecutar `main.py` sobre el árbol:
- Búsqueda completa (`buscar`, 40 combinaciones × 5 pliegues): mejor combinación
  `max_depth=5, min_samples_leaf=1`, exactitud de búsqueda 0.73.
- Con prueba reservada: la búsqueda reportó 0.705 y la prueba (datos nunca vistos)
  dio 0.780. La prueba no salió por debajo de lo que dijo la búsqueda, que es lo
  que se espera cuando no hay fuga (de haber fuga, veríamos lo contrario: la
  búsqueda optimista y la prueba mucho peor).

**Veredicto: PASA.**

## 4. Subgrupos: `housing` y `personal_status` (estado civil) — PASA, con disparidad a vigilar

**Evidencia del método:** `exactitud_por_subgrupo` en
[auditoria.py:6-12](auditoria.py#L6-L12) usa `cross_val_predict(pipeline, X, y,
cv=cv)` para obtener una predicción por solicitud hecha siempre con un modelo que
no la vio en entrenamiento (fuera de pliegue), y solo después agrupa por columna.
No hay `.fit().predict()` sobre los mismos datos de entrenamiento, así que la
exactitud por subgrupo no está inflada.

**Resultados reales** (Random Forest, [main.py:38-41](main.py#L38-L41)):

| `housing` | exactitud | casos |
|---|---|---|
| for free | 0.68 | 108 |
| own | 0.78 | 713 |
| rent | 0.72 | 179 |

| `personal_status` | exactitud | casos |
|---|---|---|
| female div/dep/mar | 0.74 | 310 |
| male div/sep | 0.62 | 50 |
| male mar/wid | 0.77 | 92 |
| male single | 0.78 | 548 |

**Hallazgo a vigilar (no es fuga de datos, es una observación de equidad):** el
grupo `male div/sep` tiene la exactitud más baja (0.62, ~15 puntos por debajo del
resto) y además es el grupo más pequeño (50 de 1000 casos), por lo que esa cifra
es más ruidosa y merece repetirse con otra semilla antes de sacar conclusiones
fuertes. En `housing`, `for free` (0.68) también queda por debajo de `own` (0.78).
Esto no invalida el pipeline, pero es información que el negocio debería conocer
antes de usar el Random Forest para decidir crédito a estos subgrupos.

**Veredicto: PASA** (el mecanismo de medición es correcto y sin fuga); se deja
constancia de la disparidad encontrada para seguimiento.

## 5. Subgrupos: `age` (edad) — FALLA

**Evidencia:** El agente auditor tiene instrucción explícita de revisar subgrupos
por edad, estado civil y vivienda, pero:
- `age` es una columna numérica (`int64`, ver
  [datos/RESUMEN.md:40](datos/RESUMEN.md#L40)), con un valor por cada edad distinta;
  `exactitud_por_subgrupo(..., "age")` agruparía por cada edad individual en lugar
  de por rangos, produciendo grupos minúsculos y una tabla poco interpretable. No
  existe en el proyecto ningún mecanismo de *binning* (p. ej. `pd.cut` por rangos de
  edad) para esta columna.
- Independientemente de lo anterior, `main.py:40`
  (`for columna in ("housing", "personal_status")`) ni siquiera incluye `"age"` en
  el bucle de auditoría. Aunque se complete `TODO 10`, la auditoría por edad no se
  ejecutaría con el código actual.

**Veredicto: FALLA.** Falta tanto el *binning* de edad como la llamada en `main.py`
que audite ese subgrupo.

---

## Notas fuera de alcance de esta auditoría

- `curva_aprendizaje` ([curvas.py:10-15](curvas.py#L10-L15), `TODO 7`) ya está
  implementada y corre; no se incluye un veredicto porque no corresponde a fuga de
  datos, partición ni subgrupos. Dato de contexto: tanto el Árbol (entrenamiento
  1.00 vs. validación 0.70) como el Random Forest (1.00 vs. 0.76) muestran
  sobreajuste claro sin límite de profundidad, lo que es consistente con que la
  búsqueda de hiperparámetros (punto 3) haya elegido `max_depth=5` en vez de
  `None`.
- El `OrdinalEncoder` trata `housing` y `personal_status` como si tuvieran un orden
  (0, 1, 2…) aunque son categorías sin orden natural. No es un problema de fuga de
  datos, pero puede afectar la calidad del modelo y conviene que el ingeniero de
  modelos lo tenga presente si se usa en subgrupos de equidad.
