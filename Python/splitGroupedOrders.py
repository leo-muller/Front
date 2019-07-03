import numpy as np
from Python.splitRecursiveFunc import ordem_tree_rec

#################################################
# Funcao que define prioridade na quebra de ordens
# ord_quant -> Quantidade em cada preco
# ord_price -> Preco de cada ordem
# split_ration -> Proporcao dividida
# split_min -> Lote minimo
#################################################

def ordem_tree_grouped(ord_quant, ord_price, split_ratio, split_min=1):
    split_order = split_ratio.argsort()  # First smaller orders
    split_ratio_aux = split_ratio.copy()
    fund_n = split_ratio.size
    ord_n = ord_quant.size
    fund_ord_all = np.empty((fund_n, ord_n))
    ord_quant_aux = ord_quant.copy()
    max_tree_levels = 4  # Number of position we will try recursively

    for i in split_order[:-1]:
        ord_quant_tot = ord_quant_aux.sum()
        fund_quant_tot = int(np.round(ord_quant_tot * split_ratio_aux[i] / split_min, 0) * split_min)
        if fund_quant_tot > 0:
            preco_med = sum(ord_price * ord_quant_aux) / ord_quant_tot
            fund_quant = fund_quant_tot * ord_quant_aux / ord_quant_tot
            fund_quant_round = np.round(fund_quant / split_min, 0) * split_min

            # Change only 'max_tree_levels' biggest impact of rounding
            preco_erro = abs(ord_price * (fund_quant - fund_quant_round))
            split_pos = preco_erro.argsort()
            split_pos = split_pos[-max_tree_levels:]
            split_pos = split_pos[ord_quant_aux[split_pos] > 0]  # Avoid zeros
            fund_quant_round[split_pos] = 0

            preco_aux, fund_aux = ordem_tree_rec(
                ord_quant_aux, ord_price, fund_quant_round, fund_quant_tot, preco_med, split_pos, split_min)

            fund_ord_all[i, ] = fund_aux

            # Update variables
            ord_quant_aux = ord_quant_aux - fund_aux
        else:
            fund_ord_all[i,] = 0

        split_ratio_aux[i] = 0
        split_ratio_aux = split_ratio_aux / split_ratio_aux.sum()

    fund_ord_all[split_order[-1],] = ord_quant_aux
    return np.array(fund_ord_all)