"""
substrate/dims.py

The field's width, in one place. Every field-dim site (CONFIG["dim"], every
constructor default, the speech bridge's projection) reads FIELD_DIM, so
widening the field (128 -> 256/768, docs/WIDENING_PLAN.md) is one edit here.
tests/doc_accuracy/hardcoded_dim.py fails on any field-dim literal elsewhere.

Changing this is a new body: checkpoints saved at another width will not load
into the field (the loaders skip a shape mismatch rather than corrupt state).
"""

FIELD_DIM = 128
