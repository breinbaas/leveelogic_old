from typing import List, Dict
from pydantic import BaseModel
import numpy as np
from math import ceil, floor, hypot
import matplotlib.pyplot as plt

from ..soilinvestigation.cpt import Cpt, CptConversionMethod


class VoxelModel(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    M: np.ndarray = None
    soilcolors: Dict = {}
    soils: Dict = {}

    @classmethod
    def from_cpts(
        self,
        cpts: List[Cpt],
        soilcolors: Dict,
        cpt_conversion_method: CptConversionMethod.THREE_TYPE_RULE,
        size_x: float = 5.0,
        size_y: float = 5.0,
        size_z: float = 1.0,
        xy_margin: float = 0.0,
        max_cpt_distance: float = 100.0,
    ) -> "VoxelModel":
        vm = VoxelModel()
        # get the dimensions
        xs = [cpt.x for cpt in cpts]
        ys = [cpt.y for cpt in cpts]
        zs = [cpt.top for cpt in cpts]
        zs += [cpt.bottom for cpt in cpts]

        # get the limits
        xleft = min(xs) - xy_margin
        xright = max(xs) + xy_margin
        ytop = max(ys) + xy_margin
        ybottom = min(ys) - xy_margin
        ztop = max(zs)
        zbottom = min(zs)

        # round x to nearest size_x
        xleft = floor(xleft / size_x) * size_x
        xright = ceil(xright / size_x) * size_x

        # round y to nearest size_y
        ybottom = floor(ybottom / size_y) * size_y
        ytop = ceil(ytop / size_y) * size_y

        # round z top nearest size_z
        ztop = ceil(ztop / size_z) * size_z
        zbottom = floor(zbottom / size_z) * size_z

        # create the matrix
        num_x = ceil((xright - xleft) / size_x)
        num_y = ceil((ytop - ybottom) / size_y)
        num_z = ceil((ztop - zbottom) / size_z)
        vm.M = np.zeros((num_x, num_y, num_z))

        # convert the cpts to a 1D matrix
        vm.soils = {}
        cpt_vectors = []
        empty_vector = np.zeros(num_z)
        for i, cpt in enumerate(cpts):
            cpt_data = {"x": cpt.x, "y": cpt.y, "vector": []}
            s1d = cpt.to_soilprofile1(
                cptconversionmethod=CptConversionMethod.THREE_TYPE_RULE,
                minimum_layerheight=size_z,
            )
            soil_vector = []
            for j in range(num_z):
                soilcode = s1d.soilcode_at(ztop - (j + 0.5) * size_z)

                if soilcode is None:
                    soil_vector.append(0)
                else:
                    if not soilcode in vm.soils.keys():
                        try:
                            soilcolor = soilcolors[soilcode]
                        except Exception as e:
                            raise ValueError(
                                f"Missing soilcolor for soilcode '{soilcode}'"
                            )
                        vm.soils[soilcode] = len(vm.soils.keys()) + 1
                        vm.soilcolors[soilcode] = soilcolor
                    soil_vector.append(vm.soils[soilcode])
            cpt_data["vector"] = soil_vector[::-1]  # reverse the z order
            cpt_vectors.append(cpt_data)

        # fill the matrix
        for i in range(num_x):
            for j in range(num_y):
                xm = xleft + (i - 0.5) * size_x
                ym = ytop - (j - 0.5) * size_y
                closest_cpt, closest_dx = None, 1e9
                for cpt_data in cpt_vectors:
                    cpt_x = cpt_data["x"]
                    cpt_y = cpt_data["y"]
                    dx = hypot(cpt_x - xm, cpt_y - ym)
                    if dx <= max_cpt_distance:
                        if dx < closest_dx:
                            closest_cpt = cpt_data["vector"]
                            closest_dx = dx
                if closest_cpt is not None:
                    vm.M[i, j] = closest_cpt
                else:
                    vm.M[i, j] = empty_vector

        # create the final soil color dictionary based on the index
        vm.soilcolors = {vm.soils[v]: k for v, k in vm.soilcolors.items()}
        # invert the soils dictionary
        vm.soils = {v: k for k, v in vm.soils.items()}

        return vm

    def plot(
        self,
        filename: str = "",
        size_x: float = 10,
        size_y: float = 12,
        alpha: str = "C0",
    ):
        fig = plt.Figure(figsize=(size_x, size_y))
        ax = fig.add_subplot(projection="3d")

        # = plt.figure().add_subplot()
        for id, color in self.soilcolors.items():
            v = self.M == id
            ax.voxels(v, facecolors=color + alpha, edgecolor="k")

        ax.set_aspect("equalxy")
        if filename == "":
            return fig
        else:
            fig.savefig(filename)

    # def export(self):
