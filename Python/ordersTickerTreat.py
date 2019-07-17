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
    add_ticker = trades_treated.TickerID.isnull().tolist()
    if any(add_ticker):
        sql_insert_data = []
        sql_insert_data_aux =pd.DataFrame({})
        for index_i, row in trades_treated.loc[add_ticker].groupby('TickerRaw').last().iterrows():
            sql_insert_data.append(
                (index_i,row.TickerBroker,row.TickerType)
            )
            sql_insert_data_aux= sql_insert_data_aux.append({
                'TickerMitra':index_i,
                'MoTicker':row.TickerMO,
                'MoVenc':index_i[-3:],
            },ignore_index=True)

        # Add core info
        conn_cursor = conn.cursor()
        conn_cursor.fast_executemany = True
        sql_query = "INSERT INTO Trade_Asset_Info (TickerMitra,TickerBroker,TickerType) VALUES (?,?,?)"
        conn_cursor.executemany(sql_query, sql_insert_data)
        conn_cursor.commit()

        # Add MO info
        sql_query = "SELECT TickerID, TickerMitra FROM Trade_Asset_Info WHERE TickerMitra IN ('{}')" \
                                  .format("','".join(sql_insert_data_aux.TickerMitra.tolist()))
        ticker_info = pd.read_sql(sql_query,conn)

        sql_insert_data_aux = sql_insert_data_aux.merge(ticker_info,on="TickerMitra")
        sql_insert_data = []
        for index_i, row in sql_insert_data_aux.iterrows():
            sql_insert_data.append((row.TickerID,'MoTicker',row.MoTicker))
            sql_insert_data.append((row.TickerID,'MoVenc',row.MoVenc))

        sql_query = "INSERT INTO Trade_Asset_Info_Aux (TickerID,TickerInfo,TickerInfoVal) VALUES (?,?,?)"
        conn_cursor.executemany(sql_query, sql_insert_data)
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