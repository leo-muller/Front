# ##############################################
# Create dataframe for Mitra
# and save info in the base
# ##############################################

import numpy as np
import pandas as pd
from datetime import datetime
import pyodbc

def save_files_rjo(conn):
    rjoCsvPath = "K://Temp/Leonardo_Muller/RJO.csv"
    rjoDf = pd.read_csv(rjoCsvPath)
    rjoDate = datetime.strptime(rjoDf.loc[0,'Trade Date'], '%m/%d/%Y %I:%M:%S %p')
    conn_cursor = conn.cursor()

    # Testa se arquivo é atual
    if rjoDate.strftime('%Y-%m-%d')==datetime.now().strftime('%Y-%m-%d'):

        # Group same prices
        rjoDf = rjoDf[['Acct', 'Quantity', 'B/S', 'Long Description', 'Price/Amount']]
        rjoDf = rjoDf.groupby(['Acct', 'B/S', 'Long Description', 'Price/Amount'],as_index=False).sum()

        # Get assets already in the base (we save RJO ticker for non exotic assets
        conn = pyodbc.connect('Driver={SQL SERVER};'
                              'Server=s01bds64;'
                              'Database=BD_Mesa;'
                              'Trusted_Connection=yes;')
        existing_ticker = pd.read_sql("SELECT TickerId,TickerInfo,TickerInfoVal FROM  Trade_Asset_Info_Aux WHERE TickerInfo IN ('TickerRJO','FactorRJO','FatorMitra')",
                                  conn)

        existing_names = existing_ticker[existing_ticker['TickerInfo']=='TickerRJO']['TickerInfoVal'].unique()

        # Se we need to add tickers
        asset_in_the_base =  rjoDf['Long Description'].isin(existing_names).tolist()
        if not all(asset_in_the_base):
            venc_list = ["F", "G", "H", "J", "K", "M", "N", "Q", "U", "V", "X", "Z"]
            rjo_template = pd.read_sql("SELECT * FROM  Trade_Asset_Template_RJO", conn)
            for i in range(rjoDf.shape[0]):
                if not asset_in_the_base[i]:

                    # Update assets in the base
                    asset_in_the_base = \
                        np.where(rjoDf['Long Description'] == rjoDf.loc[i, 'Long Description'], True, asset_in_the_base)

                    venc_i_str = rjoDf.loc[i, 'Long Description'][:6]
                    venc_i = datetime.strptime(venc_i_str, '%b %y')
                    core_i_str = rjoDf.loc[i, 'Long Description'][7:]

                    rjo_i = rjo_template[rjo_template.RJO==core_i_str]

                    sql_dict = {}
                    sql_dict['TickerMitra'] = rjo_i.MitraPrefix.iloc[0]+ venc_list[venc_i.month-1] + \
                                  str(venc_i.year%100) + "." + rjo_i.MitraSulfix.iloc[0]
                    sql_dict['TickerBlg'] = rjo_i.Blg.iloc[0]+ venc_list[venc_i.month-1] + \
                                  str(venc_i.year%100) + " " + rjo_i.BlgSufix.iloc[0]
                    sql_dict['TickerType'] = rjo_i.TickerType.iloc[0]

                    sql_string = "INSERT INTO Trade_Asset_Info ({}) VALUES ('{}')".format(
                        ",".join(sql_dict.keys()),
                        "','".join(sql_dict.values())
                    )
                    conn_cursor.execute(sql_string)
                    conn_cursor.commit()
                    conn_cursor.execute("SELECT @@IDENTITY AS 'Identity'")
                    for rr in conn_cursor:
                        save_id = int(str(rr[0]))

                    sql_string = "INSERT INTO Trade_Asset_Info_Aux (TickerID,TickerInfo,TickerInfoVal) VALUES ({},'{}','{}')".format(
                        save_id,
                        'TickerRJO',
                        rjoDf.loc[i, 'Long Description']
                    )
                    conn_cursor.execute(sql_string)
                    conn_cursor.commit()

                    sql_string = "INSERT INTO Trade_Asset_Info_Aux (TickerID,TickerInfo,TickerInfoVal) VALUES ({},'{}',{})".format(
                        save_id,
                        'FactorRJO',
                        int(rjo_i.FactRJO.iloc[0])
                    )
                    conn_cursor.execute(sql_string)
                    conn_cursor.commit()

                    sql_string = "INSERT INTO Trade_Asset_Info_Aux (TickerID,TickerInfo,TickerInfoVal) VALUES ({},'{}',{})".format(
                        save_id,
                        'FatorMitra',
                        int(rjo_i.FatorMitra.iloc[0])
                    )
                    conn_cursor.execute(sql_string)
                    conn_cursor.commit()

            existing_ticker = pd.read_sql(
                "SELECT TickerId,TickerInfo,TickerInfoVal FROM  Trade_Asset_Info_Aux WHERE TickerInfo IN ('TickerRJO','FactorRJO','FatorMitra')",
                conn)

        # Organize tickers
        existing_ticker = existing_ticker.pivot(index='TickerId', columns='TickerInfo', values='TickerInfoVal')
        ticker_core = pd.read_sql("SELECT * FROM  Trade_Asset_Info", conn, index_col="TickerID")
        existing_ticker = existing_ticker.merge(ticker_core, how='left', left_index=True, right_index=True)
        existing_ticker = existing_ticker.reset_index()

        # Organize orders
        rjoDf = rjoDf.merge(existing_ticker, how='left', left_on='Long Description', right_on='TickerRJO')
        rjoDf['Fundo'] = np.where(rjoDf['Acct']==10034,
                                  'SPC PORTIFOLIO A | SULAMERICA SPC PORTIFOLIO A',
                                  'SPC PORTIFOLIO B | SULAMERICA SPC PORTIFOLIO B',
                                  )

        rjoDf['FundoId'] = np.where(rjoDf['Acct']==10034, 931, 932)
        rjoDf['Est1'] = np.where(rjoDf['Acct'] == 10034, "MOEDAS", "TATICO")
        rjoDf['Est2'] = np.where(rjoDf['Acct'] == 10034, rjoDf['TickerType'], "TATICO")
        rjoDf['Est3'] = rjoDf['Est2']
        rjoDf['C_V'] = np.where(rjoDf['B/S'] == 'B', 'Compra', 'Venda')

        rjoDf['Corretora'] = "R.J. O'Brien & Associates LLC"
        rjoDf['CorretoraId']=9999
        rjoDf['Vazio']=""
        rjoDf['SaveType']="MitraOffFut"
        rjoDf['FactorRJO'] = rjoDf['FactorRJO'].astype('int')
        rjoDf['FatorMitra'] = rjoDf['FatorMitra'].astype('int')
        rjoDf['PrecoOff']=rjoDf['Price/Amount']/rjoDf['FactorRJO']
        rjoDf['PrecoMitra'] = rjoDf['PrecoOff'] / rjoDf['FatorMitra']
        rjoDf['GrupoType']='padrao'
        rjoDf['GrupoID'] = np.where(rjoDf['Acct'] == 10034,125,126)
        rjoDf['GrupoNome'] = np.where(rjoDf['Acct'] == 10034,"Moedas Offshore","Tatico Offshore")

        # Salva ordens
        rjoSave = rjoDf[['TickerId','Quantity','PrecoOff','CorretoraId','Est1','Est2','Est3','GrupoType',
                         'GrupoID','SaveType']].copy()
        rjoSave['Quantity']=np.where(rjoDf['B/S'] == 'B', rjoSave['Quantity'], -1*rjoSave['Quantity'])
        rjoSave['Quantity']=rjoSave['Quantity'].astype('int')
        rjoSave.columns = ['TickerId','Quantidade','Preco','CorretoraId','Est1','Est2','Est3','GrupoType','GrupoId','SaveType']
        rjoSave[['Est1', 'Est2', 'Est3', 'GrupoType', 'SaveType']] = "'" + rjoSave[['Est1', 'Est2', 'Est3', 'GrupoType', 'SaveType']] +"'"

        for idx, row in rjoSave.iterrows():
            sql_string = "INSERT INTO Trade_Orders (" + \
                     ",".join(row.keys()) + ")" + \
                     " VALUES (" + \
                     ",".join([str(x) for x in row]) + \
                     ")"

            conn_cursor.execute(sql_string)
            conn_cursor.commit()

            conn_cursor.execute("SELECT @@IDENTITY AS 'Identity'")

            for rr in conn_cursor:
                save_id = int(str(rr[0]))

            sql_insert = "INSERT INTO Trade_Orders_Split (OrderId,FundoID,Quant) VALUES ({},{},{})".format(
                save_id,rjoDf['FundoId'].loc[idx],row['Quantidade']
            )
            conn_cursor.execute(sql_insert)
            conn_cursor.commit()

        # Mitra format
        rjoMitra = rjoDf[['C_V', 'Fundo', 'TickerMitra', 'Quantity', 'PrecoMitra','Corretora','Vazio','Est1','Est2',
                          'Est3','Vazio','Vazio','Vazio','GrupoNome','Vazio','Vazio','Vazio','PrecoOff']].copy()
        return rjoMitra
    return None
