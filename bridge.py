import anvil.server
from dotenv import load_dotenv
import os
from pathlib import Path
import uuid
import subprocess

from leveelogic.deltares.dstability import DStability


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
        "soillayers": ds.soillayers,
        "plline": ds.phreatic_line_points,
        "result": ds.safety_factor_to_dict(),
    }

    # remove the file
    file_path = Path(fname)
    file_path.unlink()

    print(result)
    return result


anvil.server.wait_forever()
