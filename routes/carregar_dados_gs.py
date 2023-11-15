import pandas as pd


def carregar_dados_gs(aba):
    dados = aba.get_all_values()
    return pd.DataFrame(data=dados[1:], columns=dados[0])
