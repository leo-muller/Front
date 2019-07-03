import pyodbc
import pandas as pd
import numpy as np

def tickerExcelTemplate(trades_list,conn):

    trades_templates = pd.read_sql("SELECT * FROM Trade_Asset_Template_Excel", conn)
    letterMonth = ["F", "G", "H", "J", "K", "M", "N", "Q", "U", "V", "X", "Z"]

    trades_list = trades_list.merge(trades_templates,
                                    left_on = 'TickerRaw',
                                    right_on = 'TickerTemplate',
                                    how = 'left')

    valid = ~np.isnan(trades_list.TickerTemplateId.values)
    if any(valid):
        # Compute tickers based on template
        trades_list['TickerBlg'] = ""
        trades_list['TickerBroker'] = ""

        for name_i, row_i in trades_list[valid].iterrows():
            venc_i_m = letterMonth[int(row_i['Vencimento'][5:7])-1]
            venc_i_y = row_i['Vencimento'][2:4]

            # Change Ticker Raw to Mitra
            trades_list.loc[name_i,'TickerRaw'] = row_i['TickerMitraCore']+ venc_i_m+ venc_i_y
            if row_i['TickerBlgCore']!=None:
                trades_list.loc[name_i, 'TickerBlg'] = row_i['TickerBlgCore']+ venc_i_m+ venc_i_y + " " + row_i['TickerBlgSufix']
            trades_list.loc[name_i, 'TickerBroker'] = row_i['TickerBrokerCore']+ venc_i_m+ venc_i_y

        # Do we have
    return trades_list
