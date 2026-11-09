import sys

from app import run_app

if __name__ == "__main__":
    # "python main.py test" turns on test mode for user testing
    run_app(len(sys.argv) > 1 and sys.argv[1] == "test")
