from core.errors import DomainError
from domain.inventory import usable_width
from domain.vocabulary import Axis, Pattern

JOIN_OVERLAP_MM = 20
MIN_PANEL_WIDTH_MM = 150


def _layout(orientation, across, advance, available_width, allow_seam):
    if across <= available_width:
        return {"orientation": orientation, "widths_mm": [across], "advance_mm": advance}
    if not allow_seam:
        return None
    joined_width = across + JOIN_OVERLAP_MM
    left = (joined_width + 1) // 2
    right = joined_width - left
    if not MIN_PANEL_WIDTH_MM <= right <= left <= available_width:
        return None
    return {"orientation": orientation, "widths_mm": [left, right], "advance_mm": advance}


def solve_fit(window, roll):
    if window["finish_code"] != roll["finish_code"]:
        raise DomainError(409, "roll finish does not match the window exhibit")
    if window["pattern_axis"] == Axis.VERTICAL and roll["pattern"] != Pattern.LENGTHWISE:
        raise DomainError(409, "vertical pattern requires lengthwise-grained film")
    usable = usable_width(roll)
    bleed = 2 * window["bleed_mm"]
    padded_width, padded_height = window["width_mm"] + bleed, window["height_mm"] + bleed
    candidates = [_layout("upright", padded_width, padded_height, usable, window["allow_seam"])]
    if window["pattern_axis"] == Axis.ANY:
        candidates.append(_layout("sideways", padded_height, padded_width, usable, window["allow_seam"]))
    possible = [option for option in candidates if option]
    if not possible:
        raise DomainError(409, "usable roll width cannot fit the glazing with its seam and grain constraints")
    result = min(
        possible, key=lambda option: (len(option["widths_mm"]) * option["advance_mm"],
                                     len(option["widths_mm"]), option["orientation"] != "upright"),
    )
    return {
        **result,
        "usable_width_mm": usable,
        "feed_mm": len(result["widths_mm"]) * result["advance_mm"],
        "join_overlap_mm": JOIN_OVERLAP_MM if len(result["widths_mm"]) > 1 else 0,
        "trim_profile": {
            "bleed_mm": window["bleed_mm"],
            "top_left_bevel_mm": window["bevel_left_mm"],
            "top_right_bevel_mm": window["bevel_right_mm"],
        },
    }
