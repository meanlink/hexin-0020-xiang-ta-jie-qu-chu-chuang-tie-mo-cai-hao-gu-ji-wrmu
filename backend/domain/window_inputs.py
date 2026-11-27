from typing import Annotated

from pydantic import Field, model_validator

from domain.vocabulary import Axis, Code, Input, Label


class WindowGeometry(Input):
    exhibit: Label
    finish_code: Code
    width_mm: Annotated[int, Field(ge=250, le=5000)]
    height_mm: Annotated[int, Field(ge=250, le=5000)]
    bevel_left_mm: Annotated[int, Field(ge=0, le=400)]
    bevel_right_mm: Annotated[int, Field(ge=0, le=400)]
    bleed_mm: Annotated[int, Field(ge=5, le=80)]
    pattern_axis: Axis
    allow_seam: bool

    @model_validator(mode="after")
    def pass_corner_checks(self):
        if self.width_mm - self.bevel_left_mm - self.bevel_right_mm < 120:
            raise ValueError("top glazing edge after both chamfers must be at least 120 mm")
        if self.height_mm <= max(self.bevel_left_mm, self.bevel_right_mm):
            raise ValueError("top chamfer cannot span the window height")
        return self


class NewWindow(WindowGeometry):
    code: Code


class ReviseWindow(WindowGeometry):
    expected_revision: Annotated[int, Field(ge=1)]
