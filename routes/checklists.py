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

checklists = Blueprint(
    "checklists",
    __name__,
    static_folder="static",
    template_folder="templates",
)

# Variáveis globais para armazenar os DataFrames  - BIBLIOTECA PANDAS X GOOGLESHEET
df_checklists = None

    
@checklists.route("/selecionar_checklists_especificos", methods=["POST"])
def selecionar_checklists_especificos_f():
    try:
 
        checklists_aba = arquivo().worksheet_by_title("ChecklistRecebimento2")
        dados_checklists = checklists_aba.get_all_values()
        df_checklists = pd.DataFrame(data=dados_checklists[1:], columns=dados_checklists[0])
        
        # Filtra os registros com base no período fornecido
        checklists_especificos = df_checklists[(df_checklists["Status_Checklist"] != "FINALIZADO") & (df_checklists["ID_Checklist"].notna()) & (df_checklists["ID_Checklist"] != "0") & (df_checklists["ID_Checklist"] != "")]
    
        # Ordena os produtos pelo numero Ordem
        checklists_especificos = checklists_especificos.sort_values(by="ID_Recebimento")

        # Pega os IDs dos Ordem Recebimento únicos
        ids_recebimentos_unicos = checklists_especificos["ID_Recebimento"].unique()
        
        print('ids_recebimentos_unicos', ids_recebimentos_unicos)
        
        recebimentos_aba = arquivo().worksheet_by_title("Recebimento_v2")
        dados_recebimentos = recebimentos_aba.get_all_values()
        df_recebimentos = pd.DataFrame(data=dados_recebimentos[1:], columns=dados_recebimentos[0])

        # Filtra os Recebimento usando os IDs únicos
        recebimento_selecionados = df_recebimentos[df_recebimentos["ID_Ordem"].isin(ids_recebimentos_unicos)][["ID", "ID_Ordem", "DataRec_OrdemServiços"]]

        # Realiza o merge com os checklists
        checklists_especificos = pd.merge(checklists_especificos, recebimento_selecionados, left_on="ID_Recebimento", right_on="ID", how="left")

        # Converte a coluna "DataRec_OrdemServiços" para o tipo datetime considerando o formato dd/mm/aaaa
        df_recebimentos["DataRec_OrdemServiços"] = pd.to_datetime(df_recebimentos["DataRec_OrdemServiços"], format="%d/%m/%Y", errors='coerce')
        # Substitui os valores NaN na coluna "DataRec_OrdemServiços" por uma string vazia
        df_recebimentos["DataRec_OrdemServiços"] = df_recebimentos["DataRec_OrdemServiços"].fillna('')
    
    
        # Adiciona a coluna Nome_cliente ao DataFrame checklists_especificos
        # após o merge
        checklists_especificos["ID_Ordem"] = checklists_especificos["ID_Ordem"].fillna('')

        # Pega os IDs dos Ordem Recebimento únicos
        ids_clientes_unicos = checklists_especificos["ID"].unique()

        # Carrega a folha Cliente
        clientes_aba = arquivo().worksheet_by_title("Cliente")
        dados_clientes = clientes_aba.get_all_values()
        df_clientes = pd.DataFrame(data=dados_clientes[1:], columns=dados_clientes[0])

        # Filtra os clientes usando os IDs únicos
        clientes_selecionados = df_clientes[df_clientes["ID"].isin(ids_clientes_unicos)][["ID", "Nome_cliente"]]

         #print("Clientes Selecionados:")
         #print(clientes_selecionados)

        # Realiza o merge com os checklists
        checklists_especificos = pd.merge(checklists_especificos, clientes_selecionados, left_on="ID", right_on="ID", how="left")
    
        # Adiciona a coluna Nome_cliente ao DataFrame checklists_especificos
        # após o merge
        checklists_especificos["Nome_cliente"] = checklists_especificos["Nome_cliente"].fillna('')

        # Pega os IDs dos produtos únicos
        ids_produtos_unicos = checklists_especificos["Cod_Produto"].unique()

        # Carrega a folha Produto
        produtos_aba = arquivo().worksheet_by_title("Produto")
        dados_produtos = produtos_aba.get_all_values()
        df_produtos = pd.DataFrame(data=dados_produtos[1:], columns=dados_produtos[0])

        # Filtra os produtos usando os IDs únicos
        produtos_selecionados = df_produtos[df_produtos["Cod_Produto"].isin(ids_produtos_unicos)][["Cod_Produto", "nome_produto", "idGrupo", "idoperacaoServico", "ID_Componente", "ID_PostoTrabalho"]]

         #print("Produtos Selecionados:")
         #print(produtos_selecionados)

        # Realiza o merge com os checklists
        checklists_especificos = pd.merge(checklists_especificos, produtos_selecionados, on="Cod_Produto", how="left")

        # Pega os IDs dos grupos únicos
        ids_grupos_unicos = checklists_especificos["idGrupo"].unique()

        # Carrega a folha Grupo Produto
        grupos_aba = arquivo().worksheet_by_title("Grupo Produto")
        dados_grupos = grupos_aba.get_all_values()
        df_grupos = pd.DataFrame(data=dados_grupos[1:], columns=dados_grupos[0])

        # Filtra os grupos usando os IDs únicos
        grupos_selecionados = df_grupos[df_grupos["Id"].isin(ids_grupos_unicos)][["Id", "nome"]]

         #print("Grupos Selecionados:")
         #print(grupos_selecionados)

         # Realiza o merge com os checklists
        checklists_especificos = pd.merge(checklists_especificos, grupos_selecionados, left_on="idGrupo", right_on="Id", how="left")

        # Pega os IDs das operações únicas
        ids_operacoes_unicas = checklists_especificos["idoperacaoServico"].unique()

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
        ids_componetes_unicas = checklists_especificos["ID_Componente"].unique()

        # Carrega a folha Operacao
        componetes_aba = arquivo().worksheet_by_title("Componente")
        dados_componetes = componetes_aba.get_all_values()
        df_componetes = pd.DataFrame(data=dados_componetes[1:], columns=dados_componetes[0])

        # Filtra as operações usando os IDs únicos
        componetes_selecionadas = df_componetes[df_componetes["ID"].isin(ids_componetes_unicas)][["ID", "nome_Componente"]]

        # Preenche os valores nulos em "nome_operacao"
        componetes_selecionadas["nome_Componente"] = componetes_selecionadas["nome_Componente"].fillna('')


        # Imprime as colunas antes da conversão para dicionário
        #print("Colunas em checklists_especificos:")
        #print(checklists_especificos.columns)
        # Converte o DataFrame resultante para um dicionário
        checklists_especificos_lista = checklists_especificos.fillna('').to_dict(orient="records")

        # Adiciona os resultados à resposta JSON
        resposta_json = {"retorno_especifico": checklists_especificos_lista}

        return jsonify(resposta_json)

    except Exception as e:
        print(f"Erro ao carregar checklists específicos: {str(e)}")
        return jsonify({"error": f"Erro ao carregar checklists específicos: {str(e)}", "traceback": traceback.format_exc()})


