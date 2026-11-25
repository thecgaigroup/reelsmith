"""Shared opt-in parsing without importing the finish pipeline."""
import os


def enabled():
    return os.environ.get("REELSMITH_FINISH_PASS", "").lower() in {"1", "true", "on", "yes"}
