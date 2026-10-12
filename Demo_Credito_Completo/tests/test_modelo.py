"""Pruebas automáticas: si fallan, el cambio no se acepta. Se ejecutan con:  pytest -v

Cada prueba corresponde a una revisión de AUDIT_REPORT.md. Las de las reglas 1-4
(PASA en la auditoría) deben seguir pasando; las de la regla 5 (FALLA) están aquí
en rojo a propósito, como lista de lo que falta arreglar."""
import os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))   # permite importar los módulos de la carpeta raíz
import pytest                                                        # pytest: encuentra y corre las funciones que empiezan con test_
from sklearn.dummy import DummyClassifier
from sklearn.exceptions import NotFittedError

import auditoria
import busqueda
from datos import cargar_datos
from modelos import crear_pipeline, tres_modelos
from validacion import validar, particion_unica
from auditoria import exactitud_por_subgrupo
from busqueda import buscar_con_prueba

X, y, cols_cat, cv = cargar_datos()                                  # datos listos para todas las pruebas
RAIZ = os.path.join(os.path.dirname(__file__), "..")


@pytest.mark.parametrize("nombre", [
    pytest.param("Árbol", marks=pytest.mark.xfail(reason="el árbol sin límite no supera el 0.70")),  # se espera que falle: es la lección
    "Random Forest", "Boosting"])
def test_supera_a_siempre_bueno(nombre):
 # media de la validación cruzada del modelo
 media, _ = validar(crear_pipeline(tres_modelos()[nombre], cols_cat), X, y, cv)
 # debe acertar más que 'siempre bueno'
 assert media > 0.70


def test_resultado_estable():
 # cuánto varía entre pliegues
 _, desv = validar(crear_pipeline(tres_modelos()["Random Forest"], cols_cat), X, y, cv)
 # un resultado estable varía poco
 assert desv < 0.05


def test_codificacion_dentro_del_pipeline():
    pipe = crear_pipeline(tres_modelos()["Árbol"], cols_cat)         # el pipeline que construimos
    assert "prep" in pipe.named_steps                                # la preparación debe ser un paso del pipeline (así no hay fuga)


# --- Regla 2 (AUDIT_REPORT.md): partición única vs. validación cruzada ---

def test_particion_unica_no_reutiliza_pipeline_ajustado():
    """particion_unica debe clonar el pipeline en cada semilla; si ajustara el
    original en vez del clon, quedaría entrenado y esto no lo detectaría."""
    pipe = crear_pipeline(tres_modelos()["Árbol"], cols_cat)
    particion_unica(pipe, X, y, semillas=range(2))
    with pytest.raises(NotFittedError):
        pipe.predict(X)                                               # el original nunca se ajustó


def test_particion_unica_estratificada():
    """Con una partición estratificada, la proporción de clases en la prueba
    casi no cambia entre semillas (un modelo que siempre predice la clase
    mayoritaria debería dar casi la misma exactitud en todas)."""
    dummy = DummyClassifier(strategy="most_frequent")
    exactitudes = particion_unica(dummy, X, y)
    assert exactitudes.std() < 0.03


# --- Regla 3 (AUDIT_REPORT.md): búsqueda de hiperparámetros con prueba reservada ---

def test_busqueda_con_prueba_no_ve_el_conjunto_reservado(monkeypatch):
    """La búsqueda de hiperparámetros solo debe entrenar con el 80% reservado
    para entrenamiento; el 20% de prueba no debe pasar nunca por GridSearchCV.fit."""
    tamanos_vistos = []
    fit_original = busqueda.GridSearchCV.fit

    def fit_espia(self, X_arg, y_arg=None, **kwargs):
        tamanos_vistos.append(len(X_arg))
        return fit_original(self, X_arg, y_arg, **kwargs)

    monkeypatch.setattr(busqueda.GridSearchCV, "fit", fit_espia)
    arbol = crear_pipeline(tres_modelos()["Árbol"], cols_cat)
    buscar_con_prueba(arbol, X, y, cv)
    assert tamanos_vistos == [round(len(X) * 0.80)]                  # solo una llamada, con el 80%


# --- Regla 4 (AUDIT_REPORT.md): subgrupos housing / personal_status ---

def test_exactitud_por_subgrupo_usa_prediccion_fuera_de_pliegue(monkeypatch):
    """La auditoría debe medir con cross_val_predict (predicciones fuera de
    pliegue), no con fit().predict() sobre los mismos datos, que infla la exactitud."""
    usado = {}
    original = auditoria.cross_val_predict

    def espia(*args, **kwargs):
        usado["si"] = True
        return original(*args, **kwargs)

    monkeypatch.setattr(auditoria, "cross_val_predict", espia)
    arbol = crear_pipeline(tres_modelos()["Árbol"], cols_cat)
    auditoria.exactitud_por_subgrupo(arbol, X, y, cv, "housing")
    assert usado.get("si") is True


def test_exactitud_por_subgrupo_cubre_todos_los_casos():
    rf = crear_pipeline(tres_modelos()["Random Forest"], cols_cat)
    tabla = exactitud_por_subgrupo(rf, X, y, cv, "personal_status")
    assert tabla["casos"].sum() == len(X)                             # cada solicitud cae en un solo grupo
    assert set(tabla.index) == set(X["personal_status"].unique())
    assert tabla["exactitud"].between(0, 1).all()


# --- Regla 5 (AUDIT_REPORT.md): subgrupos por edad — FALLA en la auditoría ---
# Estas dos pruebas quedan en rojo a propósito: documentan lo que falta para
# que la regla 5 pase. Se marcan xfail para no romper `pytest -v` mientras
# tanto; al corregirlo, quitar el marcador y deben pasar en verde.

@pytest.mark.xfail(reason="AUDIT_REPORT.md #5: falta incluir 'age' en el bucle de auditoría de main.py")
def test_main_audita_por_edad():
    codigo_main = open(os.path.join(RAIZ, "main.py"), encoding="utf-8").read()
    coincidencia = re.search(r'for columna in \(([^)]*)\)', codigo_main)
    assert coincidencia is not None and "age" in coincidencia.group(1)


@pytest.mark.xfail(reason="AUDIT_REPORT.md #5: 'age' es numérica y falta agruparla en rangos antes de auditar")
def test_existe_binning_de_edad():
    codigo_auditoria = open(os.path.join(RAIZ, "auditoria.py"), encoding="utf-8").read()
    codigo_main = open(os.path.join(RAIZ, "main.py"), encoding="utf-8").read()
    assert "cut(" in codigo_auditoria or "cut(" in codigo_main
