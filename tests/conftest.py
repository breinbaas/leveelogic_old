import pytest
from typing import List, Dict
from pathlib import Path

from leveelogic.helpers import case_insensitive_glob


@pytest.fixture
def cpt_gef_files() -> List[Path]:
    """
    This creates a dictionary with cpt test files saved with the filename
    (without extentsion) as key and the data (str) as value

    You can use the filename to add more testdata like expected interpretations
    """
    return case_insensitive_glob("tests/testdata/cpts", ".gef")


@pytest.fixture
def cpt_xml_files() -> List[Path]:
    """
    This creates a dictionary with cpt test files saved with the filename
    (without extentsion) as key and the data (str) as value

    You can use the filename to add more testdata like expected interpretations
    """
    return case_insensitive_glob("tests/testdata/cpts", ".xml")


@pytest.fixture
def cpt_gef_strings() -> List[Dict]:
    """
    This creates a dictionary with cpt test files saved with the filename
    (without extentsion) as key and the data (str) as value

    You can use the filename to add more testdata like expected interpretations
    """
    cpt_strings = {}
    for f in case_insensitive_glob("tests/testdata/cpts", ".gef"):
        p = Path(f).stem
        cpt_strings[p] = open(f, "r").read()
    return cpt_strings


@pytest.fixture
def cpt_xml_strings() -> List[Dict]:
    """
    This creates a dictionary with cpt test files saved with the filename
    (without extentsion) as key and the data (str) as value

    You can use the filename to add more testdata like expected interpretations
    """
    cpt_strings = {}
    for f in case_insensitive_glob("tests/testdata/cpts", ".xml"):
        p = Path(f).stem
        cpt_strings[p] = open(f, "r").read()
    return cpt_strings
