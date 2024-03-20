from leveelogic.voxel.voxel_model import VoxelModel


class TestVoxelModel:
    def test_from_rectangle(self):
        vm = VoxelModel.from_rectangle(
            left=115297, top=480040, right=115356, bottom=479995
        )
