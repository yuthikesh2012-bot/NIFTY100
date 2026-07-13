import pandas as pd

def remove_duplicates(df):
    return df.drop_duplicates()

def remove_empty_rows(df):
    return df.dropna(how="all")

def standardize_missing(df):
    return df.replace({"NA":None,"N/A":None,"-":None})
