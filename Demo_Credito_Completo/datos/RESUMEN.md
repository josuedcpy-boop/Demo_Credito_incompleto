# Resumen de datos — credit_g.csv

## Tamaño de la tabla
- **Filas:** 1000
- **Columnas:** 21

## Proporción de clases (columna `clase`, variable objetivo)
| Clase | Conteo | Proporción |
|-------|--------|------------|
| good  | 700    | 70.0% |
| bad   | 300    | 30.0% |

Dataset desbalanceado (ratio ~2.33:1 a favor de `good`).

## Columnas categóricas (tipo `object`)
14 columnas categóricas (incluyendo la variable objetivo):

- `checking_status`
- `credit_history`
- `purpose`
- `savings_status`
- `employment`
- `personal_status`
- `other_parties`
- `property_magnitude`
- `other_payment_plans`
- `housing`
- `job`
- `own_telephone`
- `foreign_worker`
- `clase` (variable objetivo)

## Columnas numéricas (tipo `int64`)
7 columnas numéricas:

- `duration`
- `credit_amount`
- `installment_commitment`
- `residence_since`
- `age`
- `existing_credits`
- `num_dependents`

## Valores faltantes
No se encontraron valores faltantes (NaN) en ninguna de las 21 columnas del dataset.
