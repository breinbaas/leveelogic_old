import pytest

from leveelogic.soilinvestigation.cpt import Cpt, CptReadError, CptConversionMethod


class TestCptFromString:
    def test_from_gef_string(self, cpt_gef_files):
        for cpt_file in cpt_gef_files:
            s = open(cpt_file, "r").read()
            cpt_c = Cpt.from_file(cpt_file)
            cpt = Cpt.from_string(s, suffix=".gef")
            assert cpt_c == cpt

    def test_from_xml_string(self, cpt_xml_files):
        for cpt_file in cpt_xml_files:
            s = open(cpt_file, "r").read()
            cpt_c = Cpt.from_file(cpt_file)
            cpt = Cpt.from_string(s, suffix=".xml")
            assert cpt_c == cpt


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

    def test_Ic_plot(self):
        cpt = Cpt.from_file("tests/testdata/cpts/bro_cpt.gef")
        cpt.plot_Ic("tests/testdata/output/cpt_Ic_plot.png")


class TestCptTools:
    def test_cut(self):
        cpt = Cpt.from_file("tests/testdata/cpts/bro_cpt.gef")
        assert cpt.length == 16.17
        assert cpt.top == 1.75
        assert cpt.bottom == -14.42

        cpt_cut_bottom = cpt.cut(10, -5)
        assert cpt_cut_bottom.top == pytest.approx(cpt.top)
        assert cpt_cut_bottom.bottom == -5.0

        cpt_cut_top = cpt.cut(-5.0, -99)
        assert cpt_cut_top.top == -5.0
        assert cpt_cut_top.bottom == pytest.approx(cpt.bottom)

    def test_as_numpy(self):
        cpt = Cpt.from_file("tests/testdata/cpts/bro_cpt.gef")
        M = cpt.as_numpy()
        assert M.shape == (len(cpt.z), 5)
        assert M[-1][0] == cpt.z[-1]
        assert M[-1][1] == cpt.qc[-1]
        assert M[-1][2] == cpt.fs[-1]
        assert M[-1][3] == cpt.fr[-1]
        assert M[-1][4] == cpt.u[-1]

    def test_as_pandas(self):
        cpt = Cpt.from_file("tests/testdata/cpts/bro_cpt.gef")
        df = cpt.as_dataframe()
        assert df.shape == (len(cpt.z), 5)
        assert df["z"].iloc[-1] == cpt.z[-1]
        assert df["qc"].iloc[-1] == cpt.qc[-1]
        assert df["fs"].iloc[-1] == cpt.fs[-1]
        assert df["fr"].iloc[-1] == cpt.fr[-1]
        assert df["u"].iloc[-1] == cpt.u[-1]

    def test_to_z_Ic_list(self):
        cpt = Cpt.from_file("tests/testdata/cpts/bro_cpt.gef")
        M = cpt.to_z_Ic_list()
        assert M.shape == (len(cpt.z), 2)


class TestCptFromOnlineServices:
    def test_from_bro_id(self):
        cpt = Cpt.from_bro_id("CPT000000097074")
        cpt.plot(filename=f"tests/testdata/output/bro_cpt_download.png")


class TestCptClassification:
    def test_nen(self):
        cpt = Cpt.from_file("tests/testdata/cpts/bro_cpt.gef")
        cpt.plot(
            "tests/testdata/output/cpt_nen_classification.png",
            cptconversionmethod=CptConversionMethod.NL_RF,
        )
        cpt.plot(
            "tests/testdata/output/cpt_nen_classification_1m.png",
            cptconversionmethod=CptConversionMethod.NL_RF,
            minimum_layerheight=1.0,
        )

    def test_three_type_rule(self):
        cpt = Cpt.from_file("tests/testdata/cpts/bro_cpt.gef")
        cpt.plot(
            "tests/testdata/output/cpt_3tr_classification.png",
            cptconversionmethod=CptConversionMethod.THREE_TYPE_RULE,
        )
        cpt.plot(
            "tests/testdata/output/cpt_3tr_classification_1m.png",
            cptconversionmethod=CptConversionMethod.THREE_TYPE_RULE,
            minimum_layerheight=1.0,
        )

    def test_robertson(self):
        cpt = Cpt.from_file("tests/testdata/cpts/bro_cpt.gef")
        cpt.plot(
            "tests/testdata/output/cpt_robertson_classification.png",
            cptconversionmethod=CptConversionMethod.ROBERTSON,
        )
        cpt.plot(
            "tests/testdata/output/cpt_robertson_classification_1m.png",
            cptconversionmethod=CptConversionMethod.ROBERTSON,
            minimum_layerheight=1.0,
        )

    def test_robertson_with_peat(self):
        cpt = Cpt.from_file("tests/testdata/cpts/bro_cpt.gef")
        cpt.plot(
            "tests/testdata/output/cpt_robertson_with_peat_classification.png",
            cptconversionmethod=CptConversionMethod.ROBERTSON,
            peat_friction_ratio=4.0,
        )
        cpt.plot(
            "tests/testdata/output/cpt_robertson_with_peat_classification_1m.png",
            cptconversionmethod=CptConversionMethod.ROBERTSON,
            minimum_layerheight=1.0,
            peat_friction_ratio=4.0,
        )
