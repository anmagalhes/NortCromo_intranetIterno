import os
import pygsheets
import pandas as pd

import random
import string
import threading
from threading import Lock
import json

lock = threading.Lock()


# credencias = pygsheets.authorize(
#     service_file=os.getcwd() + "/sistemaNortrCromo_googleConsole.json"
# )

# arquivo = credencias.open_by_url(
#     "https://docs.google.com/spreadsheets/d/15Jyo4qMmVK0JTSB95__JaVJveAOflbS1qR0qNOucEgI/"
# )


def gera_token():
    token = "".join(
        random.choice(string.ascii_letters + string.digits) for _ in range(50)
    )
    return token


def arquivo():
    credencias = pygsheets.authorize(
        service_file=os.getcwd() + "/sistemasuelopro_googleConsole.json"
    )

    arquivo = credencias.open_by_url(
        "https://docs.google.com/spreadsheets/d/15Jyo4qMmVK0JTSB95__JaVJveAOflbS1qR0qNOucEgI/"
    )
    return arquivo


def carregar_dados_gs(aba):
    dados = aba.get_all_values()
    return pd.DataFrame(data=dados[1:], columns=dados[0])


def gerar_ids(aba, quantidade):
    try:
        # Obtenha a sequência atual da coluna de IDs
        coluna_sequencia = aba.get_col(1)[1:]

        # Converta os valores não vazios para inteiros e obtenha o máximo
        coluna_sequencia = [
            int(value) if value.strip() != "" else 0 for value in coluna_sequencia
        ]

        # Calcule o próximo ID na sequência
        max_id = int(max(coluna_sequencia, default=0))
        proximos_ids = list(range(max_id + 1, max_id + 1 + quantidade))

        return proximos_ids

    except Exception as e:
        print("Erro ao gerar IDs. Erro:", str(e))
        return []


def inserir_linhas(aba, valores, ids):
    try:
        with lock:
            # Obtenha a primeira coluna (coluna de IDs)
            coluna_ids = aba.get_col(1)

        # Converta os valores não vazios para inteiros e obtenha o máximo
        ids_existentes = [int(value) for value in coluna_ids[1:] if value.strip()]

        # Obtenha o próximo ID na sequência
        proximo_id = int(max(ids_existentes, default=0)) + 1

        # Converta os IDs para string antes de adicionar à lista de valores
        valores[0] = str(proximo_id)

        # Certifique-se de que todos os valores sejam convertidos para strings
        # antes da inserção
        valores = [str(val) if val is not None else "" for val in valores]

        # Insira uma nova linha com os dados atualizados
        aba.append_table(
            values=[valores],
            start=None,
            end=None,
            dimension="ROWS",
            overwrite=False,
        )

        return True, proximo_id

    except Exception as e:
        print("Erro ao inserir linha. Valores:", valores)
        print("Erro:", str(e))
        return False, None


def verificaSeOUsuarioTemPermissao(usuario, rota):
    # usuario = "tony"
    # rota = "rota1"
    aba_usuarios = arquivo().worksheet_by_title("usuarios")
    coluna1 = aba_usuarios.get_col(1)
    coluna1 = coluna1[1:]
    for i in range(len(coluna1)):
        if coluna1[i] == usuario:
            rotasPermitidas = json.loads(aba_usuarios.get_col(4)[i + 1])
            for rotas in rotasPermitidas:
                if rotas == rota:
                    return True
    return False
