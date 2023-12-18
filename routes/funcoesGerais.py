import os
import pygsheets
import pandas as pd

import random
import string
import threading
from threading import Lock
import json

lock = threading.Lock()


from flask import Blueprint, render_template, jsonify, request, redirect, url_for
import pandas as pd
import os
import pygsheets
import datetime
from routes.funcoesGerais import *

import threading
import traceback

import re
import json
from flask import send_file
import random
import string
import numpy as np
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from googleapiclient.discovery import build
from threading import Lock
from functools import lru_cache
from datetime import datetime, timedelta
from cachetools import cached, TTLCache

from google.auth.transport.requests import Request
from google.auth.credentials import AnonymousCredentials
from google.auth import impersonated_credentials
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from google.oauth2.service_account import Credentials
from io import BytesIO
from google.oauth2 import service_account
from docx import Document
from googleapiclient.http import MediaIoBaseUpload
from docx.shared import Pt
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from googleapiclient.errors import HttpError

from googleapiclient import discovery
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

import io

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
    # Construa o caminho absoluto para o arquivo de credenciais
    caminho_credenciais = os.path.join(os.getcwd(), "sistemaNortrCromo_googleConsole.json")

    # Verifique se o arquivo de credenciais existe
    if not os.path.exists(caminho_credenciais):
        raise FileNotFoundError(f"O arquivo de credenciais não foi encontrado em: {caminho_credenciais}")

    # Autorize o acesso ao Google Sheets
    credenciais = pygsheets.authorize(service_file=caminho_credenciais)

    # Abra a planilha pelo URL (ou você pode usar o método `open` diretamente se tiver o ID da planilha)
    arquivo = credenciais.open_by_url(
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

# Função para converter a data do frontend para o mesmo formato do DataFrame
def converter_data_frontend(data_frontend):
    # Supondo que a data do frontend esteja em formato 'DD/MM/YYYY'
    return pd.to_datetime(data_frontend, format="%d/%m/%Y")

