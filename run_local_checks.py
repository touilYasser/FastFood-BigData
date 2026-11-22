import json
import os
import sys
from pathlib import Path
root = Path(__file__).resolve().parent
sys.path.insert(0, str(root))
os.environ["FASTFOOD_LOCAL_DATA"] = str(root/"data")
os.environ["FASTFOOD_SPARK_MASTER"] = "local[2]"
os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["SPARK_LOCAL_IP"] = "127.0.0.1"
for name in sys.argv[1:]:
    path = root/"notebooks"/(name+".ipynb")
    scope = {"__name__":"__main__"}
    for i, cell in enumerate(json.loads(path.read_text(encoding="utf-8"))["cells"],1):
        if cell["cell_type"] == "code":
            print(f"{name} / {i}", flush=True)
            exec(compile("".join(cell["source"]), f"{name}:{i}", "exec"),scope)
