# this_file: packages/fontgate/src/fontgate/__init__.py
"""Explain why the native fontgate module is unavailable outside FontLab."""

raise ImportError(
    "fontgate is a native module available only inside FontLab's embedded Python. "
    "Run your script in FontLab, or install 'fontlab' for external automation. "
    "This PyPI distribution is an explanatory stub, not the native module."
)
