"""Paso 5 · Búsqueda de hiperparámetros, y la prueba honesta con datos que la búsqueda nunca vio."""
from sklearn.model_selection import GridSearchCV, train_test_split   # GridSearchCV: prueba todas las combinaciones de una cuadrícula

# El espacio de búsqueda: es parte del resultado, por eso se documenta. El prefijo 'modelo__' apunta al paso 'modelo' del pipeline.
PARAM_GRID = {
    "modelo__max_depth": [1, 2, 3, 4, 5, 7, 10, None],     # cuántas preguntas seguidas puede hacer el árbol (None = sin límite)
    "modelo__min_samples_leaf": [1, 2, 5, 10, 20],         # cuántos casos como mínimo debe tener cada hoja final
}


def buscar(pipeline, X, y, cv):
 # cada combinación se evalúa con la validación cruzada
 busqueda = GridSearchCV(pipeline, PARAM_GRID, cv=cv)
 # 40 combinaciones x 5 pliegues = 200 ajustes
 busqueda.fit(X, y)
 # la configuración ganadora y su exactitud (optimista, ya la vimos mucho)
 return busqueda.best_params_, busqueda.best_score_



def buscar_con_prueba(pipeline, X, y, cv):
 # reserva el 20% desde el inicio
 X_ent, X_pru, y_ent, y_pru = train_test_split(X, y, test_size=0.20, stratify=y,
random_state=1)
 # la búsqueda solo ve el 80%
 busqueda = GridSearchCV(pipeline, PARAM_GRID, cv=cv).fit(X_ent, y_ent)
 # (lo que dijo la búsqueda, lo que pasa con datos nuevos)
 return busqueda.best_score_, busqueda.score(X_pru, y_pru)

