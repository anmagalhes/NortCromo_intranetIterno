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

        # Verifica se todos os valores na coluna "ID" são numéricos antes de calcular o máximo
        if recebimentos_ok["ID"].str.isnumeric().all():
            # Converte a coluna "ID" para numérica e calcula o último número na coluna "ID" e incrementa 1
            ultimo_id = recebimentos_ok["ID"].astype(int).max()
            novo_id_recebimento = ultimo_id + 1 if not pd.isnull(ultimo_id) else 1
        else:
            # Se houver valores não numéricos, define novo_id_recebimento como 1
            novo_id_recebimento = 1

        # Ordena os produtos pelo nome do produto
        recebimentos_ok = recebimentos_ok.sort_values(by="ID_Ordem")

        # Converte o DataFrame resultante, o contador, o valor_seg e o novo_id_recebimento para um dicionário
        recebimentos_lista = recebimentos_ok.to_dict(orient="records")

        # Converte o novo_id_recebimento para um tipo Python nativo antes de retornar a resposta JSON
        novo_id_recebimento = int(novo_id_recebimento)

        # Adiciona o contador, o valor_seg e o novo_id_recebimento à resposta JSON
        resposta_json = {"retorno": recebimentos_lista, "contador_novo": contador_novo, "valor_seg": valor_seg, "novo_id_recebimento": novo_id_recebimento}

        return jsonify(resposta_json)

    except Exception as e:
        return jsonify({"error": f"Erro ao carregar recebimentos: {str(e)}"})
    
