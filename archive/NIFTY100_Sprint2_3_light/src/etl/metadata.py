from datetime import datetime
def metadata(df,name):
    return {
        "dataset":name,
        "rows":len(df),
        "columns":len(df.columns),
        "loaded_at":datetime.now().isoformat()
    }
