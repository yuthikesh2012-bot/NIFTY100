def insert_dataframe(df, table, connection):
    df.to_sql(table, connection, if_exists='append', index=False)
