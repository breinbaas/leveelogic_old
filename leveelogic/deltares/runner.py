from pydantic import BaseModel
from typing import List, Dict
import geolib as gl
from pathlib import Path
from dotenv import load_dotenv
import os

from ..deltares.dstability import DStability


load_dotenv()
TEMP_FILES_PATH = os.getenv("TEMP_FILES_PATH")


class RunnerResult(BaseModel):
    model: DStability
    # errors: List[str] = []
    fos: float


class Runner(BaseModel):
    models: List[DStability] = []

    def execute(self):
        result = []

        # create runner
        bml = gl.BaseModelList(models=[])
        meta = []
        for i in range(len(self.models)):
            bml.models.append(self.models[i].model)
            meta.append(self.models[i].name)

        newbm = bml.execute(Path(TEMP_FILES_PATH), nprocesses=len(self.models))

        # save output
        for i, model in enumerate(newbm.models):
            dm = DStability(model=model)
            dm._post_process()
            dm.name = meta[i]
            fos_dict = dm.safety_factor_to_dict()

            if fos_dict != {}:
                result.append(RunnerResult(model=dm, fos=fos_dict["fos"]))

        return result