@checklists.route("/selecionar_checklists_especificos_Recebimento", methods=["POST"])
def selecionar_checklists_especificos_Recebimento_f():
    try:
        
        # Obter o período inicial e final do corpo da requisição
        id_recebimento_Filtrado_frontend = request.json["ID_Recebimento"]
        
        checklists_aba = arquivo().worksheet_by_title("ChecklistRecebimento2")
        dados_checklists = checklists_aba.get_all_values()
        df_checklists = pd.DataFrame(data=dados_checklists[1:], columns=dados_checklists[0])
        
        # Filtra os registros com base no ID_Recebimento fornecido
        checklists_especificos = df_checklists[df_checklists["ID_Recebimento"] == id_recebimento_Filtrado_frontend]
        
        # Ordena os produtos pelo numero Ordem
        checklists_especificos = checklists_especificos.sort_values(by="ID_Recebimento")

        # Pega os IDs dos Ordem Recebimento únicos
        ids_recebimentos_unicos = checklists_especificos["ID_Recebimento"].unique()
        
        print('ids_recebimentos_unicos', ids_recebimentos_unicos)
        
        recebimentos_aba = arquivo().worksheet_by_title("Recebimento_v2")
        dados_recebimentos = recebimentos_aba.get_all_values()
        df_recebimentos = pd.DataFrame(data=dados_recebimentos[1:], columns=dados_recebimentos[0])

        # Filtra os Recebimento usando os IDs únicos
        recebimento_selecionados = df_recebimentos[df_recebimentos["ID_Ordem"].isin(ids_recebimentos_unicos)][["ID", "ID_Ordem", "DataRec_OrdemServiços"]]

        # Realiza o merge com os checklists
        checklists_especificos = pd.merge(checklists_especificos, recebimento_selecionados, left_on="ID_Recebimento", right_on="ID", how="left")

        # Converte a coluna "DataRec_OrdemServiços" para o tipo datetime considerando o formato dd/mm/aaaa
        df_recebimentos["DataRec_OrdemServiços"] = pd.to_datetime(df_recebimentos["DataRec_OrdemServiços"], format="%d/%m/%Y", errors='coerce')
        # Substitui os valores NaN na coluna "DataRec_OrdemServiços" por uma string vazia
        df_recebimentos["DataRec_OrdemServiços"] = df_recebimentos["DataRec_OrdemServiços"].fillna('')
    
    
        # Adiciona a coluna Nome_cliente ao DataFrame checklists_especificos
        # após o merge
        checklists_especificos["ID_Ordem"] = checklists_especificos["ID_Ordem"].fillna('')

        # Pega os IDs dos Ordem Recebimento únicos
        ids_clientes_unicos = checklists_especificos["ID"].unique()

        # Carrega a folha Cliente
        clientes_aba = arquivo().worksheet_by_title("Cliente")
        dados_clientes = clientes_aba.get_all_values()
        df_clientes = pd.DataFrame(data=dados_clientes[1:], columns=dados_clientes[0])

        # Filtra os clientes usando os IDs únicos
        clientes_selecionados = df_clientes[df_clientes["ID"].isin(ids_clientes_unicos)][["ID", "Nome_cliente"]]

         #print("Clientes Selecionados:")
         #print(clientes_selecionados)

        # Realiza o merge com os checklists
        checklists_especificos = pd.merge(checklists_especificos, clientes_selecionados, left_on="ID", right_on="ID", how="left")
    
        # Adiciona a coluna Nome_cliente ao DataFrame checklists_especificos
        # após o merge
        checklists_especificos["Nome_cliente"] = checklists_especificos["Nome_cliente"].fillna('')

        # Pega os IDs dos produtos únicos
        ids_produtos_unicos = checklists_especificos["Cod_Produto"].unique()

        # Carrega a folha Produto
        produtos_aba = arquivo().worksheet_by_title("Produto")
        dados_produtos = produtos_aba.get_all_values()
        df_produtos = pd.DataFrame(data=dados_produtos[1:], columns=dados_produtos[0])

        # Filtra os produtos usando os IDs únicos
        produtos_selecionados = df_produtos[df_produtos["Cod_Produto"].isin(ids_produtos_unicos)][["Cod_Produto", "nome_produto", "idGrupo", "idoperacaoServico", "ID_Componente", "ID_PostoTrabalho"]]

         #print("Produtos Selecionados:")
         #print(produtos_selecionados)

        # Realiza o merge com os checklists
        checklists_especificos = pd.merge(checklists_especificos, produtos_selecionados, on="Cod_Produto", how="left")

        # Pega os IDs dos grupos únicos
        ids_grupos_unicos = checklists_especificos["idGrupo"].unique()

        # Carrega a folha Grupo Produto
        grupos_aba = arquivo().worksheet_by_title("Grupo Produto")
        dados_grupos = grupos_aba.get_all_values()
        df_grupos = pd.DataFrame(data=dados_grupos[1:], columns=dados_grupos[0])

        # Filtra os grupos usando os IDs únicos
        grupos_selecionados = df_grupos[df_grupos["Id"].isin(ids_grupos_unicos)][["Id", "nome"]]

         #print("Grupos Selecionados:")
         #print(grupos_selecionados)

         # Realiza o merge com os checklists
        checklists_especificos = pd.merge(checklists_especificos, grupos_selecionados, left_on="idGrupo", right_on="Id", how="left")

        # Pega os IDs das operações únicas
        ids_operacoes_unicas = checklists_especificos["idoperacaoServico"].unique()

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
        ids_componetes_unicas = checklists_especificos["ID_Componente"].unique()

        # Carrega a folha Operacao
        componetes_aba = arquivo().worksheet_by_title("Componente")
        dados_componetes = componetes_aba.get_all_values()
        df_componetes = pd.DataFrame(data=dados_componetes[1:], columns=dados_componetes[0])

        # Filtra as operações usando os IDs únicos
        componetes_selecionadas = df_componetes[df_componetes["ID"].isin(ids_componetes_unicas)][["ID", "nome_Componente"]]

        # Preenche os valores nulos em "nome_operacao"
        componetes_selecionadas["nome_Componente"] = componetes_selecionadas["nome_Componente"].fillna('')


        # Imprime as colunas antes da conversão para dicionário
        #print("Colunas em checklists_especificos:")
        #print(checklists_especificos.columns)
        # Converte o DataFrame resultante para um dicionário
        checklists_especificos_lista = checklists_especificos.fillna('').to_dict(orient="records")

        # Adiciona os resultados à resposta JSON
        resposta_json = {"retorno_especifico": checklists_especificos_lista}

        return jsonify(resposta_json)

    except Exception as e:
        print(f"Erro ao carregar checklists específicos: {str(e)}")
        return jsonify({"error": f"Erro ao carregar checklists específicos: {str(e)}", "traceback": traceback.format_exc()})
    

