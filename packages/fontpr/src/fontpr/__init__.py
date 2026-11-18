# this_file: packages/fontpr/src/fontpr/__init__.py
"""Explain why the native fontpr module is unavailable outside FontLab."""

raise ImportError(
    "fontpr is a native module available only inside FontLab's embedded Python. "
    "Run your script in FontLab, or install 'fontlab' for external automation. "
    "This PyPI distribution is an explanatory stub, not the native module."
)
