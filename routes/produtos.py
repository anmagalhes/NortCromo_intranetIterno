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

produtos = Blueprint(
    "produtos",
    __name__,
    static_folder="static",
    template_folder="templates",
)

# Variáveis globais para armazenar os DataFrames  - BIBLIOTECA PANDAS X GOOGLESHEET
df_produto = None

@produtos.route("/adiciona_produto", methods=["POST"])
def produtos_f():
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


@produtos.route("/selecionar_produtos", methods=["POST"])
def selecionar_produtos_f():
    try:
        produtos_aba = arquivo().worksheet_by_title("Produto")
        dados_produtos = produtos_aba.get_all_values()
        df_produtos = pd.DataFrame(data=dados_produtos[1:], columns=dados_produtos[0])

        # Seleciona apenas as colunas desejadas
        colunas_desejadas_produtos = ["Cod_Produto", "nome_produto", "idGrupo", "idoperacaoServico", "ID_Componente", "ID_PostoTrabalho"]
        df_selecionado_produtos = df_produtos[colunas_desejadas_produtos]

        # Filtra os registros onde a coluna "Produto" é diferente de vazio ou nulo
        produtos_ok = df_selecionado_produtos[df_selecionado_produtos["nome_produto"].notna()]

        # Ordena os produtos pelo nome do produto
        produtos_ok = produtos_ok.sort_values(by="nome_produto")

        # Converte o DataFrame resultante para um dicionário
        produtos_lista = produtos_ok.to_dict(orient="records")

         #print("Produtos carregados com sucesso:", produtos_lista)
        return jsonify({"retorno": produtos_lista})

    except Exception as e:
        return jsonify({"error": f"Erro ao carregar produtos: {str(e)}"})   
    
@produtos.route("/selecionar_novos_produtos", methods=["POST"])
def selecionar_novos_produtos():
    try:
        # Carrega a folha Produto
        produtos_aba = arquivo().worksheet_by_title("Produto")
        dados_produtos = produtos_aba.get_all_values()
        df_produtos = pd.DataFrame(data=dados_produtos[1:], columns=dados_produtos[0])

        # Filtra os registros onde a coluna "Cod_Produto" não é nula ou vazia
        novos_produtos = df_produtos[df_produtos["Cod_Produto"].notna() & (df_produtos["Cod_Produto"] != "")]

        # Pega os IDs dos grupos únicos
        ids_grupos_unicos = novos_produtos["idGrupo"].unique()

        # Carrega a folha Grupo Produto
        grupos_aba = arquivo().worksheet_by_title("Grupo Produto")
        dados_grupos = grupos_aba.get_all_values()
        df_grupos = pd.DataFrame(data=dados_grupos[1:], columns=dados_grupos[0])

        # Filtra os grupos usando os IDs únicos
        grupos_selecionados = df_grupos[df_grupos["Id"].isin(ids_grupos_unicos)][["Id", "nome"]]

        # Realiza o merge com os produtos
        novos_produtos = pd.merge(novos_produtos, grupos_selecionados, left_on="idGrupo", right_on="Id", how="left")

        # Pega os IDs das operações únicas
        ids_operacoes_unicas = novos_produtos["idoperacaoServico"].unique()

        # Carrega a folha Operacao
        operacoes_aba = arquivo().worksheet_by_title("Operacao")
        dados_operacoes = operacoes_aba.get_all_values()
        df_operacoes = pd.DataFrame(data=dados_operacoes[1:], columns=dados_operacoes[0])

        # Filtra as operações usando os IDs únicos
        operacoes_selecionadas = df_operacoes[df_operacoes["Id"].isin(ids_operacoes_unicas)][["Id", "grupo_Processo", "nome"]]

        # Renomeia a coluna "nome" localmente para "nome_operacao"
        operacoes_selecionadas = operacoes_selecionadas.rename(columns={"nome": "nome_operacao"})

        # Preenche os valores nulos em "grupo_Processo" e "nome_operacao"
        operacoes_selecionadas["grupo_Processo"] = operacoes_selecionadas["grupo_Processo"].fillna('')
        operacoes_selecionadas["nome_operacao"] = operacoes_selecionadas["nome_operacao"].fillna('')

        # Pega os IDs das componetes únicas
        ids_componetes_unicas = novos_produtos["ID_Componente"].unique()

        # Carrega a folha Componente
        componetes_aba = arquivo().worksheet_by_title("Componente")
        dados_componetes = componetes_aba.get_all_values()
        df_componetes = pd.DataFrame(data=dados_componetes[1:], columns=dados_componetes[0])

        # Filtra as componentes usando os IDs únicos
        componetes_selecionadas = df_componetes[df_componetes["ID"].isin(ids_componetes_unicas)][["ID", "nome_Componente"]]

        # Preenche os valores nulos em "nome_Componente"
        componetes_selecionadas["nome_Componente"] = componetes_selecionadas["nome_Componente"].fillna('')

        # Converta o DataFrame original para um dicionário
        novos_produtos_dict = novos_produtos.to_dict(orient="records")

        print('novos_produtos_dict', novos_produtos_dict)

        # Adiciona os resultados à resposta JSON
        return jsonify({
            "novos_produtos": novos_produtos_dict,
        })

    except ValueError as ve:
        return jsonify({"error": str(ve)})

    except Exception as e:
        print(f"Erro ao carregar novos produtos: {str(e)}")
        return jsonify({"error": f"Erro ao carregar novos produtos: {str(e)}", "traceback": traceback.format_exc()})
