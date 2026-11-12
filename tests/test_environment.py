"""Environment smoke checks only; no dataset or tactics implementation."""

from pathlib import Path
import sys

import numpy as np
import pandas as pd

import basketball_tactics


def test_supported_python():
    assert sys.version_info[:2] == (3, 12)


def test_isolated_virtual_environment():
    assert sys.prefix != sys.base_prefix


def test_editable_package_import():
    project_root = Path(__file__).resolve().parents[1]
    assert Path(basketball_tactics.__file__).resolve() == (
        project_root / "src" / "basketball_tactics" / "__init__.py"
    )


def test_numpy_pandas_interoperability():
    values = np.array([1.0, 2.0, 3.0])
    frame = pd.DataFrame({"value": values})
    assert frame["value"].sum() == 6.0
