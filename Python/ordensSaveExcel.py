import pandas as pd
import pyodbc
import datetime
import xlsxwriter
import numpy as np

def save_files():
    path_output = "K://Temp/Leonardo_Muller/Trades/"
    today_aux = np.datetime64(datetime.datetime.now())
    today_aux2 = pd.to_datetime(today_aux)

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
        sql_query = "SELECT  GrupoID,Grupo FROM BD_RISCO..Pre_Grupos WHERE (" \
                    "data = (SELECT MAX(data) FROM BD_RISCO..Pre_Grupos) AND " \
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

    xls_file_name = 'Trades_python_{}.xlsx'.format(today_aux2.strftime('%Y_%m_%d'))
    writer = pd.ExcelWriter(path_output + xls_file_name, engine='xlsxwriter')

    # Futuros
    colsMitra = ['C_V','CD_CARTEIRA','TickerMitra','Quant','Preco','CorretoraMitra','PU','Est1','Est2','Est3',
                 'Vazio','Vazio','Vazio','Vazio','Vazio',
                 'GrupoTexto','GrupoMotivo']

    rowsMitraFut = Trades_Info_Full['SaveType'].isin(('MitraFut','ItauMitraFut')).tolist()
    MitraDf = Trades_Info_Full.loc[rowsMitraFut,colsMitra].copy()
    MitraDf['Quant']=np.abs(MitraDf['Quant'])
    is_PU = MitraDf['TickerMitra'].apply(lambda x: x[:4]=='DI1F')
    MitraDf.loc[~is_PU,"PU"]=""
    MitraDf.loc[is_PU, "Preco"] = ""
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

    writer.save()

    # Itau to text_file
    txt_file_name = 'Trades_python_{}.txt'.format(pd.to_datetime(today_aux).strftime('%Y_%m_%d'))
    Trades_Itau.to_csv(path_output + txt_file_name, sep='\t', index=False)


