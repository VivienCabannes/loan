
def remboursement_periodique(taux, periodes):
    return taux * (1 + taux) ** periodes / ((1 + taux) ** periodes - 1)

def cout_credit(taux, periodes):
    return periodes * remboursement_periodique(taux, periodes) - 1
