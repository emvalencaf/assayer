"""Tests for the Score model."""

import pytest

from assayer.models import Score


class TestScore:
    @pytest.mark.parametrize("value", [-0.01, 1.01])
    def test_value_outside_unit_range_is_rejected(self, value):
        with pytest.raises(ValueError):
            Score(name="m", value=value)

    @pytest.mark.parametrize("value", [0.0, 0.5, 1.0])
    def test_value_inside_unit_range_is_accepted(self, value):
        assert Score(name="m", value=value).value == value

    def test_booleans_map_to_zero_and_one(self):
        assert Score(name="m", value=True).value == 1.0
        assert Score(name="m", value=False).value == 0.0

    def test_optional_fields_and_target(self):
        score = Score(
            name="m",
            value=1,
            field="amount",
            label="ok",
            comment="c",
            metadata={"a": 1},
            target="step",
            target_id="s1",
        )

        assert (score.field, score.label, score.comment) == ("amount", "ok", "c")
        assert (score.metadata, score.target, score.target_id) == ({"a": 1}, "step", "s1")

    def test_target_defaults_to_trajectory(self):
        assert Score(name="m", value=1).target == "trajectory"

    def test_unknown_target_is_rejected(self):
        with pytest.raises(ValueError):
            Score(name="m", value=1, target="span")
