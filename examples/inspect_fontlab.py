# this_file: examples/inspect_fontlab.py
"""External Python example; requires a functioning native FontLab MCP bridge."""

import fontlab

with fontlab.connect() as app:
    print(app.fonts())
