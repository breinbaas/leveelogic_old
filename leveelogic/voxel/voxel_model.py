from pydantic import BaseModel, Field
from typing import List, Tuple
import numpy as np
from math import hypot

from ..api.bro_api import BROAPI
from ..soilinvestigation.cpt import Cpt, CptConversionMethod
from ..soil.soilcollection import SoilCollection


class CptVoxel(BaseModel):

    class Config:
        arbitrary_types_allowed = True

    id: str
    soils: np.ndarray = Field(default_factory=lambda: np.zeros(1))


class VoxelModel(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    xy_matrix: np.ndarray = Field(default_factory=lambda: np.zeros(1))
    z_matrix: List[np.ndarray] = []

    @classmethod
    def from_rectangle(
        cls,
        left: int,
        top: int,
        right: int,
        bottom: int,
        size_xy: float = 10.0,
        size_z: float = 1.0,
        max_distance=20.0,
    ) -> "VoxelModel":
        result = VoxelModel()

        # generate cpt matrix
        num_x = int((right - left) / size_xy) + 1
        num_y = int((top - bottom) / size_xy) + 1
        result.xy_matrix = np.zeros((num_y, num_x), dtype=int)

        api = BROAPI()

        _, cpts = api.get_cpts_by_bounds_rd(
            left=left,
            right=right,
            top=top,
            bottom=bottom,
            max_num=2,
        )

        if len(cpts) == 0:
            return VoxelModel()

        # determine the size of the z direction
        zs = [cpt.top for cpt in cpts] + [cpt.bottom for cpt in cpts]
        zmin = min(zs)
        zmax = max(zs)
        num_z = int((zmax - zmin) / size_z) + 1

        # create a dictionary with soil names -> id (int)
        soilcollection = SoilCollection()
        soil_ids = {}
        for i, soil in enumerate(soilcollection.soils):
            soil_ids[soil.code] = i

        cpt_dict = {}
        for i, cpt in enumerate(cpts):
            cpt_voxel = CptVoxel(id=i + 1)
            cpt_dict[cpt.name] = i + 1
            cpt_voxel.soils = np.ndarray((num_z), dtype=int)

            sp1 = cpt.to_soilprofile1(
                cptconversionmethod=CptConversionMethod.ROBERTSON,
                minimum_layerheight=0.5,
                peat_friction_ratio=5.0,
            )
            for j in range(num_z):
                z = zmax - (j + 0.5) * size_z
                soilcode = sp1.soilcode_at(z)
                if soilcode is None:
                    cpt_voxel.soils[j] = 0
                else:
                    cpt_voxel.soils[j] = soil_ids[soilcode]
            
            result.z_matrix.append(cpt_voxel)

        for r in range(num_y):
            y = top - (r + 0.5) * size_xy
            for c in range(num_x):
                x = left + (c + 0.5) * size_xy
                dlmin, cpt_id = 1e9, None
                for cpt in cpts:
                    dl = hypot(x - cpt.x, y - cpt.y)
                    if dl < dlmin:
                        dlmin = dl
                        cpt_id = cpt_dict[cpt.name]

                if dlmin <= max_distance:
                    result.xy_matrix[r, c] = cpt_id
                else:
                    result.xy_matrix[r, c] = 0

        return result
