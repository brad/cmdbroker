#!/bin/bash
set -euxo pipefail

poetry run mypy --ignore-missing-imports cmdbroker/
poetry run isort --check --diff cmdbroker/ tests/
poetry run black --check cmdbroker/ tests/
poetry run flake8 cmdbroker/ tests/
poetry run safety check -i 70612
poetry run bandit -r cmdbroker/
