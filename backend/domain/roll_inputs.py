from typing import Annotated

from pydantic import Field, model_validator

from domain.vocabulary import Code, Input, Pattern


class AddRoll(Input):
    code: Code
    finish_code: Code
    width_mm: Annotated[int, Field(ge=250, le=3500)]
    edge_damage_mm: Annotated[int, Field(ge=0, le=150)]
    pattern: Pattern
    thickness_um: Annotated[int, Field(ge=30, le=300)]
    initial_length_mm: Annotated[int, Field(ge=500, le=200000)]

    @model_validator(mode="after")
    def web_is_usable(self):
        if self.width_mm - 2 * self.edge_damage_mm < 180:
            raise ValueError("edge damage leaves less than 180 mm of usable web")
        return self
