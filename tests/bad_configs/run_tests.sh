#!/bin/bash

# every one of these should fail.

../../phosphor-uikit.py bad-suffix.txt
../../phosphor-uikit.py malformed.json
../../phosphor-uikit.py not-array.json
../../phosphor-uikit.py unknown-option.json
../../phosphor-uikit.py unknown-renderer.json
../../phosphor-uikit.py float-size.json
../../phosphor-uikit.py unexpected-array.json
../../phosphor-uikit.py unexpected-dict.json
