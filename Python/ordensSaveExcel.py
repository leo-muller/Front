import pandas as pd
import pyodbc
import datetime
from Python.ordersRJO import save_files_rjo
import numpy as np

def save_files():
    path_output = "K://Temp/Leonardo_Muller/Trades/"
    today_aux = np.datetime64(datetime.datetime.now())

    conn = pyodbc.connect('Driver={SQL SERVER};'
                          'Server=s01bds64;'
                          'Database=BD_Mesa;'
                          'Trusted_Connection=yes;')

    Trades_Info = pd.read_sql(
        "SELECT * FROM  " +\
        "(SELECT * FROM Trade_Orders WHERE Date0 = CONVERT(char(10),GETDATE(),126)) AS C1 " + \
        "LEFT JOIN " + \
        "Trade_asset_Info AS C2 ON " + \
        "C1.TickerId = C2.TickerID", conn)

    Trades_Info_Full = pd.read_sql("SELECT * FROM  Trade_Info_Full WHERE Quant!=0", conn)
    Trades_Info_Full['GrupoTexto']="Individual"
    Trades_Info_Full['GrupoMotivo'] = ""
    Trades_Info_Full['Vazio'] = ""
    Trades_Info_Full['PU'] = Trades_Info_Full['Preco']
    Trades_Info_Full['C_V'] = np.where(Trades_Info_Full['Quant'] > 0, "Compra", 'Venda')
    Trades_Info_Full['Quant']=Trades_Info_Full['Quant'].astype('int')

    grupos_id_padrao = Trades_Info.GrupoId.iloc[Trades_Info.GrupoType.values=="padrao"].unique().tolist()
    grupos_id_mesa = Trades_Info.GrupoId.iloc[Trades_Info.GrupoType.values != "padrao"].unique().tolist()

    # ============================================
    # Groups info
    # ============================================

    # Official groups information
    if len(grupos_id_padrao)>0:
        sql_query = "SELECT  GrupoID,Grupo FROM BD_RISCO..pre_grupo_movonline WHERE (" \
                    "data = (SELECT MAX(data) FROM BD_RISCO..pre_grupo_movonline) AND " \
                    "GrupoID IN ({})) GROUP BY GrupoID, Grupo".format(
            ",".join(grupos_id_padrao)
        )
        grupos_padrao = pd.read_sql(sql_query, conn,index_col="GrupoID")

        valid = Trades_Info_Full.GrupoType.values == "padrao"
        grupos_padrao = grupos_padrao.reindex([int(x) for x in Trades_Info_Full.loc[valid,'GrupoId']])
        Trades_Info_Full.loc[valid,'GrupoTexto']=grupos_padrao.Grupo.values

    # Taylor groups information
    if len(grupos_id_mesa)>0:
        sql_query = "SELECT  GroupId, GroupName, GroupInfo FROM Trade_Grupos_Info WHERE " \
                    "GroupId IN ({})".format(
            ",".join(grupos_id_mesa)
        )
        grupos_mesa = pd.read_sql(sql_query, conn,index_col="GroupId")

        valid = Trades_Info_Full.GrupoType.values != "padrao"
        grupos_mesa = grupos_mesa.reindex([int(x) for x in Trades_Info_Full.loc[valid,'GrupoId']])
        Trades_Info_Full.loc[valid,'GrupoMotivo']=["("+row.GroupName+"): "+row.GroupInfo for idx, row in grupos_mesa.iterrows()]

    # ============================================
    # Salva tabelas
    # ============================================

    xls_file_name = 'TradesPython{}.xlsx'.format(datetime.datetime.now().strftime('%Y_%m_%d'))
    writer = pd.ExcelWriter(path_output + xls_file_name, engine='xlsxwriter')

    # Futuros
    colsMitra = ['C_V','CD_CARTEIRA','TickerMitra','Quant','Preco','CorretoraMitra','PU','Est1','Est2','Est3',
                 'Vazio','Vazio','Vazio',
                 'GrupoTexto','GrupoMotivo']

    rowsMitraFut = Trades_Info_Full['SaveType'].isin(('MitraFut','ItauMitraFut')).tolist()
    MitraDf = Trades_Info_Full.loc[rowsMitraFut,colsMitra].copy()
    MitraDf['Quant']=np.abs(MitraDf['Quant'])
    is_PU = MitraDf['TickerMitra'].apply(lambda x: x[:4]=='DI1F' or x[:4]=='DAPF')
    MitraDf.loc[~is_PU,"PU"]=""
    MitraDf.loc[is_PU, "Preco"] = ""
    MitraDf['CorretoraMitra']="ITAU REP"
    MitraDf.to_excel(writer, sheet_name='MitraFut')

    MitraDf['PU']=""
    MitraDf["Preco"]=""
    MitraDf.to_excel(writer, sheet_name='MitraFutPO')

    # Info Itau
    colsItau = ['CD_CCI', 'TickerBroker', 'Quant', 'Preco', 'CorretoraId']
    rowsItau = Trades_Info_Full['SaveType'].isin(('Itau','ItauMitraOpt','ItauMitraFut')).tolist()

    MitraDf = Trades_Info_Full.loc[rowsItau,colsItau].copy()
    MitraDf['C_V'] = np.where(MitraDf['Quant'] > 0, "C", 'V')
    MitraDf['Quant']=np.abs(MitraDf['Quant'])
    MitraDf['Emissor'] = "SAAMERICA"
    MitraDf['CD_CCI'] = MitraDf.CD_CCI.astype('int')
    MitraDf['Data'] = datetime.datetime.now().strftime('%d/%m/%y')
    MitraDf = MitraDf[['Emissor', 'Data', 'CD_CCI', 'TickerBroker', 'CorretoraId', 'C_V', 'Quant', 'Preco']]
    MitraDf.columns = ["Emissor", "Data", "Código", "PrdMercSérie", "Cod Corre", "Cra/Vda", "Qtde",
                           "PU da Operação"]
    MitraDf.to_excel(writer, sheet_name='Itau')

    # Itau to text_file
    txt_file_name = 'Trades_itau_{}.txt'.format(datetime.datetime.now().strftime('%Y_%m_%d'))
    MitraDf.to_csv(path_output + txt_file_name, sep='\t', index=False)

    # Info MO
    rowsMO = Trades_Info_Full.SaveType != 'Itau'
    colsMO = ['MoTicker', 'MoVenc', 'CD_CCI', 'Quant', 'Preco']
    rowsMO = np.logical_and([not x for x in Trades_Info_Full.MoTicker.isnull().tolist()],rowsMO)
    MitraDf = Trades_Info_Full.loc[rowsMO, colsMO].copy()

    MitraDf['C_V'] = np.where(MitraDf['Quant'] > 0, "C", 'V')
    MitraDf['COR']=114
    MitraDf['Quant'] = np.abs(MitraDf['Quant'])
    MitraDf.columns = ['Classe', 'Venc', 'CCI', 'Quant', 'Preco', 'C_V', 'COR']
    MitraDf.to_excel(writer, sheet_name='MO')

    # Fundos offshore baseado no arquivo
    MitraOff = save_files_rjo(conn)
    if not MitraOff is None:
        MitraOff.to_excel(writer, sheet_name='TradesOff')

    Trades_Info_Full.to_excel(writer, sheet_name='TradesFull')

    writer.save()




