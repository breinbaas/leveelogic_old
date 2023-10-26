import simplejson as json
from pydantic import BaseModel
from pathlib import Path


class DataModel(BaseModel):
    """ "Base class for all json serializable objects"""

    def to_json(self, indent: int = 4):
        """Convert to json string"""
        if indent != 0:
            return json.dumps(self.dict(), indent=indent)
        else:
            return json.dumps(self.dict())

    @classmethod
    def from_json(cls, json_str) -> "DataModel":
        """Generate class from json string"""
        return cls(**json.loads(json_str))

    @classmethod
    def parse(cls, filename: str) -> "DataModel":
        json_str = open(filename, "r").read()
        return cls(**json.loads(json_str))

    def serialize(self, filepath: str, filename: str) -> str:
        """Write to file

        Args:
            filepath (str): path to the file
            filename (str): filename

        Returns:
            str: absolute filename
        """
        Path(filepath).mkdir(parents=True, exist_ok=True)
        pfilename = Path(filepath) / f"{filename}"
        with open(pfilename, "w") as outfile:
            json.dump(self.dict(), outfile, ignore_nan=True)
        return str(pfilename)
