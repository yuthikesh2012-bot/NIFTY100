def validate_features(df):
    required=["daily_return"]
    return all(c in df.columns for c in required)
