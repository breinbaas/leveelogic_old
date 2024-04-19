from leveelogic.voxel.voxel_model import VoxelModel
from leveelogic.helpers import case_insensitive_glob
from leveelogic.soilinvestigation.cpt import Cpt, CptConversionMethod
from leveelogic.soil.soilcollection import SoilCollection


class TestVoxelModel:
    def test_from_cpts(self):
        sc = SoilCollection()
        cpts = []

        for cpt_file in case_insensitive_glob(
            "./tests/testdata/cpts/voxelmodel", ".gef"
        ):
            cpts.append(Cpt.from_file(cpt_file))

        vm = VoxelModel.from_cpts(
            cpts=cpts,
            soilcolors=sc.get_color_dict(),
            cpt_conversion_method=CptConversionMethod.THREE_TYPE_RULE,
        )
        vm.plot(filename="./tests/testdata/output/voxel_plot.png")
