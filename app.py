import importlib.util
import os
import sys


BASE_DIR = os.path.dirname(__file__)
SOURCE_DIR = os.path.join(BASE_DIR, "source_code")
SOURCE_APP_PATH = os.path.join(BASE_DIR, "source_code", "app.py")
if SOURCE_DIR not in sys.path:
    sys.path.insert(0, SOURCE_DIR)

spec = importlib.util.spec_from_file_location("task_manager_source_app", SOURCE_APP_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("Could not load Flask app module from source_code/app.py")

module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
app = module.app

