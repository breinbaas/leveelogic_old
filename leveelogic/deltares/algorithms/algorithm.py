from pydantic import BaseModel
from typing import List, Dict
import abc
from ..dstability import DStability

from ...geometry.characteristic_point import CharacteristicPoint


class AlgorithmExecutionError(Exception):
    """This exception is raised if an error occured during execution"""

    pass


class Algorithm(BaseModel, metaclass=abc.ABCMeta):
    """Base class for all algorithms

    You will need to implement the abstract _execute function
    """

    ds: DStability

    def execute(self):
        try:
            self._check_input()
        except Exception as e:
            raise AlgorithmExecutionError(
                f"Could not execute algorithm, got error '{e}'"
            )

        return self._execute()

    @abc.abstractmethod
    def _check_input(self):
        raise NotImplementedError

    @abc.abstractmethod
    def _execute(self) -> DStability:
        raise NotImplementedError
