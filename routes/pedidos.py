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

pedidos = Blueprint(
    "pedidos",
    __name__,
    static_folder="static",
    template_folder="templates",
)

# Variáveis globais para armazenar os DataFrames  - BIBLIOTECA PANDAS X GOOGLESHEET
df_pedidos = None

pedidos_df = pd.DataFrame(columns=["ID", "Cliente", "Produto", "Quantidade", "Status"])

@pedidos.route("/criar_pedido", methods=["POST"])
def criar_pedido():
    try:
        global pedidos_df

        # Simula a criação de um novo pedido
        novo_pedido = {
            "ID": pedidos_df["ID"].max() + 1 if not pedidos_df.empty else 1,
            "Cliente": request.form.get("cliente"),
            "Produto": request.form.get("produto"),
            "Quantidade": request.form.get("quantidade"),
            "Status": "Em Processo"
        }

        # Adiciona o novo pedido ao DataFrame
        pedidos_df = pedidos_df.append(novo_pedido, ignore_index=True)

        # Atualiza o DataFrame
        pedidos_df.to_csv("pedidos.csv", index=False)

        return jsonify({"status": "Pedido criado com sucesso", "pedido": novo_pedido})

    except Exception as e:
        return jsonify({"error": f"Erro ao criar pedido: {str(e)}"})

@pedidos.route("/selecionar_pedidos", methods=["GET"])
def selecionar_pedidos():
    try:
        global pedidos_df

        # Carrega os pedidos do DataFrame
        pedidos_df = pd.read_csv("pedidos.csv") if pd.DataFrame().empty else pedidos_df

        # Ordena os pedidos por ID
        pedidos_df = pedidos_df.sort_values(by="ID")

        # Converte o DataFrame resultante para um dicionário
        pedidos_lista = pedidos_df.to_dict(orient="records")

        return jsonify({"pedidos": pedidos_lista})

    except Exception as e:
        return jsonify({"error": f"Erro ao carregar pedidos: {str(e)}"})


