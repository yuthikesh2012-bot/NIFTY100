from typing import Dict,Any
class FeatureStore:
    def __init__(self):
        self._store:Dict[str,Any]={}
    def save(self,key:str,features:Any):
        self._store[key]=features
    def load(self,key:str):
        return self._store.get(key)
