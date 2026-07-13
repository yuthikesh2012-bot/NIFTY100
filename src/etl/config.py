from dataclasses import dataclass
@dataclass
class ETLConfig:
    strict: bool=True
    encoding:str="utf-8"
