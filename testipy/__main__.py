import sys
import os
# allow root folder to be available for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from testipy.run import run_testipy


if __name__ == "__main__":
    sys.exit(run_testipy())
