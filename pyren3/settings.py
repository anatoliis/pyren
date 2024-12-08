import json
import os
import pprint


class Settings:
    path: str = "./pyren3"
    port: str = "192.168.0.10:35000"
    lang: str = "RU"
    speed: str = "38400"
    log_name: str = "log.txt"
    csv_option: str = "csv"
    log: bool = True
    cfc: bool = True
    n1c: bool = False
    si: bool = False
    csv: bool = False
    dump: bool = True
    can2: bool = False
    options: str = ""

    def __init__(self):
        self._load_settings()

    def _load_settings(self) -> None:
        path = "./settings.json"
        if not os.path.isfile(path):
            self.save()
        settings_ = self._read_settings(path=path)
        self.__dict__.update(settings_)

    @staticmethod
    def _read_settings(path: str) -> dict:
        settings_ = {}
        with open(path, "r") as file:
            settings_raw: str = file.read()
        try:
            settings_ = json.loads(settings_raw)
        except (TypeError, json.decoder.JSONDecodeError):
            pass
        return settings_

    @staticmethod
    def _write_settings(path: str, data: dict) -> None:
        with open(path, "w") as file:
            file.write(json.dumps(data, indent=2))
        print(data)

    def save(self) -> None:
        self._write_settings(
            path="./settings.json",
            data=self.__dict__,
        )

    def __str__(self):
        return pprint.pformat(self.__dict__)
