import anvil.server
from dotenv import load_dotenv
import os
from pathlib import Path
import uuid
import subprocess

from leveelogic.deltares.dstability import DStability
from leveelogic.deltares.algorithms.algorithm_berm_from_z import AlgorithmBermFromZ


load_dotenv()
ANVIL_KEY = os.getenv("ANVIL_KEY")
TEMP_FILES_PATH = os.getenv("TEMP_FILES_PATH")
DSTABILITY_PATH = os.getenv("DSTABILITY_PATH")
DSTABILITY_MIGRATION_CONSOLE_PATH = os.getenv("DSTABILITY_MIGRATION_CONSOLE_PATH")

anvil.server.connect(ANVIL_KEY)


def update_stix(stix_file):
    subprocess.run([DSTABILITY_MIGRATION_CONSOLE_PATH, stix_file, stix_file])


@anvil.server.callable
def LL_parse_stix(stix_file):
    print("UPLOAD stix file", type(stix_file))
    # write to temporary file
    fname = Path(TEMP_FILES_PATH) / f"{uuid.uuid4()}.stix"
    with open(fname, "wb") as f:
        f.write(stix_file.get_bytes())

    try:
        ds = DStability.from_stix(fname)
    except:
        try:
            update_stix(fname)
            ds = DStability.from_stix(fname)
        except Exception as e:
            raise ValueError(f"Error reading file '{fname}'; '{e}")

    result = {
        "soiltypes": ds.soils,
        "soillayers": ds.soillayers,
        "plline": ds.phreatic_line_points,
        "result": ds.safety_factor_to_dict(),
    }

    # remove the file
    file_path = Path(fname)
    file_path.unlink()

    return result


@anvil.server.callable
def LL_auto_berm(file, settings):
    print("ALG AUTO BERM CALLED")
    print(settings)
    print("EXE STIX FILE", type(bytes))
    try:
        fname = Path(TEMP_FILES_PATH) / f"{uuid.uuid4()}.stix"
        with open(fname, "wb") as f:
            f.write(file.get_bytes())
    except Exception as e:
        print(f"Error writing file; {e}")

    try:
        ds = DStability.from_stix(fname)
    except:
        raise ValueError(f"Error reading file '{fname}'; '{e}")

    alg = AlgorithmBermFromZ(
        ds=ds,
        soilcode=settings["berm_material"],
        required_sf=settings["req_sf"],
        x_base=settings["berm_designpoint_x"],
        angle=settings["growth_slope"],
        initial_height=settings["berm_initial_height"],
        slope_top=settings["berm_slope_top"],
        slope_side=settings["berm_slope_side"],
        step_size=settings["berm_height_step"],
    )

    try:
        ds = alg.execute()
    except Exception as e:
        print(e)
        raise e

    # remove the file
    # file_path = Path(fname)
    # file_path.unlink()

    result = {
        "soillayers": ds.soillayers,
        "plline": ds.phreatic_line_points,
        "result": ds.safety_factor_to_dict(),
    }


anvil.server.wait_forever()
