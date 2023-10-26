import pytest
from leveelogic.soilinvestigation.cpt import Cpt, CptReadError


class TestCptReadAndPlot:
    def test_from_gef(self, cpt_gef_files):
        for cpt_file in cpt_gef_files:
            cpt = Cpt.from_file(cpt_file)
            fig = cpt.plot(filename=f"tests/testdata/output/{cpt_file.stem}.gef.png")

    def test_from_xml(self, cpt_xml_files):
        for cpt_file in cpt_xml_files:
            cpt = Cpt.from_file(cpt_file)
            cpt.plot(filename=f"tests/testdata/output/{cpt_file.stem}.xml.png")

    def test_invalid_gef(self, cpt_gef_files_invalid):
        for cpt_file in cpt_gef_files_invalid:
            with pytest.raises(CptReadError):
                cpt = Cpt.from_file(cpt_file)

    def test_invalid_xml(self, cpt_xml_files_invalid):
        for cpt_file in cpt_xml_files_invalid:
            with pytest.raises(CptReadError):
                cpt = Cpt.from_file(cpt_file)


class TestCptFromOnlineServices:
    def test_from_bro_id(self):
        cpt = Cpt.from_bro_id("CPT000000097074")
        cpt.plot(filename=f"tests/testdata/output/bro_cpt_download.png")
