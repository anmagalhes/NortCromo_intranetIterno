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

recebimentos = Blueprint(
    "recebimentos",
    __name__,
    static_folder="static",
    template_folder="templates",
)

# Variáveis globais para armazenar os DataFrames  - BIBLIOTECA PANDAS X GOOGLESHEET
df_recebimentos = None



@recebimentos.route("/selecionar_recebimentos", methods=["POST"])
def selecionar_recebimentos_f():
    try:
        recebimentos_aba = arquivo().worksheet_by_title("Recebimento_v2")
        dados_recebimentos = recebimentos_aba.get_all_values()
        df_recebimentos = pd.DataFrame(data=dados_recebimentos[1:], columns=dados_recebimentos[0])
        
        # Seleciona apenas as colunas desejadas
        colunas_desejadas_recebimentos = ["ID", "ID_Ordem", "DataRec_OrdemServiços", "ID_cliente", "NotaInterna", "TipoOrdem"]
        df_selecionado_recebimentos = df_recebimentos[colunas_desejadas_recebimentos]
        
        # Filtra os registros onde a coluna "ID_Ordem" é diferente de nulo e diferente de vazio
        recebimentos_ok = df_selecionado_recebimentos[df_selecionado_recebimentos["ID_Ordem"].notna() & (df_selecionado_recebimentos["ID_Ordem"] != "")]

        # Conta quantas linhas têm na coluna "TipoOrdem" com nome "NOVO"
        contador_novo = recebimentos_ok[recebimentos_ok["TipoOrdem"] == "NOVO"].shape[0]

        # Calcular o valor_seg com base no contador_novo
        valor_seg = (
            f"0001-{str(datetime.now().year)[-2:]}"
            if contador_novo < 2
            else f"{contador_novo + 1:04d}-{str(datetime.now().year)[-2:]}"
        )

        # Ordena os produtos pelo nome do produto
        recebimentos_ok = recebimentos_ok.sort_values(by="ID_Ordem")

        # Converte o DataFrame resultante e o contador para um dicionário
        recebimentos_lista = recebimentos_ok.to_dict(orient="records")

        # Adiciona o contador e o valor_seg à resposta JSON
        resposta_json = {"retorno": recebimentos_lista, "contador_novo": contador_novo, "valor_seg": valor_seg}

        return jsonify(resposta_json)

    except Exception as e:
        return jsonify({"error": f"Erro ao carregar recebimentos: {str(e)}"})