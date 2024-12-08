import os

from pyren3.mod import config

config.BASE_PATH = os.path.dirname(os.path.abspath(__file__))

if config.OS == "android":
    from main_android import main
else:
    from main_desktop import main

if __name__ == "__main__":
    main()
