from pydantic import BaseModel
from typing import List, Dict
import geolib as gl
from pathlib import Path
from dotenv import load_dotenv
import os

from ..deltares.dstability import DStability


load_dotenv()
TEMP_FILES_PATH = os.getenv("TEMP_FILES_PATH")


class Runner(BaseModel):
    models: List[DStability] = []
    errors: List[str] = []
    result: List[Dict] = []

    def execute(self):
        self.result = []
        self.errors = []

        # create runner
        bm = gl.BaseModelList(models=[m.model for m in self.models])
        newbm = bm.execute(Path(TEMP_FILES_PATH), nprocesses=len(self.models))

        # save output
        self.models = []
        for model in newbm.models:
            dm = DStability(model=model)
            dm._post_process()
            self.models.append(dm)
            self.result.append(dm.safety_factor_to_dict())
