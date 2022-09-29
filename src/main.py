# __main__.py

import sys
from src.pymologie import pymologie

def main():
    pym = pymologie()
    if len(sys.argv) > 1:
        print(pym.suchen(sys.argv[1]))
if __name__ == "__main__":
    main()