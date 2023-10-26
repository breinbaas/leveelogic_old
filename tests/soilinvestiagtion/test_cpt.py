from leveelogic.soilinvestigation.cpt import Cpt


class TestCptPlot:
    def test_cpt_from_gef(self, cpt_gef_files):
        for cpt_file in cpt_gef_files:
            cpt = Cpt.from_file(cpt_file)
            fig = cpt.plot(filename=f"tests/testdata/output/{cpt_file.stem}.gef.png")

    def test_cpt_from_xml(self, cpt_xml_files):
        for cpt_file in cpt_xml_files:
            cpt = Cpt.from_file(cpt_file)
            cpt.plot(filename=f"tests/testdata/output/{cpt_file.stem}.xml.png")
