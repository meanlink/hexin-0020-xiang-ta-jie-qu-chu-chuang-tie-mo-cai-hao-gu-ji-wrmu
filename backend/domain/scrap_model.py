import hashlib
import json
from math import ceil

import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_pinball_loss
from sklearn.model_selection import train_test_split

from core.errors import DomainError
from domain.history import FEATURES

RANDOM_STATE = 2020
LOSS_QUANTILE = 0.8
CUT_MARK_MM = 5


def predict_loss(rows, profile):
    if len(rows) < 45:
        raise DomainError(409, "at least 45 completed cut observations are required")
    data = np.array([[row[field] for field in FEATURES] for row in rows], dtype=float)
    wanted = np.array([[profile[field] for field in FEATURES]], dtype=float)
    if np.any(wanted < data.min(axis=0)) or np.any(wanted > data.max(axis=0)):
        raise DomainError(409, "physical cut dimensions exceed the measured scrap model's range")
    targets = np.array([row["loss_mm"] for row in rows], dtype=float)
    x_train, x_holdout, y_train, y_holdout = train_test_split(
        data, targets, test_size=0.2, random_state=RANDOM_STATE,
    )
    model = GradientBoostingRegressor(
        loss="quantile", alpha=LOSS_QUANTILE, n_estimators=90, max_depth=2,
        min_samples_leaf=6, learning_rate=0.055, random_state=RANDOM_STATE,
    )
    model.fit(x_train, y_train)
    holdout = np.maximum(model.predict(x_holdout), 0)
    predicted = max(float(model.predict(wanted)[0]), 0)
    rounded = ceil(predicted / CUT_MARK_MM) * CUT_MARK_MM
    return rounded, {
        "algorithm": "gradient_boosting_quantile_regression",
        "loss_quantile": LOSS_QUANTILE,
        "features": FEATURES,
        "training_rows": len(y_train),
        "holdout_rows": len(y_holdout),
        "pinball_loss_mm": round(float(mean_pinball_loss(y_holdout, holdout, alpha=LOSS_QUANTILE)), 3),
        "holdout_coverage": round(float(np.mean(y_holdout <= holdout)), 3),
        "observation_digest": hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest(),
    }
