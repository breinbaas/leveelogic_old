from typing import List, Union, Dict
from pydantic import BaseModel
from enum import IntEnum
import threading
import subprocess
from dotenv import load_dotenv
import os
from pathlib import Path
from uuid import uuid1
import logging

from .dstability import DStability
from .dgeoflow import DGeoFlow


class CalculationResult(BaseModel):
    error: str = ""


class DStabilityCalculationResult(CalculationResult):
    safety_factor: float = 0.0


class DGeoFlowCalculationResult(CalculationResult):
    pass


class CalculationModelType(IntEnum):
    NONE = 0
    DSTABILITY = 1
    DGEOFLOW = 2


class CalculationModel(BaseModel):
    model: Union[DStability, DGeoFlow]
    name: str
    filename: str = ""
    result: Union[DStabilityCalculationResult, DGeoFlowCalculationResult] = None

    @property
    def type(self):
        if type(self.model) == DStability:
            return CalculationModelType.DSTABILITY
        elif type(self.model) == DGeoFlow:
            return CalculationModelType.DGEOFLOW
        return CalculationModelType.NONE


class CalculationModelType(IntEnum):
    NONE = 0
    DSTABILITY = 1
    DGEOFLOW = 2


def calculate(exe: str, model: CalculationModel):
    try:
        subprocess.call([exe, model.filename])
    except Exception as e:
        model.result.error = f"Got a calculation error; '{e}'"
        return

    if model.type == CalculationModelType.DSTABILITY:
        try:
            ds = DStability.from_stix(model.filename)
            model.result = DStabilityCalculationResult(
                safety_factor=ds.model.output[0].FactorOfSafety
            )
            return
        except Exception as e:
            model.result = DStabilityCalculationResult(
                error=f"Got calculation result error '{e}'"
            )
    elif model.type == CalculationModelType.DGEOFLOW:
        raise NotImplementedError()


class DSeriesCalculator(BaseModel):
    calculation_model_type: CalculationModelType = CalculationModelType.NONE
    calculation_models: List[CalculationModel] = []
    logfile: Union[Path, str] = None

    def export_files(self, output_path: Union[Path, str]):
        for cm in self.calculation_models:
            if self.calculation_model_type == CalculationModelType.DSTABILITY:
                cm.model.serialize(Path(output_path) / f"{cm.name}.stix")
            elif self.calculation_model_type == CalculationModelType.DGEOFLOW:
                cm.model.serialize(Path(output_path) / f"{cm.name}.flox")

    def clear(self, unset_logfile=False):
        self.calculation_model_type = CalculationModelType.NONE
        self.calculation_models = []
        if unset_logfile:
            self.logfile = None

    def get_model_by_name(self, model_name: str):
        for cm in self.calculation_models:
            if cm.name == model_name:
                return cm
        raise ValueError(f"No model with name '{model_name}'")

    def get_model_result_dict(self):
        if self.calculation_model_type == CalculationModelType.DSTABILITY:
            return {
                cm.name: cm.result.safety_factor
                for cm in self.calculation_models
                if cm.result.safety_factor is not None
            }
        elif self.calculation_model_type == CalculationModelType.DGEOFLOW:
            raise NotImplementedError()
        else:
            raise ValueError("Unknown calculation model type encountered")

    def add_models(self, models: List[Union[DStability, DGeoFlow]], names: List[str]):
        if len(models) != len(names):
            raise ValueError(
                f"Got {len(models)} model(s) and {len(names)} name(s), this should be the same amount"
            )
        for i in range(len(models)):
            self.add_model(models[i], names[i])

    def add_model(self, model: Union[DStability, DGeoFlow], name: str):
        # adding the first model (the model type is NONE) which also defines which type of calculator this will be
        if self.calculation_model_type == CalculationModelType.NONE:
            if type(model) == DStability:
                self.calculation_model_type = CalculationModelType.DSTABILITY
            elif type(model) == DGeoFlow:
                self.calculation_model_type = CalculationModelType.DGEOFLOW
            else:
                raise ValueError(f"Got an invalid model type '{type(model)}'")
            self.calculation_models.append(CalculationModel(model=model, name=name))
        else:  # the next models should be of the same type as the first model
            if (
                type(model) == DStability
                and self.calculation_model_type == CalculationModelType.DSTABILITY
            ):
                self.calculation_models.append(CalculationModel(model=model, name=name))
            elif (
                type(model) == DGeoFlow
                and self.calculation_model_type == CalculationModelType.DGEOFLOW
            ):
                self.calculation_models.append(CalculationModel(model=model, name=name))
            else:
                raise ValueError(
                    f"Adding an incompatible model '{type(model)}' to this calculator"
                )

    def calculate(self):
        if self.logfile is not None:
            logging.basicConfig(
                filename=str(self.logfile),
                filemode="w",
                format="%(asctime)s %(levelname)s %(message)s",
                datefmt="%H:%M:%S",
                level=logging.INFO,
            )

        try:
            load_dotenv("leveelogic.env")

            DSTABILITY_CONSOLE_EXE = os.getenv("DSTABILITY_CONSOLE_EXE")
            DGEOFLOW_CONSOLE_EXE = os.getenv("DGEOFLOW_CONSOLE_EXE")
            CALCULATIONS_FOLDER = os.getenv("CALCULATIONS_FOLDER")

            assert Path(DSTABILITY_CONSOLE_EXE).exists()
            assert Path(DGEOFLOW_CONSOLE_EXE).exists()
            assert Path(CALCULATIONS_FOLDER).exists()
        except Exception as e:
            raise ValueError(f"Error setting up calculation environment, '{e}'")

        threads = []
        for calculation_model in self.calculation_models:
            calculation_model.filename = str(
                Path(CALCULATIONS_FOLDER) / f"{str(uuid1())}.stix"
            )
            calculation_model.model.serialize(calculation_model.filename)
            if calculation_model.type == CalculationModelType.DSTABILITY:
                threads.append(
                    threading.Thread(
                        target=calculate,
                        args=[DSTABILITY_CONSOLE_EXE, calculation_model],
                    )
                )
            elif calculation_model.type == CalculationModelType.DGEOFLOW:
                raise NotImplementedError()
                threads.append(
                    threading.Thread(
                        target=calculate, args=[DGEOFLOW_CONSOLE_EXE, calculation_model]
                    )
                )
            else:
                raise NotImplementedError(
                    f"Encountered unsupported model '{type(calculation_model)}'"
                )

            if self.logfile is not None:
                logging.info(
                    f"Added model '{calculation_model.name}' to the calculations as file '{calculation_model.filename}'"
                )

        logging.info(f"Starting {len(threads)} calculation(s)")
        for t in threads:
            t.start()

        for t in threads:
            t.join()
        logging.info(f"Finished {len(threads)} calculation(s)")
