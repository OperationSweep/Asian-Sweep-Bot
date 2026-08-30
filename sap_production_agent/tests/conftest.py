"""Shared fixtures. The workbook is generated, never committed."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import fixture as fixture_module
from sap_agent.excel.reader import read_workbook


@pytest.fixture(scope="session")
def sample_path(tmp_path_factory) -> Path:
    return fixture_module.build(tmp_path_factory.mktemp("wb") / "ZPRO.xlsx")


@pytest.fixture(scope="session")
def book(sample_path):
    return read_workbook(sample_path)
