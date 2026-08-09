import os
import sys
import traceback

APP_ROOT = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, APP_ROOT)
sys.path.insert(0, os.path.join(APP_ROOT, "packages"))

LOGFILE = os.path.join(APP_ROOT, "startup_error.log")

try:
    from app import app as application

except Exception:
    with open(LOGFILE, "w", encoding="utf-8") as f:
        traceback.print_exc(file=f)

    raise