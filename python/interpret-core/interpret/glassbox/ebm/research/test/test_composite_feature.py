import pandas as pd
import numpy as np
import pytest
from sklearn.exceptions import NotFittedError

from ...ebm import ExplainableBoostingRegressor, ExplainableBoostingClassifier
from .....test.utils import synthetic_multiclass, synthetic_classification, synthetic_regression
from ..composite_importance import (
    compute_composite_importance,
    _get_composite_name,
    append_composite_importance
)

def test_composite_name():
    mocked_ebm_term_names = ["Ft1", "Ft2", "Ft3", "Ft4", "Ft1 x Ft2"]

    assert "Ft3" == _get_composite_name(["Ft3"], mocked_ebm_term_names)

    composite_names = ["Ft1", "Ft3", "Ft1 x Ft2"]
    assert "Ft1 & Ft3 & Ft1 x Ft2" == _get_composite_name(composite_names, mocked_ebm_term_names)

    # Ft2, Ft4, Ft1 x Ft2
    composite_indices = [1, 3, 4]
    assert "Ft2 & Ft4 & Ft1 x Ft2" == _get_composite_name(composite_indices, mocked_ebm_term_names)

    out_of_bound_indices = [-1, 5]
    with pytest.raises(ValueError):
        _get_composite_name(out_of_bound_indices, mocked_ebm_term_names)

def test_append_composite_importance():
    data = synthetic_regression()
    X = data["full"]["X"]
    y = data["full"]["y"]
    composite_names = ["A", "B"]

    ebm = ExplainableBoostingRegressor()
    ebm.fit(X, y)
    global_explanation = ebm.explain_global()
    local_explanation = ebm.explain_local(X)

    # An exception should be raised when the EBM is not fitted
    non_fitted_ebm = ExplainableBoostingRegressor()
    with pytest.raises(NotFittedError):
        append_composite_importance(composite_names, non_fitted_ebm, global_explanation, X)

    # An exception should be raised when the explanation is not valid
    with pytest.raises(ValueError):
        append_composite_importance(composite_names, ebm, local_explanation, X)

    wrong_global_exp = ebm.explain_global()
    wrong_global_exp._internal_obj = None
    with pytest.raises(ValueError):
        append_composite_importance(composite_names, ebm, wrong_global_exp, X)

    # An exception should be raised when none of the input terms is valid
    with pytest.raises(ValueError):
        append_composite_importance(["Z", -1, 20], ebm, global_explanation, X)

    append_composite_importance(composite_names, ebm, global_explanation, X)
    assert "A & B" in global_explanation._internal_obj["overall"]["names"]
    assert compute_composite_importance(composite_names, ebm, X) in global_explanation._internal_obj["overall"]["scores"]

    append_composite_importance(composite_names, ebm, global_explanation, X, composite_name="Comp 1")
    assert "Comp 1" in global_explanation._internal_obj["overall"]["names"]
    assert compute_composite_importance(composite_names, ebm, X) in global_explanation._internal_obj["overall"]["scores"]

def _check_composite_importance(X, y, ebm):
    composite_names = ["A", "B"]
    composite_indices = [0, 1]

    # An exception should be raised when the EBM is not fitted
    with pytest.raises(NotFittedError):
        compute_composite_importance(composite_names, ebm, X)

    ebm.fit(X, y)

    # An exception should be raised when at least one of the input terms is invalid
    with pytest.raises(ValueError):
        compute_composite_importance(["A", "B", 10], ebm, X)

    with pytest.raises(ValueError):
        compute_composite_importance([], ebm, X)

    # It should be the same for term names and indices
    assert compute_composite_importance(composite_names, ebm, X) == \
        compute_composite_importance(composite_indices, ebm, X)

    # For one term, its importance should be approx. equal to the one computed by interpret
    # TODO For multiclass this is currently consistent with interpret, but might be changed
    assert pytest.approx(ebm.get_importances()[0]) == compute_composite_importance(["A"], ebm, X)

    mixed_list = ["A", 1]
    assert compute_composite_importance(["A", "B"], ebm, X) == \
        compute_composite_importance(mixed_list, ebm, X)

    _, contributions = ebm.predict_and_contrib(X)
    assert compute_composite_importance(composite_names, ebm, X, contributions) == \
        compute_composite_importance(composite_names, ebm, X)

def test_composite_importance_regression():
    data = synthetic_regression()
    X = data["full"]["X"]
    y = data["full"]["y"]

    ebm = ExplainableBoostingRegressor()
    _check_composite_importance(X, y, ebm)

def test_composite_importance_classification():
    data = synthetic_classification()
    X = data["full"]["X"]
    y = data["full"]["y"]

    ebm = ExplainableBoostingClassifier()
    _check_composite_importance(X, y, ebm)

def test_composite_importance_multiclass():
    data = synthetic_multiclass()
    X = data["full"]["X"]
    y = data["full"]["y"]

    ebm = ExplainableBoostingClassifier()
    _check_composite_importance(X, y, ebm)