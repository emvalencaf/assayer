"""Tests for EvaluatorRegistry class.

This module tests the EvaluatorRegistry implementation according to the spec
requirements: registration, retrieval, validation, and state isolation.
"""

import pytest
from typing import Any

from assayer.registries.evaluator_registry import EvaluatorRegistry
from assayer.evaluators.base import BaseEvaluator
from assayer.models import FieldEvaluation


class ConcreteEvaluator(BaseEvaluator):
    """Test evaluator that properly implements the evaluate method."""

    def evaluate(self, prediction: Any, reference: Any, **kwargs: Any) -> FieldEvaluation:
        """Mock implementation of evaluate method."""
        return FieldEvaluation(
            field_name="test_field",
            evaluator_method="test_method",
            expected_value=reference,
            obtained_value=prediction,
            score=1.0,
            prompt_hash=None
        )


class AnotherEvaluator(BaseEvaluator):
    """Another test evaluator for testing multiple registrations."""

    def evaluate(self, prediction: Any, reference: Any, **kwargs: Any) -> FieldEvaluation:
        """Mock implementation of evaluate method."""
        return FieldEvaluation(
            field_name="another_field",
            evaluator_method="another_method",
            expected_value=reference,
            obtained_value=prediction,
            score=0.8,
            prompt_hash=None
        )


class NotAnEvaluator:
    """A plain class that is not a BaseEvaluator subclass."""
    pass


class TestEvaluatorRegistryRegistration:
    """Test EvaluatorRegistry.register() functionality."""

    def test_register_and_get_returns_same_class(self):
        """AC-SPEC-009: register(name, cls) stores the class; get(name) returns the same class."""
        registry = EvaluatorRegistry()

        registry.register("concrete", ConcreteEvaluator)
        retrieved_cls = registry.get("concrete")

        assert retrieved_cls is ConcreteEvaluator

    def test_register_multiple_evaluators(self):
        """Test registering multiple different evaluator classes."""
        registry = EvaluatorRegistry()

        registry.register("concrete", ConcreteEvaluator)
        registry.register("another", AnotherEvaluator)

        assert registry.get("concrete") is ConcreteEvaluator
        assert registry.get("another") is AnotherEvaluator

    def test_register_empty_name_raises_value_error(self):
        """AC-SPEC-010: register raises ValueError for empty name."""
        registry = EvaluatorRegistry()

        with pytest.raises(ValueError):
            registry.register("", ConcreteEvaluator)

    def test_register_whitespace_only_name_raises_value_error(self):
        """AC-SPEC-010: register raises ValueError for whitespace-only name."""
        registry = EvaluatorRegistry()

        with pytest.raises(ValueError):
            registry.register("   ", ConcreteEvaluator)

        with pytest.raises(ValueError):
            registry.register("\t\n  ", ConcreteEvaluator)

    def test_register_not_evaluator_subclass_raises_type_error(self):
        """AC-SPEC-010: register raises TypeError when cls is not a BaseEvaluator subclass."""
        registry = EvaluatorRegistry()

        with pytest.raises(TypeError):
            registry.register("not_evaluator", NotAnEvaluator)

    def test_register_base_evaluator_itself_raises_type_error(self):
        """AC-SPEC-010: register raises TypeError when cls is BaseEvaluator itself."""
        registry = EvaluatorRegistry()

        with pytest.raises(TypeError):
            registry.register("base_evaluator", BaseEvaluator)

    def test_register_none_as_class_raises_type_error(self):
        """Edge case: Passing None as cls raises TypeError."""
        registry = EvaluatorRegistry()

        with pytest.raises(TypeError):
            registry.register("none_evaluator", None)

    def test_register_duplicate_name_raises_key_error(self):
        """AC-SPEC-010: register raises KeyError for duplicate name."""
        registry = EvaluatorRegistry()

        registry.register("duplicate", ConcreteEvaluator)

        with pytest.raises(KeyError):
            registry.register("duplicate", AnotherEvaluator)

    def test_register_duplicate_with_same_class_raises_key_error(self):
        """Test that registering the same name twice raises KeyError even with same class."""
        registry = EvaluatorRegistry()

        registry.register("same", ConcreteEvaluator)

        with pytest.raises(KeyError):
            registry.register("same", ConcreteEvaluator)


class TestEvaluatorRegistryRetrieval:
    """Test EvaluatorRegistry.get() functionality."""

    def test_get_unregistered_name_raises_key_error(self):
        """AC-SPEC-011: get raises KeyError for an unregistered name."""
        registry = EvaluatorRegistry()

        with pytest.raises(KeyError):
            registry.get("nonexistent")

    def test_get_after_clear_registry_raises_key_error(self):
        """Test that get raises KeyError after registry becomes empty."""
        registry = EvaluatorRegistry()

        registry.register("temp", ConcreteEvaluator)
        # Reset registry by creating new one (simulating cleared state)
        registry = EvaluatorRegistry()

        with pytest.raises(KeyError):
            registry.get("temp")

    def test_get_case_sensitive_names(self):
        """Test that evaluator names are case-sensitive."""
        registry = EvaluatorRegistry()

        registry.register("CamelCase", ConcreteEvaluator)

        # Should work with exact case
        assert registry.get("CamelCase") is ConcreteEvaluator

        # Should fail with different case
        with pytest.raises(KeyError):
            registry.get("camelcase")

        with pytest.raises(KeyError):
            registry.get("CAMELCASE")