@checklists.route("/numeroControle_checklists_especificos_Recebimento", methods=["POST"])
def numeroControle_checklists_especificos_Recebimento_f():
    try:
        checklists_aba = arquivo().worksheet_by_title("ChecklistRecebimento2")
        dados_checklists = checklists_aba.get_all_values()
        df_checklists = pd.DataFrame(data=dados_checklists[1:], columns=dados_checklists[0])

        # Ordena os produtos pelo numero Ordem
        df_checklists = df_checklists.sort_values(by="ID_Recebimento")

        # Pega os IDs dos Ordem Recebimento únicos
        ids_recebimentos_unicos = df_checklists["ID_Recebimento"].unique()

        print('ids_recebimentos_unicos', ids_recebimentos_unicos)

        recebimentos_aba = arquivo().worksheet_by_title("Recebimento_v2")
        dados_recebimentos = recebimentos_aba.get_all_values()
        df_recebimentos = pd.DataFrame(data=dados_recebimentos[1:], columns=dados_recebimentos[0])

       # Filtra os Recebimento usando os IDs únicos
        recebimento_selecionados = df_recebimentos[df_recebimentos["ID_Ordem"].isin(ids_recebimentos_unicos)][["ID", "ID_Ordem", "DataRec_OrdemServiços"]]

        # Realiza o merge com os checklists
        checklists_especificos = pd.merge(checklists_especificos, recebimento_selecionados, left_on="ID_Recebimento", right_on="ID", how="left")

        # Adiciona a coluna   ID_Ordem ao DataFrame checklists_especificos
        # após o merge
        checklists_especificos["ID_Ordem"] = checklists_especificos["ID_Ordem"].fillna('')

        checklists_especificos_lista = checklists_especificos.fillna('').to_dict(orient="records")

        # Adiciona os resultados à resposta JSON
        resposta_json = {"retorno_especifico": checklists_especificos_lista}

        print('Tony - resposta_json', resposta_json)
        return jsonify(resposta_json)

    except Exception as e:
        print(f"Erro ao carregar checklists específicos: {str(e)}")
        return jsonify({"error": f"Erro ao carregar checklists específicos: {str(e)}", "traceback": traceback.format_exc()})



