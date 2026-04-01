"""Mock bert_score module for testing purposes."""

def score(predictions, references, lang="en", rescale_with_baseline=True):
    """Mock implementation of bert_score.score function.

    This is a minimal implementation to allow tests to run.
    The actual implementation will be mocked in tests.
    """
    # This should not be called in actual tests since they mock this function
    raise ImportError("bert_score library not available")