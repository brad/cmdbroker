import re

import toml

from cmdbroker import __version__ as cmdbroker_version


def get_version_from_pyproject():
    with open("pyproject.toml", "r") as file:
        pyproject_data = toml.load(file)
    return pyproject_data["tool"]["poetry"]["version"]


def get_latest_version_from_changelog():
    with open("CHANGELOG.md", "r") as file:
        content = file.read()
        match = re.search(r"^## (\d+\.\d+\.\d+) - ", content, re.MULTILINE)
        return match.group(1)


def test_version_consistency():
    pyproject_version = get_version_from_pyproject()
    changelog_version = get_latest_version_from_changelog()
    assert (
        pyproject_version == cmdbroker_version
    ), "Version mismatch between pyproject.toml and cmdbroker package"
    assert (
        changelog_version == cmdbroker_version
    ), "Version mismatch between CHANGELOG.md and cmdbroker package"
