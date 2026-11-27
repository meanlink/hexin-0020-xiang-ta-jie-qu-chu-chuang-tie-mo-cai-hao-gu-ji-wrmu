from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

Code = Annotated[str, StringConstraints(pattern=r"^[A-Z][A-Z0-9-]{2,23}$")]
Label = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Axis(StrEnum):
    ANY = "any"
    VERTICAL = "vertical"


class Pattern(StrEnum):
    NEUTRAL = "neutral"
    LENGTHWISE = "lengthwise"


class SheetState(StrEnum):
    DRAFT = "draft"
    ISSUED = "issued"
    CUT = "cut"
    VOID = "void"
