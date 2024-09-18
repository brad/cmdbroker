#!/bin/bash
set -euxo pipefail

poetry run isort cmdbroker/ tests/
poetry run black cmdbroker/ tests/
