#################################################
#  Move raw groups to group table
#################################################

import pyodbc
import pandas as pd
import numpy as np

def upodateRawGroups(funds_info,conn):

    conn_cursor = conn.cursor()
    conn_cursor.fast_executemany = True

    # Clean old in Raw and today's in structured data
    conn_cursor.execute("DELETE FROM Trade_Grupos_Raw WHERE Date0 < CONVERT(char(10),GETDATE(),126)")
    conn_cursor.execute(
        "DELETE FROM Trade_Grupos_Detail WHERE GroupId IN (SELECT GroupID FROM Trade_Grupos_Info WHERE GroupDate = CONVERT(char(10),GETDATE(),126))")
    conn_cursor.execute(
        "DELETE FROM Trade_Grupos_Info WHERE GroupDate = CONVERT(char(10),GETDATE(),126)")

    # Add new data
    group_raw = pd.read_sql("SELECT * FROM Trade_Grupos_Raw", conn)
    if group_raw.shape[0] > 0:
        group_raw = group_raw.merge(funds_info[['FundoID','nmFundo']],left_on='FundoNome',right_on='nmFundo',how='left')
        group_raw['ID']=0

        for name_i, group_i in group_raw.groupby('GroupName'):
            group_des = " ".join(group_i.GroupInfo[group_i.GroupInfo.notnull()])
            sql_string = "INSERT INTO Trade_Grupos_Info (GroupName,GroupInfo,GroupDate,Owner0) VALUES ('{}','{}','{}','{}')".format(
                group_i.GroupName.iloc[0],
                group_des,
                group_i.Date0.iloc[0],
                group_i.Owner0.iloc[0])
            conn_cursor.execute(sql_string)

            # Get ID
            sql_sting = "SELECT GroupId FROM Trade_Grupos_Info WHERE (GroupName='{}') AND (GroupDate='{}')".format(
                group_i.GroupName.iloc[0],
                group_i.Date0.iloc[0]
            )
            group_id = pd.read_sql(sql_sting, conn)
            group_id = group_id.GroupId[0]

            # Add group details
            group_raw.loc[group_i.index,'ID']=group_id

        # To avoid problems with null value
        isQuant = group_raw.Ratio.isnull()
        if(any(isQuant)):
            sql_insert_data = [
                    (row.ID,
                     row.FundoID,
                     row.Quant
                     ) for index_i, row in group_raw.loc[isQuant].iterrows()
                ]
            print(sql_insert_data)
            sql_insert = "INSERT INTO Trade_Grupos_Detail (GroupId,FundoId,Quant) VALUES (?,?,?)"
            conn_cursor.executemany(sql_insert, sql_insert_data)
            conn_cursor.commit()

        if(not all(isQuant)):
            sql_insert_data = [
                    (row.ID,
                     row.FundoID,
                     row.Ratio
                     ) for index_i, row in group_raw.loc[~isQuant].iterrows()
                ]
            sql_insert = "INSERT INTO Trade_Grupos_Detail (GroupId,FundoId,Ratio) VALUES (?,?,?)"
            conn_cursor.executemany(sql_insert, sql_insert_data)
            conn_cursor.commit()