import pytest

from leveelogic.calculations.functions import *
from leveelogic.geolib.models.dstability.internal import AnalysisTypeEnum
import pytest


class TestFunctions:
    def test_sf_to_beta(self):
        a = sf_to_beta(1.21, 1.07)
        assert sf_to_beta(1.21, 1.07) == pytest.approx(4.805607, 1e-5)

    def test_beta_to_pf(self):
        assert beta_to_pf(4.805607) == pytest.approx(7.71e-7, 0.001)

    def test_pf_to_beta(self):
        assert pf_to_beta(7.71e-7) == pytest.approx(4.806, 0.001)

    def test_get_model_factor(self):
        assert get_model_factor(AnalysisTypeEnum.BISHOP) == 1.11
        assert get_model_factor(AnalysisTypeEnum.BISHOP_BRUTE_FORCE) == 1.11
        assert get_model_factor(AnalysisTypeEnum.SPENCER) == 1.07
        assert get_model_factor(AnalysisTypeEnum.SPENCER_GENETIC) == 1.07
        assert get_model_factor(AnalysisTypeEnum.UPLIFT_VAN) == 1.06
        assert get_model_factor(AnalysisTypeEnum.UPLIFT_VAN_PARTICLE_SWARM) == 1.06
        with pytest.raises(ValueError):
            get_model_factor(-1) == 1.12