@recebimentos.route("/selecionar_recebimentos_especificos", methods=["POST"])
def selecionar_recebimentos_especificos_f():
    try:
        # Obter o período inicial e final do corpo da requisição
        data_inicial_frontend = request.json["data_inicial"]
        data_final_frontend = request.json["data_final"]
 
        # Convertendo as datas do frontend
        data_inicial = converter_data_frontend(data_inicial_frontend)
        data_final = converter_data_frontend(data_final_frontend)

        recebimentos_aba = arquivo().worksheet_by_title("Recebimento_v2")
        dados_recebimentos = recebimentos_aba.get_all_values()
        df_recebimentos = pd.DataFrame(data=dados_recebimentos[1:], columns=dados_recebimentos[0])

        # Converte a coluna "DataRec_OrdemServiços" para o tipo datetime considerando o formato dd/mm/aaaa
        df_recebimentos["DataRec_OrdemServiços"] = pd.to_datetime(df_recebimentos["DataRec_OrdemServiços"], format="%d/%m/%Y", errors='coerce')
        # Substitui os valores NaN na coluna "DataRec_OrdemServiços" por uma string vazia
        df_recebimentos["DataRec_OrdemServiços"] = df_recebimentos["DataRec_OrdemServiços"].fillna('')

        # Filtra os registros com base no período fornecido
        recebimentos_especificos = df_recebimentos[(df_recebimentos["DataRec_OrdemServiços"] >= data_inicial) & (df_recebimentos["DataRec_OrdemServiços"] <= data_final) & (df_recebimentos["Status_Ordem"] != "FINALIZADO")]
        # Filtra os registros onde a coluna "DataRec_OrdemServiços" é maior que a data de hoje menos 15 dias
         #data_limite = datetime.now() - timedelta(days=215)
        # recebimentos_especificos = df_recebimentos[(df_recebimentos["DataRec_OrdemServiços"] >= data_limite) & (df_recebimentos["Status_Ordem"] != "finalizado")]
        # Ordena os produtos pelo nome do produto
        recebimentos_especificos = recebimentos_especificos.sort_values(by="ID_Ordem")

        # Pega os IDs dos clientes únicos
        ids_clientes_unicos = recebimentos_especificos["ID"].unique()

        # Carrega a folha Cliente
        clientes_aba = arquivo().worksheet_by_title("Cliente")
        dados_clientes = clientes_aba.get_all_values()
        df_clientes = pd.DataFrame(data=dados_clientes[1:], columns=dados_clientes[0])

        # Filtra os clientes usando os IDs únicos
        clientes_selecionados = df_clientes[df_clientes["ID"].isin(ids_clientes_unicos)][["ID", "Nome_cliente"]]

         #print("Clientes Selecionados:")
         #print(clientes_selecionados)

        # Realiza o merge com os recebimentos
        recebimentos_especificos = pd.merge(recebimentos_especificos, clientes_selecionados, left_on="ID", right_on="ID", how="left")
    
        # Adiciona a coluna Nome_cliente ao DataFrame recebimentos_especificos
        # após o merge
        recebimentos_especificos["Nome_cliente"] = recebimentos_especificos["Nome_cliente"].fillna('')

        # Pega os IDs dos produtos únicos
        ids_produtos_unicos = recebimentos_especificos["Cod_Produto"].unique()

        # Carrega a folha Produto
        produtos_aba = arquivo().worksheet_by_title("Produto")
        dados_produtos = produtos_aba.get_all_values()
        df_produtos = pd.DataFrame(data=dados_produtos[1:], columns=dados_produtos[0])

        # Filtra os produtos usando os IDs únicos
        produtos_selecionados = df_produtos[df_produtos["Cod_Produto"].isin(ids_produtos_unicos)][["Cod_Produto", "nome_produto", "idGrupo", "idoperacaoServico", "ID_Componente", "ID_PostoTrabalho"]]

         #print("Produtos Selecionados:")
         #print(produtos_selecionados)

        # Realiza o merge com os recebimentos
        recebimentos_especificos = pd.merge(recebimentos_especificos, produtos_selecionados, on="Cod_Produto", how="left")

        # Pega os IDs dos grupos únicos
        ids_grupos_unicos = recebimentos_especificos["idGrupo"].unique()

        # Carrega a folha Grupo Produto
        grupos_aba = arquivo().worksheet_by_title("Grupo Produto")
        dados_grupos = grupos_aba.get_all_values()
        df_grupos = pd.DataFrame(data=dados_grupos[1:], columns=dados_grupos[0])

        # Filtra os grupos usando os IDs únicos
        grupos_selecionados = df_grupos[df_grupos["Id"].isin(ids_grupos_unicos)][["Id", "nome"]]

         #print("Grupos Selecionados:")
         #print(grupos_selecionados)

         # Realiza o merge com os recebimentos
        recebimentos_especificos = pd.merge(recebimentos_especificos, grupos_selecionados, left_on="idGrupo", right_on="Id", how="left")

        # Pega os IDs das operações únicas
        ids_operacoes_unicas = recebimentos_especificos["idoperacaoServico"].unique()

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

         #print("Operações Selecionadas:")
         #print(operacoes_selecionadas)
   
        # Pega os IDs das componetes únicas
        ids_componetes_unicas = recebimentos_especificos["ID_Componente"].unique()

        # Carrega a folha Operacao
        componetes_aba = arquivo().worksheet_by_title("Componente")
        dados_componetes = componetes_aba.get_all_values()
        df_componetes = pd.DataFrame(data=dados_componetes[1:], columns=dados_componetes[0])

        # Filtra as operações usando os IDs únicos
        componetes_selecionadas = df_componetes[df_componetes["ID"].isin(ids_componetes_unicas)][["ID", "nome_Componente"]]

        # Preenche os valores nulos em "nome_operacao"
        componetes_selecionadas["nome_Componente"] = componetes_selecionadas["nome_Componente"].fillna('')


        # Imprime as colunas antes da conversão para dicionário
        print("Colunas em recebimentos_especificos:")
        print(recebimentos_especificos.columns)
        # Converte o DataFrame resultante para um dicionário
        recebimentos_especificos_lista = recebimentos_especificos.fillna('').to_dict(orient="records")

        # Adiciona os resultados à resposta JSON
        resposta_json = {"retorno_especifico": recebimentos_especificos_lista}

        return jsonify(resposta_json)

    except Exception as e:
        print(f"Erro ao carregar recebimentos específicos: {str(e)}")
        return jsonify({"error": f"Erro ao carregar recebimentos específicos: {str(e)}", "traceback": traceback.format_exc()})


