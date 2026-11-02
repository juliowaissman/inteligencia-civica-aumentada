import numpy as np
import pandas as pd
import pytest

from iica import metodo


def test_normalizar_minmax_y_sentido():
    s = pd.Series([10.0, 20.0, 30.0], index=list("abc"))
    assert metodo.normalizar(s).tolist() == [0.0, 50.0, 100.0]
    assert metodo.normalizar(s, sentido=-1).tolist() == [100.0, 50.0, 0.0]


def test_normalizar_con_limites_fijos_recorta():
    s = pd.Series([0.0, 5.0, 15.0])
    assert metodo.normalizar(s, minimo=0, maximo=10).tolist() == [0.0, 50.0, 100.0]


def test_normalizar_constante_no_divide_entre_cero():
    s = pd.Series([3.0, 3.0, np.nan])
    out = metodo.normalizar(s)
    assert out.iloc[0] == 100.0 and np.isnan(out.iloc[2])


def test_puntaje_dimension_promedia_indicadores():
    norm = pd.DataFrame({"a": [0.0, 100.0], "b": [100.0, 100.0], "c": [50.0, 0.0]})
    dims = metodo.puntajes_dimension(norm, {"a": 1, "b": 1, "c": 2})
    assert dims[1].tolist() == [50.0, 100.0]
    assert dims[2].tolist() == [50.0, 0.0]


def test_geometrica_penaliza_desequilibrio():
    dims = pd.DataFrame({1: [50.0, 100.0], 2: [50.0, 0.0]})
    g = metodo.geometrica(dims)
    a = metodo.aritmetica(dims)
    assert a.iloc[0] == a.iloc[1] == 50.0
    assert g.iloc[0] > g.iloc[1]  # el perfil equilibrado gana con la geométrica


def test_geometrica_nan_si_falta_dimension():
    dims = pd.DataFrame({1: [50.0], 2: [np.nan]})
    assert np.isnan(metodo.geometrica(dims).iloc[0])


def test_geometrica_valores_extremos():
    dims = pd.DataFrame({1: [100.0, 0.0], 2: [100.0, 0.0]})
    g = metodo.geometrica(dims)
    assert g.iloc[0] == pytest.approx(100.0)
    assert g.iloc[1] == pytest.approx(1.0)


def test_atipicos_winsoriza_valor_extremo():
    s = pd.Series([1.0, 2, 2, 3, 3, 3, 4, 4, 5, 100], index=list("abcdefghij"))
    t, n = metodo.tratar_atipicos(s)
    assert n >= 1
    assert t["j"] == 5.0  # el extremo baja al siguiente valor
    assert t["a"] == 1.0


def test_atipicos_no_toca_distribucion_normal():
    s = pd.Series(np.linspace(0, 10, 32))
    t, n = metodo.tratar_atipicos(s)
    assert n == 0 and t.equals(s)


def test_sensibilidad_intervalos_ordenados():
    dims = pd.DataFrame({1: [90.0, 50.0, 10.0], 2: [80.0, 50.0, 20.0]}, index=list("xyz"))
    s = metodo.sensibilidad(dims, n=50)
    assert (s["rango_p5"] <= s["rango_mediana"]).all()
    assert (s["rango_mediana"] <= s["rango_p95"]).all()
    assert s.loc["x", "rango_mediana"] == 1
