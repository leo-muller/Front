#################################################
# Treat raw orders
# Move Trade_Orders_Raw to Trade_Orders
#################################################

import pyodbc
import pandas as pd
import numpy as np
from datetime import datetime
from dateutil.relativedelta import relativedelta
from Python.ordersTreatGroups import upodateRawGroups
from Python.ordersTickerTreat import tickerTreat
from Python.splitRawOrders import ordem_tree

def treat_raw_orders():

    # Connect and get basic tables
    conn = pyodbc.connect('Driver={SQL SERVER};'
                          'Server=s01bds64;'
                          'Database=BD_Mesa;'
                          'Trusted_Connection=yes;')

    trades_list = pd.read_sql("SELECT * FROM Trade_Orders_Raw", conn)
    group_list = pd.read_sql("SELECT * FROM bd_risco..Pre_Grupos WHERE data = (SELECT MAX(data) FROM BD_RISCO..Pre_Grupos)", conn)
    group_list['FundoID']=group_list['FundoID'].astype(int)

    print(27)
    # Filter group to funds info
    funds_info = group_list[['FundoID','nmFundo','CD_CARTEIRA','vlPatrimonio','CD_CCI']].groupby('FundoID',as_index =False).last()

    # Upodate group info
    upodateRawGroups(funds_info, conn)
    print(33)
    # Get relevant Risk groups
    group_risk = group_list['Grupo'].unique()
    group_trade = trades_list['GrupoRaw'].unique()

    # See if we need taylor groups
    group_add = group_trade[~np.isin(group_trade,group_risk)]
    if len(group_add)>0:
        sql_string = "SELECT C1.GroupName, C2.* FROM (" \
                     "SELECT GroupName,MAX(GroupID) AS GroupID  FROM Trade_Grupos_Info WHERE GroupName IN ('{}') GROUP BY GroupName" \
                     ") AS C1 " \
            "INNER JOIN Trade_Grupos_Detail AS C2 ON C1.GroupID = C2.GroupID".format("','".join(group_add))
        group_list_mesa = pd.read_sql(sql_string,conn)
        group_list_mesa['Participacao'] = 1
        group_list_mesa['FundoId']=group_list_mesa['FundoId'].astype(int)
        group_list_mesa = group_list_mesa.merge(funds_info[['FundoID', 'vlPatrimonio']], left_on='FundoId',
                                                right_on='FundoID',how='left')
        for name_i, group_i in group_list_mesa.groupby('GroupId'):
            if len(group_i.Ratio) > 1:
                if (group_i.Ratio.values[0]==None) | np.isnan(group_i.Ratio.values[0]):
                    group_list_mesa.loc[group_i.index,'Participacao'] = group_i.Quant.values / np.sum(
                        group_i.Quant.values)
                else:
                    group_list_mesa_sum = group_i.Ratio.values * group_i.vlPatrimonio.values
                    group_list_mesa.loc[group_i.index,'Participacao'] = group_list_mesa_sum / np.sum(group_list_mesa_sum)
    print(58)
    # Treat template tickers
    tickers_treated = tickerTreat(trades_list, conn)

    # Split the raw orders
    conn_cursor = conn.cursor()
    conn_cursor.execute(
        "DELETE FROM Trade_Orders_Split WHERE OrderId IN (SELECT OrderId FROM Trade_Orders WHERE Date0 = CONVERT(char(10),GETDATE(),126))")
    conn_cursor.execute(
        "DELETE FROM Trade_Orders WHERE Date0 = CONVERT(char(10),GETDATE(),126)")
    orders_detail_data = []
    print(69)
    col_save = ['Quantidade','Preco','Est1','Est2','Est3','Owner0','Date0','FillType','FillAsset','FillEst',
                'TradeRational','TickerID','CorretoraID','SaveType']
    for name_i, orders_i in tickers_treated.groupby(['GrupoRaw','TickerID','C_V','Est1','Est2','Est3']):
        orders_i = orders_i.copy()
        if orders_i.GrupoRaw.iloc[0] in group_risk:
            group_type = 'padrao'
            group_i = group_list[['GrupoID','FundoID','Participacao']].loc[group_list.Grupo==name_i[0]].copy()
        else:
            group_type = 'novo'
            group_i = group_list_mesa[['GroupId','FundoID','Participacao']].loc[group_list_mesa.GroupName==name_i[0]].copy()
            group_i.columns = ['GrupoID','FundoID','Participacao']

        # Faz o split
        print(orders_i)
        print(group_i)
        split_ordens =  ordem_tree(
                orders_i.Quantidade.values,  # quantity traded and not allocated
                orders_i.Preco.values,  # price of each trade
                group_i.Participacao.values,  # target ratio for each fund
                1  # Border lot
        )
        if orders_i.C_V.iloc[0] == "V":
            split_ordens = -1*split_ordens

        # Trata rolagem
        if orders_i.TickerTemplate.iloc[0] == "FUT DOL DR1":
            orders_i['SaveType']="Itau"
            ponta_curta = orders_i[trades_list.columns].copy()
            ponta_curta['Preco']=orders_i['PrecoAux']
            ponta_curta['C_V']='V' if orders_i.C_V[0]=='C' else 'C'
            ponta_longa = orders_i[trades_list.columns].copy()
            ponta_longa['Preco'] = orders_i['PrecoAux']+orders_i['Preco']
            venc_aux = datetime.strptime(orders_i.Vencimento[0], '%Y-%m-%d')+relativedelta(months=+1)
            ponta_longa['Vencimento'] = venc_aux.strftime("%Y-%m-%d")

            order_add = ponta_curta.append(ponta_longa).reset_index(drop=True)
            order_add['TickerRaw'] = "FUT DOL"

            order_add = tickerTreat(order_add, conn)
            order_add['SaveType'] = "MitraFut"
            orders_i = orders_i.append(order_add).reset_index(drop=True)

            split_ordens = np.concatenate((split_ordens,-1*split_ordens,split_ordens),axis=1)
        else:
            orders_i['SaveType'] = "ItauMitraFut"


        # Salva valores
        order_col = 0
        for save_idx, save_i in orders_i.iterrows():

            # Save each order
            saveDict = {}
            for key_i in col_save:
                if  save_i[key_i]!=None:
                    if isinstance(save_i[key_i],str):
                        saveDict[key_i] = "\'" + save_i[key_i] + "\'"
                    else:
                        saveDict[key_i] = str(save_i[key_i])

            saveDict['GrupoId'] = str(group_i.GrupoID.iloc[0])
            saveDict['GrupoType'] = "\'" + group_type +"\'"

            sql_string = "INSERT INTO Trade_Orders (" + \
                ",".join(saveDict.keys()) + ")" + \
                " VALUES (" + \
                ",".join(saveDict.values()) + \
                ")"

            conn_cursor.execute(sql_string)
            conn_cursor.commit()
            save_id = pd.read_sql("SELECT SCOPE_IDENTITY()", conn)

            # Update order detail
            for order_row in range(group_i.shape[0]):
                orders_detail_data.append(
                    (int(save_id.values[0]),
                     int(group_i.FundoID.values[order_row]),
                     split_ordens[order_row,order_col]
                     )
                )
            order_col = order_col + 1

    sql_insert = "INSERT INTO Trade_Orders_Split (OrderId,FundoID,Quant) VALUES (?,?,?)"
    conn_cursor.executemany(sql_insert, orders_detail_data)
    conn_cursor.commit()