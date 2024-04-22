from typing import List, Union, Dict, Optional
from pydantic import BaseModel
from enum import IntEnum
import threading
import subprocess
from dotenv import load_dotenv
import os
from pathlib import Path
from uuid import uuid1
import logging
from geolib.models.dstability.internal import AnalysisType

from .dstability import DStability
from .dgeoflow import DGeoFlow


class CalculationResult(BaseModel):
    error: str = ""


class DStabilityCalculationResult(CalculationResult):
    analysis_type: AnalysisType
    calculation_model_name: str = ""
    scenario_label: str = ""
    calculation_label: str = ""
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
    results: List[Union[DStabilityCalculationResult, DGeoFlowCalculationResult]] = []

    @property
    def type(self):
        if type(self.model) == DStability:
            return CalculationModelType.DSTABILITY
        elif type(self.model) == DGeoFlow:
            return CalculationModelType.DGEOFLOW
        return CalculationModelType.NONE

    def get_safety_factor(
        self, scenario_label: str, calculation_label: str
    ) -> Optional[float]:
        """Get the safery factor for the given scenario and calculation label (case insensitive)

        Args:
            scenario_label (str): The label of the scenario
            calculation_label (str): The label of the calculation

        Returns:
            Optional[float]: the safetyfactor or None if not found
        """
        if type(self.model) == DStability:
            for result in self.results:
                if (
                    result.scenario_label.lower() == scenario_label.lower()
                    and result.calculation_label.lower() == calculation_label.lower()
                ):
                    return result.safety_factor
        return None


class CalculationModelType(IntEnum):
    NONE = 0
    DSTABILITY = 1
    DGEOFLOW = 2


def calculate(exe: str, model: CalculationModel):
    try:
        subprocess.call([exe, model.filename])
    except Exception as e:
        model.results.error = f"Got a calculation error; '{e}'"
        return

    if model.type == CalculationModelType.DSTABILITY:
        try:
            ds = DStability.from_stix(model.filename)

            results = []
            for scenario_index in range(len(ds.model.scenarios)):
                for calculation_index in range(
                    len(ds.model.scenarios[scenario_index].Calculations)
                ):
                    try:
                        result = ds.model.get_result(scenario_index, calculation_index)
                        calculation_settings = ds.model._get_calculation_settings(
                            scenario_index, calculation_index
                        )

                        results.append(
                            DStabilityCalculationResult(
                                analysis_type=calculation_settings.AnalysisType.value,
                                calculation_model_name=model.name,
                                scenario_label=ds.model.scenarios[scenario_index].Label,
                                calculation_label=ds.model.scenarios[scenario_index]
                                .Calculations[calculation_index]
                                .Label,
                                safety_factor=result.FactorOfSafety,
                            )
                        )
                    except ValueError as e:
                        logging.error(f"Error creating calculation result; {e}")

            model.results = results
            return
        except Exception as e:
            model.results = DStabilityCalculationResult(
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

    def get_model_result(self, scenario_label: str, calculation_label: str):
        results = []
        if self.calculation_model_type == CalculationModelType.DSTABILITY:
            for cm in self.calculation_models:
                for result in cm.results:
                    if (
                        result.scenario_label == scenario_label
                        and result.calculation_label == calculation_label
                    ):
                        results.append(result)
            return results
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
                i = 1
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
