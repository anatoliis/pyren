import os

from pyren3 import config

config.BASE_PATH = os.path.dirname(os.path.abspath(__file__))

if config.OS == "android":
    from pyren3.gui.android import main
else:
    from pyren3.gui.desktop import main

if __name__ == "__main__":
    main()
