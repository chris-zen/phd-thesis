import os
import tempfile

def temp_file(base_path=None, suffix=None):
    if base_path is None:
        base_path = tempfile.gettempdir()

    if not os.path.exists(base_path):
        os.makedirs(base_path)

    if base_path[-1] != "/":
        base_path += "/"

    tf = tempfile.NamedTemporaryFile(prefix=base_path, suffix=suffix or "")

    return tf