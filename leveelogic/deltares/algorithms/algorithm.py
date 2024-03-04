from pydantic import BaseModel
from typing import List
import abc
from ..dstability import DStability


class AlgorithmExecutionError(Exception):
    pass


class AlgorithmInputCheckError(Exception):
    pass


class Algorithm(BaseModel, metaclass=abc.ABCMeta):
    """Base class for all algorithms

    You will need to implement the abstract _execute function
    """

    ds: DStability
    log: List[str] = []

    def execute(self) -> DStability:
        try:
            self._check_input()
        except Exception as e:
            raise AlgorithmInputCheckError(
                f"Could not execute algorithm, got error '{e}'"
            )

        ds = self._execute()
        ds._post_process()

        return ds

    def execute_multiple_results(self) -> List[DStability]:
        try:
            self._check_input()
        except Exception as e:
            raise AlgorithmExecutionError(
                f"Could not execute algorithm, got error '{e}'"
            )

        return self._execute_multiple_results()

    @abc.abstractmethod
    def _check_input(self):
        raise NotImplementedError

    def _execute(self) -> DStability:
        raise NotImplementedError

    def _execute_multiple_results(self) -> List[DStability]:
        raise NotImplementedError
