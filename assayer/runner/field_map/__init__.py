"""The map from output Fields (dotted paths) to the metrics that score them."""

from assayer.alignment import Alignment
from assayer.path import resolve

from .builder import build_field_map, metrics_of
from .field_metric import FieldMetric
from .list_field import ALIGNMENTS, Align, ListField, ListSpec
from .loader import FieldMapError, load_field_map, parse_field_map
from .schema import FieldMapDraft, schema_to_field_map
from .scoring import score_experiment_field, score_field

__all__ = [
    "ALIGNMENTS",
    "Align",
    "Alignment",
    "FieldMapDraft",
    "FieldMapError",
    "FieldMetric",
    "ListField",
    "ListSpec",
    "build_field_map",
    "load_field_map",
    "metrics_of",
    "parse_field_map",
    "resolve",
    "schema_to_field_map",
    "score_experiment_field",
    "score_field",
]
