from typing import Annotated

from pydantic import Field, StringConstraints

from domain.vocabulary import Code, Input


class NewEstimate(Input):
    window_code: Code
    window_revision: Annotated[int, Field(ge=1)]
    roll_code: Code


class CompleteCut(Input):
    used_mm: Annotated[int, Field(ge=1, le=200000)]


class VoidCut(Input):
    reason: Annotated[str, StringConstraints(strip_whitespace=True, min_length=5, max_length=240)]
