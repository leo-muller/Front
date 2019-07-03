import numpy as np

#################################################
# Recursive function that tries rounding higher or
# lower and return only the best fit
##################################################

def ordem_tree_rec(ord_quant,  # quantity traded and not allocated
                   ord_price,  # price of each trade
                   fund_quant,  # array with quantity for each price already allocated
                   fund_quant_tot,  # total trade quantity for the fund
                   target_price,  # ideal average price
                   split_pos,  # position not split
                   split_min):  # Border lot

    # Amount we still have to allocate
    not_alocated = int(np.round(fund_quant_tot - fund_quant.sum(), 0))
    fund_quant_aux = fund_quant.copy()

    # If fully allocated or only one price to fill the order return the only possible solution
    # else split recursively
    if not_alocated == 0 or split_pos.size == 1:
        fund_quant_aux[split_pos[0]] = not_alocated
        return sum(fund_quant_aux * ord_price) / fund_quant_tot, fund_quant_aux
    else:
        # Rounded quantity
        quant_aux = ord_quant[split_pos[0]] * not_alocated / ord_quant[split_pos].sum()

        # Border lot floor quantity
        quant_aux = np.floor(quant_aux / split_min) * split_min

        # Update non considered positions
        split_pos_aux = split_pos[1:].copy()

        # Call the recursive function to get the best average for floor
        fund_quant_floor = fund_quant_aux.copy()
        fund_quant_floor[split_pos[0]] = quant_aux
        preco_floor, fund_quant_floor = ordem_tree_rec(
            ord_quant, ord_price, fund_quant_floor, fund_quant_tot, target_price, split_pos_aux, split_min)

        # Call the recursive function to get the best average for ceiling
        fund_quant_ceil = fund_quant_aux.copy()
        fund_quant_ceil[split_pos[0]] = min(quant_aux + split_min, ord_quant[split_pos[0]])
        preco_ceil, fund_quant_ceil = ordem_tree_rec(
            ord_quant, ord_price, fund_quant_ceil, fund_quant_tot, target_price, split_pos_aux, split_min)

        # Return smallest error
        if abs(target_price - preco_floor) < abs(target_price - preco_ceil):
            return preco_floor, fund_quant_floor
        else:
            return preco_ceil, fund_quant_ceil

