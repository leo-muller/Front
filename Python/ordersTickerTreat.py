import pyodbc
import pandas as pd
import numpy as np
from Python.ordersTickerTemplate import tickerExcelTemplate

def tickerTreat(trades_list,conn):
    trades_mitra = tickerExcelTemplate(trades_list, conn)

    # Get existing assets
    ticker_list = pd.read_sql("SELECT TickerID, TickerMitra, TickerType AS TickerTypeSQL FROM Trade_Asset_Info", conn)
    trades_treated = trades_mitra.merge(ticker_list,
                                          left_on='TickerRaw',
                                          right_on='TickerMitra',
                                          how='left'
                                          )

    # Do we need to add any ticker
    add_ticker = np.isnan(trades_treated.TickerID)
    if any(add_ticker):
        sql_insert_data = [
            (index_i,
             row.TickerBroker,
             row.TickerType
             ) for index_i, row in trades_treated.loc[add_ticker].groupby('TickerRaw').last().iterrows()
        ]
        conn_cursor = conn.cursor()
        conn_cursor.fast_executemany = True
        sql_insert = "INSERT INTO Trade_Asset_Info (TickerMitra,TickerBroker,TickerType) VALUES (?,?,?)"
        conn_cursor.executemany(sql_insert, sql_insert_data)
        conn_cursor.commit()

        # Update
        ticker_list = pd.read_sql("SELECT TickerID, TickerMitra, TickerType AS TickerTypeSQL FROM Trade_Asset_Info", conn)
        trades_treated = trades_mitra.merge(ticker_list,
                                            left_on='TickerRaw',
                                            right_on='TickerMitra',
                                            how='left'
                                            )

    # Add corretora
    trades_treated['CorretoraExcel'] = trades_treated['CorretoraExcel'].str.upper()
    corr_list = pd.read_sql("SELECT CorretoraID, UPPER(CorretoraExcel) AS CorretoraExcel FROM Trade_Corretora", conn)
    trades_treated = trades_treated.merge(corr_list,
                                        left_on='CorretoraExcel',
                                        right_on='CorretoraExcel',
                                        how='left'
                                        )

    return trades_treated