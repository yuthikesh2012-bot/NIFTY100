from pydantic import BaseModel, Field
from datetime import date
class OHLCVRecord(BaseModel):
    symbol:str
    date:date
    open:float=Field(...,ge=0)
    high:float=Field(...,ge=0)
    low:float=Field(...,ge=0)
    close:float=Field(...,ge=0)
    volume:int=Field(...,ge=0)
class CompanyMetadata(BaseModel):
    symbol:str
    name:str
    sector:str|None=None
    industry:str|None=None
    exchange:str="NSE"
