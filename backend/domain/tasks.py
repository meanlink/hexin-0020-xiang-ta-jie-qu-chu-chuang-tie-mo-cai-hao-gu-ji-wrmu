from core.errors import DomainError
from domain.fit_geometry import solve_fit
from domain.history import feature_values, observations
from domain.inventory import get_roll
from domain.openings import check_revision, get_window
from domain.scrap_model import predict_loss
from domain.sheet_store import insert_draft

ESTIMATE_CUT = "estimate_window_film_cut"


def run(conn, kind, payload):
    if kind != ESTIMATE_CUT:
        raise DomainError(422, "unknown window film task")
    window = get_window(conn, payload["window_code"], lock=True)
    check_revision(window, payload["window_revision"])
    roll = get_roll(conn, payload["roll_code"])
    fit = solve_fit(window, roll)
    loss, metrics = predict_loss(observations(conn), feature_values(window, roll, fit))
    sheet_id = insert_draft(conn, window, roll, fit, loss, metrics)
    return {
        "sheet_id": str(sheet_id),
        "window_revision": window["revision"],
        "feed_mm": fit["feed_mm"],
        "loss_mm": loss,
        "allowance_mm": fit["feed_mm"] + loss,
        "observation_digest": metrics["observation_digest"],
    }
