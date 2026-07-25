import logging
logger=logging.getLogger("nifty100.etl")
if not logger.handlers:
    h=logging.StreamHandler();logger.addHandler(h)
logger.setLevel(logging.INFO)