class TestEvaluatorRegistryListing:
    """Test EvaluatorRegistry.list_evaluators() functionality."""

    def test_list_evaluators_returns_sorted_names(self):
        """AC-SPEC-012: list_evaluators() returns a sorted list of registered names."""
        registry = EvaluatorRegistry()

        registry.register("zebra", ConcreteEvaluator)
        registry.register("alpha", AnotherEvaluator)
        registry.register("beta", ConcreteEvaluator)

        names = registry.list_evaluators()
        assert names == ["alpha", "beta", "zebra"]

    def test_list_evaluators_empty_registry_returns_empty_list(self):
        """Edge case: list_evaluators() on empty registry returns []."""
        registry = EvaluatorRegistry()

        names = registry.list_evaluators()
        assert names == []

    def test_list_evaluators_single_item(self):
        """Test list_evaluators with a single registered evaluator."""
        registry = EvaluatorRegistry()

        registry.register("single", ConcreteEvaluator)
        names = registry.list_evaluators()
        assert names == ["single"]

    def test_list_evaluators_returns_copy_not_reference(self):
        """Test that list_evaluators returns a new list, not internal reference."""
        registry = EvaluatorRegistry()
        registry.register("test", ConcreteEvaluator)

        names1 = registry.list_evaluators()
        names2 = registry.list_evaluators()

        # Should be equal but not the same object
        assert names1 == names2
        assert names1 is not names2

        # Modifying returned list should not affect registry
        names1.append("should_not_affect_registry")
        assert registry.list_evaluators() == ["test"]


class TestEvaluatorRegistryStateIsolation:
    """Test that independent EvaluatorRegistry instances do not share state."""

    def test_independent_registries_do_not_share_state(self):
        """AC-SPEC-014: Two independent EvaluatorRegistry instances do not share state."""
        registry1 = EvaluatorRegistry()
        registry2 = EvaluatorRegistry()

        registry1.register("evaluator1", ConcreteEvaluator)
        registry2.register("evaluator2", AnotherEvaluator)

        # Registry1 should not have evaluator2
        assert registry1.get("evaluator1") is ConcreteEvaluator
        with pytest.raises(KeyError):
            registry1.get("evaluator2")

        # Registry2 should not have evaluator1
        assert registry2.get("evaluator2") is AnotherEvaluator
        with pytest.raises(KeyError):
            registry2.get("evaluator1")

        # List operations should be independent
        assert registry1.list_evaluators() == ["evaluator1"]
        assert registry2.list_evaluators() == ["evaluator2"]

    def test_multiple_independent_registries_isolation(self):
        """Test that multiple registries remain fully isolated."""
        registries = [EvaluatorRegistry() for _ in range(3)]

        # Register different evaluators in each
        registries[0].register("reg0_eval", ConcreteEvaluator)
        registries[1].register("reg1_eval", AnotherEvaluator)
        registries[2].register("reg2_eval", ConcreteEvaluator)

        # Each should only see its own registrations
        for i, registry in enumerate(registries):
            expected_name = f"reg{i}_eval"
            assert registry.list_evaluators() == [expected_name]

            # Should not see evaluators from other registries
            for j in range(3):
                if i != j:
                    other_name = f"reg{j}_eval"
                    with pytest.raises(KeyError):
                        registry.get(other_name)

    def test_registry_modification_does_not_affect_others(self):
        """Test that modifying one registry does not affect others."""
        registry1 = EvaluatorRegistry()
        registry2 = EvaluatorRegistry()

        # Start with same evaluator in both
        registry1.register("shared_name", ConcreteEvaluator)
        registry2.register("shared_name", ConcreteEvaluator)

        # Verify both have it
        assert registry1.get("shared_name") is ConcreteEvaluator
        assert registry2.get("shared_name") is ConcreteEvaluator

        # Add different evaluator to registry1
        registry1.register("unique_to_1", AnotherEvaluator)

        # Registry2 should not be affected
        assert registry2.list_evaluators() == ["shared_name"]
        with pytest.raises(KeyError):
            registry2.get("unique_to_1")


class TestEvaluatorRegistryEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_register_very_long_name(self):
        """Test registering evaluator with very long name."""
        registry = EvaluatorRegistry()
        long_name = "a" * 1000  # Very long but valid name

        registry.register(long_name, ConcreteEvaluator)
        assert registry.get(long_name) is ConcreteEvaluator

    def test_register_name_with_special_characters(self):
        """Test registering evaluator with special characters in name."""
        registry = EvaluatorRegistry()

        special_names = [
            "eval-with-dashes",
            "eval_with_underscores",
            "eval.with.dots",
            "eval123numbers",
            "EVAL_UPPERCASE"
        ]

        for name in special_names:
            registry.register(name, ConcreteEvaluator)
            assert registry.get(name) is ConcreteEvaluator

    def test_unicode_evaluator_names(self):
        """Test registering evaluators with unicode names."""
        registry = EvaluatorRegistry()

        unicode_names = ["evaluador_español", "评估器", "оценщик"]

        for name in unicode_names:
            registry.register(name, ConcreteEvaluator)
            assert registry.get(name) is ConcreteEvaluator

        # Should be sorted properly
        sorted_names = registry.list_evaluators()
        assert len(sorted_names) == 3
        assert sorted_names == sorted(unicode_names)