import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from .constants import MAX_RETRIES,BACKOFF_FACTOR
def create_session():
 s=requests.Session();r=Retry(total=MAX_RETRIES,backoff_factor=BACKOFF_FACTOR,status_forcelist=[429,500,502,503,504]);a=HTTPAdapter(max_retries=r);s.mount("http://",a);s.mount("https://",a);return s
