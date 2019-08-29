import pyodbc
import pandas as pd
import numpy as np
from datetime import datetime
from dateutil.relativedelta import relativedelta

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
        trades_list['MoVenc'] = ""

        for name_i, row_i in trades_list[valid].iterrows():
            venc_i_m = letterMonth[int(row_i['Vencimento'][5:7])-1]
            venc_i_y = row_i['Vencimento'][2:4]

            # Change Ticker Raw to Mitra

            if row_i['TickerBlgCore']!=None:
                trades_list.loc[name_i, 'TickerBlg'] = row_i['TickerBlgCore']+ venc_i_m+ venc_i_y + " " + row_i['TickerBlgSufix']

            if row_i['TickerRaw'] in ("FUT DOL DR1", "FUT WDO DR1", "FUT WIN IR1", "FUT IND IR1"):
                if  row_i['TickerRaw'] in ("FUT DOL DR1", "FUT WDO DR1"):
                    venc_aux = datetime.strptime(row_i['Vencimento'], '%Y-%m-%d') + relativedelta(months=+1)
                else:
                    venc_aux = datetime.strptime(row_i['Vencimento'], '%Y-%m-%d') + relativedelta(months=+2)
                venc_aux = venc_aux.strftime("%Y-%m-%d")
                venc_i_m2 = letterMonth[int(venc_aux[5:7]) - 1]
                venc_i_y = row_i['Vencimento'][2:4]
                venc_i_y2 =venc_aux[2:4]
                trades_list.loc[name_i, 'TickerRaw'] = row_i['TickerBrokerCore'] + venc_i_m + venc_i_y + venc_i_m2 + venc_i_y2
                trades_list.loc[name_i, 'MoVenc'] = venc_i_m + venc_i_y + venc_i_m2 + venc_i_y2

                venc_i_y = row_i['Vencimento'][3:4]
                venc_i_y2 =venc_aux[3:4]
                trades_list.loc[name_i, 'TickerBroker'] = row_i['TickerBrokerCore'] + venc_i_m + venc_i_y + venc_i_m2 + venc_i_y2

            else:
                trades_list.loc[name_i, 'TickerRaw'] = row_i['TickerMitraCore'] + venc_i_m + venc_i_y
                trades_list.loc[name_i, 'TickerBroker'] = row_i['TickerBrokerCore']+ venc_i_m+ venc_i_y
                trades_list.loc[name_i, 'MoVenc'] = venc_i_m+ venc_i_y

        # Do we have
    return trades_list
