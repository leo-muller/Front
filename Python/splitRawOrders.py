import numpy as np
import pandas as pd
from Python.splitGroupedOrders import ordem_tree_grouped

#################################################
# Transform order (quantity and price) in round
# far allocation based on split ration
# it group same price orders and call a auxiliar
# function
#################################################

def ordem_tree(
        ord_quant,  # quantity traded and not allocated
        ord_price,  # price of each trade
        split_ratio,  # target ratio for each fund
        split_min=1):  # Border lot

    # Agrupa precos iguais
    preco_quant = pd.DataFrame({
        'Preco': ord_price,
        'Quant': ord_quant}).groupby('Preco').agg({'Quant': 'sum'})

    ord_quant_aux = np.array(preco_quant['Quant'].values)
    ord_price_aux = np.array(preco_quant.index)
    split_aux = ordem_tree_grouped(ord_quant_aux, ord_price_aux, split_ratio, split_min)

    # Loop para quebrar a ordem antes agrupadas por preco
    split_final = np.zeros((len(split_ratio), len(ord_quant)))

    # Loop para desagrupar a ordem
    for j in range(len(ord_quant)):
        pos_j = np.arange(len(ord_price_aux))[ord_price[j] == ord_price_aux][0]
        quant_j = ord_quant[j]
        for k in range(len(split_ratio)):
            split_final[k, j] = min(quant_j, split_aux[k, pos_j])
            split_aux[k, pos_j] -= split_final[k, j]
            quant_j = int(quant_j - split_final[k, j])

    return split_final
