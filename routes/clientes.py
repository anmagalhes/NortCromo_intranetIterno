from flask import Blueprint, render_template, jsonify, request, redirect, url_for
import pandas as pd
import os
import pygsheets
import datetime
from routes.funcoesGerais import *
from routes.cache_manager import obter_dados_clientes 

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

clientes = Blueprint(
    "clientes",
    __name__,
    static_folder="static",
    template_folder="templates",
)


# Variáveis globais para armazenar os DataFrames  - BIBLIOTECA PANDAS X GOOGLESHEET
df_cliente = None

@clientes.route("/adiciona_cliente", methods=["POST"])
def clientes_f():
    try:
        o_que_escrever = request.form["o_que_escrever"]

        aba = arquivo().worksheet_by_title("base_de_dados")

        coluna1 = aba.get_col(1)
        coluna1 = coluna1[1:]  # tirar o cabeçalho

        meu_id = int(max(coluna1)) + 1

        # Adicione a nova coluna de "Nome_Usuario" ao seu mapeamento e obtenha
        # o nome de usuário
        nome_usuario = request.cookies.get("userName")

        # Adicione a nova coluna de "Data_Hora" com a data e hora atual
        data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        o_que_escrever = [str(meu_id), o_que_escrever, nome_usuario, data_hora]

        # Adicione a nova coluna "Nome_Usuario" e "Data_Hora" ao seu mapeamento
        mapeamento_cliente = {
            "Id_cliente": "id_cliente",
            "Nome_cliente": "nome_cliente",
            "Nome_Usuario": "nome_usuario",  # Adicione esta linha
            "Data_Hora": "data_hora",  # Adicione esta linha
        }

        # Mapeie os campos do frontend para as colunas do Google Sheets
        valores = {}
        for campo_frontend, coluna_sheet in mapeamento_cliente.items():
            if campo_frontend == "Nome_Usuario":
                valores[coluna_sheet] = nome_usuario
            elif campo_frontend == "Data_Hora":
                valores[coluna_sheet] = data_hora
            else:
                # Verifique se o campo do frontend existe antes de atribuir
                if campo_frontend in request.form:
                    valores[coluna_sheet] = request.form[campo_frontend]
                else:
                    valores[coluna_sheet] = ""

        # Converta os valores em uma lista antes de inseri-los
        valores_list = list(valores.values())

        # Insira uma nova linha com os dados atualizados
        aba.append_table(
            values=[valores_list],
            start="A1",
            end=None,
            dimension="ROWS",
            overwrite=False,
        )

        return jsonify(retorno="Tudo Certo")

    except Exception as e:
        return jsonify(retorno="Algo deu errado: " + str(e))
    
# Para selecionar as lista de clientes
@clientes.route("/selecionar_clientes_cache", methods=["POST"])
def selecionar_clientes_cache_f():
    try:
        dados_clientes = obter_dados_clientes()
        return jsonify({"retorno": dados_clientes})

    except Exception as e:
        return jsonify({"error": f"Erro ao carregar clientes: {str(e)}"})
    

@clientes.route("/selecionar_clientes", methods=["POST"])
def selecionar_clientes_f():
    try:
        clientes_aba = arquivo().worksheet_by_title("Cliente")
        dados_clientes = clientes_aba.get_all_values()
        df_clientes = pd.DataFrame(data=dados_clientes[1:], columns=dados_clientes[0])

        # Seleciona apenas as colunas desejadas
        colunas_desejadas = ["ID", "Nome_cliente"]
        df_selecionado = df_clientes[colunas_desejadas]

        # Filtra os registros onde a coluna "Nome_cliente" é diferente de vazio ou nulo
        clientes_ok = df_selecionado[df_selecionado["Nome_cliente"].notna()]

        # Converte o DataFrame resultante para um dicionário
        clientes_lista = clientes_ok.to_dict(orient="records")

        print("Clientes carregados com sucesso:", clientes_lista)
        return jsonify({"retorno": clientes_lista})

    except Exception as e:
        return jsonify({"error": f"Erro ao carregar clientes: {str(e)}"})
    


@clientes.route("/selecionar_clientes", methods=["POST"])
def selecionar_clientes_teste_f():
    try:
        # Selecione a aba correta (você já deve ter esse código)
        aba = arquivo.worksheet_by_title("Cliente")

        # Obtenha todos os valores da planilha
        dados_da_planilha = aba.get_all_values()

        # A primeira linha contém os nomes das colunas, que serão usados para
        # mapeamento
        colunas = dados_da_planilha[0]

        # Os dados começam da segunda linha em diante
        dados = dados_da_planilha[1:]

        # Mapeamento de colunas (mesmo mapeamento usado na função de adicionar
        # funcionário)
        mapeamento = {
            "id_Obra": "id_Obra",
            "obra_nome": "obra_nome",
            "Status": "Status",
        }

        # Inicialize uma lista para armazenar os dados mapeados
        dados_mapeados = []

        # Itere pelas linhas da planilha
        for linha in dados:
            obra = {
                mapeamento[coluna]: valor for coluna, valor in zip(mapeamento, linha)
            }
            if obra["Status"].upper() == "OK":  # Verifica se o status é "OK"
                dados_mapeados.append(obra)

        # print("tony", dados_mapeados)
        # Retorne os dados mapeados como JSON
        return jsonify(retorno=dados_mapeados)
    except Exception as e:
        return jsonify(retorno="Algo deu errado: " + str(e))


