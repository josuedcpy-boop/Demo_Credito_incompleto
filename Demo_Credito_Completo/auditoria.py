"""Paso 6 · Auditoría: ¿el modelo se equivoca más con algún subgrupo?"""
import pandas as pd
from sklearn.model_selection import cross_val_predict


def exactitud_por_subgrupo(pipeline, X, y, cv, columna):
 # una predicción por solicitud, hecha sin que el modelo la viera
 pred = cross_val_predict(pipeline, X, y, cv=cv)
 # una fila por solicitud: su grupo y si acertó
 tabla = pd.DataFrame({"grupo": X[columna].values, "acierto": pred == y.values})
 # por grupo: promedio de aciertos y cuántos casos hay
 return tabla.groupby("grupo")["acierto"].agg(exactitud="mean", casos="count")
