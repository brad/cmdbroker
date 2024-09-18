#!/bin/bash
set -euxo pipefail

./scripts/lint.sh
poetry run pytest -s --cov=cmdbroker/ --cov-fail-under=100 --cov=tests --cov-report=term-missing ${@-} --cov-branch --cov-report html
