from dataclasses import dataclass, field

from assayer.models.case import Case


@dataclass
class Dataset:
    """A named collection of Cases.

    Args:
        name: Name of the Dataset.
        cases: The Cases. Defaults to empty list.
    """

    name: str
    cases: list[Case] = field(default_factory=list)
