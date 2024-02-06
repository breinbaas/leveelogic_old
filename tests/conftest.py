import pytest
from typing import List, Dict
from pathlib import Path

from leveelogic.helpers import case_insensitive_glob
from leveelogic.soilinvestigation.cpt import Cpt, CptConversionMethod
from leveelogic.geometry.soilprofileN import SoilProfileN


@pytest.fixture
def cpt_gef_files() -> List[Path]:
    """Get all valid cpt gef files

    Returns:
        List[Path]: A list with all file paths to valid gef cpt files
    """
    return [
        f
        for f in case_insensitive_glob("tests/testdata/cpts", ".gef")
        if not f.stem.find("invalid") > -1
    ]


@pytest.fixture
def cpt_gef_files_invalid() -> List[Path]:
    """Get all invalid cpt gef files

    Returns:
        List[Path]: A list with all file paths to invalid gef cpt files
    """
    return [
        f
        for f in case_insensitive_glob("tests/testdata/cpts", ".gef")
        if not f.stem.find("invalid") == -1
    ]


@pytest.fixture
def cpt_xml_files() -> List[Path]:
    """Get all valid cpt xml files

    Returns:
        List[Path]: A list with all file paths to valid xml cpt files
    """
    return [
        f
        for f in case_insensitive_glob("tests/testdata/cpts", ".xml")
        if not f.stem.find("invalid") > -1
    ]


@pytest.fixture
def cpt_xml_files_invalid() -> List[Path]:
    """Get all invalid cpt xml files

    Returns:
        List[Path]: A list with all file paths to invalid xml cpt files
    """
    return [
        f
        for f in case_insensitive_glob("tests/testdata/cpts", ".xml")
        if not f.stem.find("invalid") == -1
    ]


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


@pytest.fixture
def cpt_soilprofileN() -> SoilProfileN:
    cpt_left = Cpt.from_file("tests/testdata/cpts/01.gef")
    cpt_right = Cpt.from_file("tests/testdata/cpts/02.gef")

    spN = SoilProfileN()
    spN.append(
        cpt_left.to_soilprofile1(
            cptconversionmethod=CptConversionMethod.ROBERTSON,
            minimum_layerheight=0.5,
            peat_friction_ratio=6.0,
            left=0,
            right=20,
        )
    )
    spN.append(
        cpt_right.to_soilprofile1(
            cptconversionmethod=CptConversionMethod.ROBERTSON,
            minimum_layerheight=0.5,
            peat_friction_ratio=6.0,
            left=20,
            right=50,
        ),
        fill_material_bottom="bottom_material",
        fill_material_top="top_material",
    )
    return spN