@recebimentos.route("/numeroControles_Unicos", methods=["POST"])
def numeroControles_Unicos_f():
    try:
        recebimentos_aba = arquivo().worksheet_by_title("Recebimento_v2")
        dados_recebimentos = recebimentos_aba.get_all_values()
        df_recebimentos = pd.DataFrame(data=dados_recebimentos[1:], columns=dados_recebimentos[0])

        # Seleciona apenas as colunas desejadas
        colunas_desejadas = ["ID", "ID_Ordem"]
        df_selecionado = df_recebimentos[colunas_desejadas]
        
        # Filtra os registros onde a coluna "ID_Ordem" é diferente de nulo e diferente de vazio
        recebimentos_ok = df_recebimentos[df_selecionado["ID_Ordem"].notna() & (df_selecionado["ID_Ordem"] != "")]

        # Filtra os registros onde a coluna "Nome_cliente" é diferente de vazio ou nulo
        recebimentos_ok = df_selecionado[df_selecionado["ID"].notna()]

        # Converte o DataFrame resultante para um dicionário
        recebimentos_lista =recebimentos_ok.to_dict(orient="records")

        # print("Clientes carregados com sucesso:", clientes_lista)
        return jsonify({"retorno_especifico": recebimentos_lista})
    
    except Exception as e:
        return jsonify({"error": f"Erro ao carregar clientes: {str(e)}"})
    
@recebimentos.route("/numeroControles_Unicos_Filtros", methods=["POST"])
def numeroControles_Unicos_Filtros_f():
    try:
        # Obter o período inicial e final do corpo da requisição
        data_inicial_frontend = request.json["data_inicial"]
        data_final_frontend = request.json["data_final"]
 
        # Convertendo as datas do frontend
        data_inicial = converter_data_frontend(data_inicial_frontend)
        data_final = converter_data_frontend(data_final_frontend)

        recebimentos_aba = arquivo().worksheet_by_title("Recebimento_v2")
        dados_recebimentos = recebimentos_aba.get_all_values()
        df_recebimentos = pd.DataFrame(data=dados_recebimentos[1:], columns=dados_recebimentos[0])
             
        # Seleciona apenas as colunas desejadas
        colunas_desejadas = ["ID", "ID_Ordem, DataRec_OrdemServiços"]
        df_selecionado = df_recebimentos[colunas_desejadas]

        # Converte a coluna "DataRec_OrdemServiços" para o tipo datetime considerando o formato dd/mm/aaaa
        df_recebimentos["DataRec_OrdemServiços"] = pd.to_datetime(df_recebimentos["DataRec_OrdemServiços"], format="%d/%m/%Y", errors='coerce')
        # Substitui os valores NaN na coluna "DataRec_OrdemServiços" por uma string vazia
        df_recebimentos["DataRec_OrdemServiços"] = df_recebimentos["DataRec_OrdemServiços"].fillna('')

        # Filtra os registros com base no período fornecido
        df_selecionado  = df_recebimentos[(df_recebimentos["DataRec_OrdemServiços"] >= data_inicial) & (df_recebimentos["DataRec_OrdemServiços"] <= data_final) & (df_selecionado["ID_Ordem"].notna()) & (df_selecionado["ID_Ordem"] != "")]
        
        # Filtra os registros onde a coluna "Recebimento" é diferente de vazio ou nulo
        recebimentos_ok = df_selecionado[df_selecionado["ID"].notna()]

        # Converte o DataFrame resultante para um dicionário
        recebimentos_lista2 =recebimentos_ok.to_dict(orient="records")

        # print("Clientes carregados com sucesso:", clientes_lista)
        return jsonify({"retorno_especifico": recebimentos_lista2})
    
    except Exception as e:
        return jsonify({"error": f"Erro ao carregar clientes: {str(e)}"})
