"""Fraud detection entry points."""


def detect_fraud(transaction: dict) -> bool:
    """Return whether a transaction matches a fraud rule."""
    return any(rule(transaction) for rule in ())
