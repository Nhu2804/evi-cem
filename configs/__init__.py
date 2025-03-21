import os
import yaml
import json
import hashlib
import argparse

from ast import literal_eval
from multimethod import multimethod
from typing import Any, Dict, List, Tuple, Union


class Config(dict):
    def __getattr__(self, key: str) -> Any:
        if key not in self:
            raise AttributeError(key)
        return self[key]

    def __setattr__(self, key: str, value: Any) -> None:
        self[key] = value

    def __delattr__(self, key: str) -> None:
        del self[key]

    def load(self, fpath: str, *, recursive: bool = False) -> None:
        if not os.path.exists(fpath):
            raise FileNotFoundError(fpath)
        fpaths = [fpath]
        if recursive:
            extension = os.path.splitext(fpath)[1]
            while os.path.dirname(fpath) != fpath:
                fpath = os.path.dirname(fpath)
                fpaths.append(os.path.join(fpath, "default" + extension))
        for fpath in reversed(fpaths):
            if os.path.exists(fpath):
                with open(fpath) as f:
                    self.update(yaml.safe_load(f))

    def reload(self, fpath: str, *, recursive: bool = False) -> None:
        self.clear()
        self.load(fpath, recursive=recursive)

    @multimethod
    def update(self, other: Dict) -> None:
        for key, value in other.items():
            if isinstance(value, dict):
                if key not in self or not isinstance(self[key], Config):
                    self[key] = Config()
                self[key].update(value)
            else:
                self[key] = value

    @multimethod
    def update(self, opts: Union[List, Tuple]) -> None:
        index = 0
        while index < len(opts):
            opt = opts[index]
            if opt.startswith("--"):
                opt = opt[2:]
            if "=" in opt:
                key, value = opt.split("=", 1)
                index += 1
            else:
                key, value = opt, opts[index + 1]
                index += 2
            current = self
            subkeys = key.split(".")
            try:
                value = literal_eval(value)
            except:
                pass
            for subkey in subkeys[:-1]:
                current = current.setdefault(subkey, Config())
            current[subkeys[-1]] = value

    def dict(self) -> Dict[str, Any]:
        configs = dict()
        for key, value in self.items():
            if isinstance(value, Config):
                value = value.dict()
            configs[key] = value
        return configs

    def hash(self) -> str:
        buffer = json.dumps(self.dict(), sort_keys=True)
        return hashlib.sha256(buffer.encode()).hexdigest()

    def __str__(self) -> str:
        texts = []
        for key, value in self.items():
            if isinstance(value, Config):
                seperator = "\n"
            else:
                seperator = " "
            text = key + ":" + seperator + str(value)
            lines = text.split("\n")
            for k, line in enumerate(lines[1:]):
                lines[k + 1] = (" " * 2) + line
            texts.extend(lines)
        return "\n".join(texts)


def get_config():
    config = Config()
    parser = argparse.ArgumentParser("CBM")
    parser.add_argument("--config", type=str, required=True, help="config file")
    args, opts = parser.parse_known_args()
    config.load(args.config, recursive=True)
    config.update(opts)
    return config
