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

novas_Tarefas = Blueprint(
    "novas_Tarefas",
    __name__,
    static_folder="static",
    template_folder="templates",
)

# Variáveis globais para armazenar os DataFrames  - BIBLIOTECA PANDAS X GOOGLESHEET
df_novas_Tarefas = None

@novas_Tarefas.route("/selecionar_novas_tarefas_Checklist", methods=["POST"])
def selecionar_novas_tarefas_Checklist_f():
    try:
        # Carrega os dados da folha "NovasTarefas2"
        NovasTarefas_aba = arquivo().worksheet_by_title("NovasTarefas2")
        dados_NovasTarefas = NovasTarefas_aba.get_all_values()
        df_NovasTarefas = pd.DataFrame(data=dados_NovasTarefas[1:], columns=dados_NovasTarefas[0])
        
        # Filtra os registros da folha "ChecklistRecebimento2" com base no status e ID_Recebimento
        checklist_recebimento_aba = arquivo().worksheet_by_title("ChecklistRecebimento2")
        dados_checklist_recebimento = checklist_recebimento_aba.get_all_values()
        df_checklist_recebimento = pd.DataFrame(data=dados_checklist_recebimento[1:], columns=dados_checklist_recebimento[0])
        
        # Filtra os registros com base no status e ID_Recebimento
        novastarefas_checklist_filtrados = df_checklist_recebimento[
            (df_checklist_recebimento["Status_Checklist"] == "FINALIZADO") &
            (df_checklist_recebimento["ID_Recebimento"].notna()) &
            (df_checklist_recebimento["ID_Recebimento"] != "0") &
            (df_checklist_recebimento["ID_Recebimento"] != "") &
            (~df_checklist_recebimento["ID_Recebimento"].isin(df_NovasTarefas["ID_Recebimento"]))
        ]
    
        # Adicione prints para verificar os tamanhos dos DataFrames
        print("Tamanho df_checklist_recebimento:", len(df_checklist_recebimento))
        print("Tamanho df_NovasTarefas:", len(df_NovasTarefas))
        print("Tamanho novastarefas_checklist_filtrados:", len(novastarefas_checklist_filtrados))
                
        # Ordena os ID_Recebimento pelo numero Ordem
        novastarefas_checklist_filtrados = novastarefas_checklist_filtrados.sort_values(by="ID_Recebimento")

        # Pega os IDs dos Ordem Recebimento únicos
        ids_recebimentos_unicos = novastarefas_checklist_filtrados["ID_Recebimento"].unique()

        # Carrega os dados da folha "Recebimento"
        recebimentos_aba = arquivo().worksheet_by_title("Recebimento_v2")
        dados_recebimentos = recebimentos_aba.get_all_values()
        df_recebimentos = pd.DataFrame(data=dados_recebimentos[1:], columns=dados_recebimentos[0])

        # Filtra os Recebimento usando os IDs únicos
        recebimento_selecionados = df_recebimentos[df_recebimentos["ID"].isin(ids_recebimentos_unicos)][["ID", "ID_Ordem", "DataRec_OrdemServiços"]]

        # print('recebimento_selecionados', df_recebimentos)
         
        # Realiza o merge com os checklists
        novastarefas_checklist_filtrados = pd.merge(novastarefas_checklist_filtrados, recebimento_selecionados, left_on="ID_Recebimento", right_on="ID", how="left")

        # Converte a coluna "DataRec_OrdemServiços" para o tipo datetime considerando o formato dd/mm/aaaa
        df_recebimentos["DataRec_OrdemServiços"] = pd.to_datetime(df_recebimentos["DataRec_OrdemServiços"], format="%d/%m/%Y", errors='coerce')
        # Substitui os valores NaN na coluna "DataRec_OrdemServiços" por uma string vazia
        df_recebimentos["DataRec_OrdemServiços"] = df_recebimentos["DataRec_OrdemServiços"].fillna('')
    
        # Adiciona a coluna Nome_cliente ao DataFrame novastarefas_checklist_filtrados
        novastarefas_checklist_filtrados["ID_Ordem"] = novastarefas_checklist_filtrados["ID_Ordem"].fillna('')
 
        # Pega os IDs dos Ordem Recebimento únicos
        ids_clientes_unicos = novastarefas_checklist_filtrados["ID"].unique()

        # Carrega a folha Cliente
        clientes_aba = arquivo().worksheet_by_title("Cliente")
        dados_clientes = clientes_aba.get_all_values()
        df_clientes = pd.DataFrame(data=dados_clientes[1:], columns=dados_clientes[0])

        # Filtra os clientes usando os IDs únicos
        clientes_selecionados = df_clientes[df_clientes["ID"].isin(ids_clientes_unicos)][["ID", "Nome_cliente"]]

        # Realiza o merge com os checklists
        novastarefas_checklist_filtrados = pd.merge(novastarefas_checklist_filtrados, clientes_selecionados, left_on="ID", right_on="ID", how="left")
       
        # Adiciona a coluna Nome_cliente ao DataFrame novastarefas_checklist_filtrados após o merge
        novastarefas_checklist_filtrados["Nome_cliente"] = novastarefas_checklist_filtrados["Nome_cliente"].fillna('')

        # Pega os IDs dos produtos únicos
        ids_produtos_unicos = novastarefas_checklist_filtrados["Cod_Produto"].unique()

        # Carrega a folha Produto
        produtos_aba = arquivo().worksheet_by_title("Produto")
        dados_produtos = produtos_aba.get_all_values()
        df_produtos = pd.DataFrame(data=dados_produtos[1:], columns=dados_produtos[0])

        # Filtra os produtos usando os IDs únicos
        produtos_selecionados = df_produtos[df_produtos["Cod_Produto"].isin(ids_produtos_unicos)][["Cod_Produto", "nome_produto", "idGrupo", "idoperacaoServico", "ID_Componente", "ID_PostoTrabalho"]]

        # Realiza o merge com os checklists
        novastarefas_checklist_filtrados = pd.merge(novastarefas_checklist_filtrados, produtos_selecionados, on="Cod_Produto", how="left")

        # Pega os IDs dos grupos únicos
        ids_grupos_unicos = novastarefas_checklist_filtrados["idGrupo"].unique()

        # Carrega a folha Grupo Produto
        grupos_aba = arquivo().worksheet_by_title("Grupo Produto")
        dados_grupos = grupos_aba.get_all_values()
        df_grupos = pd.DataFrame(data=dados_grupos[1:], columns=dados_grupos[0])

        # Filtra os grupos usando os IDs únicos
        grupos_selecionados = df_grupos[df_grupos["Id"].isin(ids_grupos_unicos)][["Id", "nome"]]

         # Realiza o merge com os checklists
        novastarefas_checklist_filtrados = pd.merge(novastarefas_checklist_filtrados, grupos_selecionados, left_on="idGrupo", right_on="Id", how="left")

        # Pega os IDs das operações únicas
        ids_operacoes_unicas = novastarefas_checklist_filtrados["idoperacaoServico"].unique()

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
        ids_componetes_unicas = novastarefas_checklist_filtrados["ID_Componente"].unique()

        # Carrega a folha Operacao
        componetes_aba = arquivo().worksheet_by_title("Componente")
        dados_componetes = componetes_aba.get_all_values()
        df_componetes = pd.DataFrame(data=dados_componetes[1:], columns=dados_componetes[0])

        # Filtra as operações usando os IDs únicos
        componetes_selecionadas = df_componetes[df_componetes["ID"].isin(ids_componetes_unicas)][["ID", "nome_Componente"]]

        # Preenche os valores nulos em "nome_operacao"
        componetes_selecionadas["nome_Componente"] = componetes_selecionadas["nome_Componente"].fillna('')
        
        # Agrupa pelos IDs únicos e seleciona apenas a primeira linha
        primeira_linha_checklist = novastarefas_checklist_filtrados.groupby("ID_Checklist").first().reset_index()

        # Seleciona apenas as colunas necessárias para visualização do usuário
        colunas_resumidas = ["ID_Checklist"]
        checklist_resumido = primeira_linha_checklist[colunas_resumidas]

        # Converta o DataFrame resultante para um dicionário
        checklist_resumido_dict = checklist_resumido.to_dict(orient="records")

        # Converta o DataFrame original para um dicionário
        novastarefas_checklist_filtrados_dict = novastarefas_checklist_filtrados.to_dict(orient="records")
        
         # Adiciona os resultados à resposta JSON
        return jsonify({
            "checklist_resumido": checklist_resumido_dict,
            "retorno_especifico": novastarefas_checklist_filtrados_dict
        })

    except ValueError as ve:
        # Captura de erro específica para ID_Recebimento ausente
        return jsonify({"error": str(ve)})

    except Exception as e:
        # Captura de erro genérico
        print(f"Erro ao carregar checklists específicos: {str(e)}")
        return jsonify({"error": f"Erro ao carregar checklists específicos: {str(e)}", "traceback": traceback.format_exc()})
    
@novas_Tarefas.route("/selecionar_novas_tarefas_Checklist_resumido", methods=["POST"])
def selecionar_novas_tarefas_Checklist_resumido():
    try:
        # Carrega os dados da folha "NovasTarefas2"
        NovasTarefas_aba = arquivo().worksheet_by_title("NovasTarefas2")
        dados_NovasTarefas = NovasTarefas_aba.get_all_values()
        df_NovasTarefas = pd.DataFrame(data=dados_NovasTarefas[1:], columns=dados_NovasTarefas[0])
        
        # Filtra os registros da folha "ChecklistRecebimento2" com base no status e ID_Recebimento
        checklist_recebimento_aba = arquivo().worksheet_by_title("ChecklistRecebimento2")
        dados_checklist_recebimento = checklist_recebimento_aba.get_all_values()
        df_checklist_recebimento = pd.DataFrame(data=dados_checklist_recebimento[1:], columns=dados_checklist_recebimento[0])
        
        # Filtra os registros com base no status e ID_Recebimento
        novastarefas_checklist_filtrados = df_checklist_recebimento[
            (df_checklist_recebimento["Status_Checklist"] == "FINALIZADO") &
            (df_checklist_recebimento["ID_Recebimento"].notna()) &
            (df_checklist_recebimento["ID_Recebimento"] != "0") &
            (df_checklist_recebimento["ID_Recebimento"] != "") &
            (~df_checklist_recebimento["ID_Recebimento"].isin(df_NovasTarefas["ID_Recebimento"]))
        ]
    
        # Adicione prints para verificar os tamanhos dos DataFrames
        print("Tamanho df_checklist_recebimento:", len(df_checklist_recebimento))
        print("Tamanho df_NovasTarefas:", len(df_NovasTarefas))
        print("Tamanho novastarefas_checklist_filtrados:", len(novastarefas_checklist_filtrados))
                
        # Ordena os ID_Recebimento pelo numero Ordem
        novastarefas_checklist_filtrados = novastarefas_checklist_filtrados.sort_values(by="ID_Recebimento")

        # Pega os IDs dos Ordem Recebimento únicos
        ids_recebimentos_unicos = novastarefas_checklist_filtrados["ID_Recebimento"].unique()

        # Carrega os dados da folha "Recebimento"
        recebimentos_aba = arquivo().worksheet_by_title("Recebimento_v2")
        dados_recebimentos = recebimentos_aba.get_all_values()
        df_recebimentos = pd.DataFrame(data=dados_recebimentos[1:], columns=dados_recebimentos[0])

        # Filtra os Recebimento usando os IDs únicos
        recebimento_selecionados = df_recebimentos[df_recebimentos["ID"].isin(ids_recebimentos_unicos)][["ID", "ID_Ordem", "DataRec_OrdemServiços"]]


        # Realiza o merge com os checklists
        novastarefas_checklist_filtrados = pd.merge(novastarefas_checklist_filtrados, recebimento_selecionados, left_on="ID_Recebimento", right_on="ID", how="left")

        # Converte a coluna "DataRec_OrdemServiços" para o tipo datetime considerando o formato dd/mm/aaaa
        df_recebimentos["DataRec_OrdemServiços"] = pd.to_datetime(df_recebimentos["DataRec_OrdemServiços"], format="%d/%m/%Y", errors='coerce')
        # Substitui os valores NaN na coluna "DataRec_OrdemServiços" por uma string vazia
        df_recebimentos["DataRec_OrdemServiços"] = df_recebimentos["DataRec_OrdemServiços"].fillna('')
    
        # Adiciona a coluna Nome_cliente ao DataFrame novastarefas_checklist_filtrados
        novastarefas_checklist_filtrados["ID_Ordem"] = novastarefas_checklist_filtrados["ID_Ordem"].fillna('')

        # Seleciona apenas as colunas desejadas
        checklist_resumido_NumeroControle = novastarefas_checklist_filtrados[["ID_Recebimento", "ID_Ordem"]]

        # Converte o DataFrame resumido para um dicionário
        checklist_resumido_NumeroControle_dict = checklist_resumido_NumeroControle.to_dict(orient="records")

        # Adiciona os resultados à resposta JSON
        return jsonify({
            "checklist_resumido": checklist_resumido_NumeroControle_dict,
        })

    except ValueError as ve:
        # Captura de erro específica para ID_Recebimento ausente
        return jsonify({"error": str(ve)})

    except Exception as e:
        # Captura de erro genérico
        print(f"Erro ao carregar checklists específicos: {str(e)}")
        return jsonify({"error": f"Erro ao carregar checklists específicos: {str(e)}", "traceback": traceback.format_exc()})

@novas_Tarefas.route("/selecionar_novas_tarefas_Checklist_Recebimento", methods=["POST"])
def selecionar_novas_tarefas_Checklist_Recebimento_f():
    try:
        
        # Obter o período inicial e final do corpo da requisição
        id_recebimento_Filtrado_frontend = request.json["ID_Recebimento"]
        
        NovasTarefas_aba = arquivo().worksheet_by_title("ChecklistRecebimento2")
        dados_NovasTarefas = NovasTarefas_aba.get_all_values()
        df_NovasTarefas = pd.DataFrame(data=dados_NovasTarefas[1:], columns=dados_NovasTarefas[0])
        
        # Filtra os registros com base no ID_Recebimento fornecido
        novastarefas_checklist_filtrados =  df_NovasTarefas[ df_NovasTarefas["ID_Recebimento"] == id_recebimento_Filtrado_frontend]
        
        # Ordena os produtos pelo numero Ordem
        novastarefas_checklist_filtrados = novastarefas_checklist_filtrados.sort_values(by="ID_Recebimento")

        # Pega os IDs dos Ordem Recebimento únicos
        ids_recebimentos_unicos = novastarefas_checklist_filtrados["ID_Recebimento"].unique()
        
        # print('ids_recebimentos_unicos', ids_recebimentos_unicos)
        
        recebimentos_aba = arquivo().worksheet_by_title("Recebimento_v2")
        dados_recebimentos = recebimentos_aba.get_all_values()
        df_recebimentos = pd.DataFrame(data=dados_recebimentos[1:], columns=dados_recebimentos[0])

        # Filtra os Recebimento usando os IDs únicos
        recebimento_selecionados = df_recebimentos[df_recebimentos["ID_Ordem"].isin(ids_recebimentos_unicos)][["ID", "ID_Ordem", "DataRec_OrdemServiços"]]

        # Realiza o merge com os checklists
        novastarefas_checklist_filtrados = pd.merge(novastarefas_checklist_filtrados, recebimento_selecionados, left_on="ID_Recebimento", right_on="ID", how="left")

        # Converte a coluna "DataRec_OrdemServiços" para o tipo datetime considerando o formato dd/mm/aaaa
        df_recebimentos["DataRec_OrdemServiços"] = pd.to_datetime(df_recebimentos["DataRec_OrdemServiços"], format="%d/%m/%Y", errors='coerce')
        # Substitui os valores NaN na coluna "DataRec_OrdemServiços" por uma string vazia
        df_recebimentos["DataRec_OrdemServiços"] = df_recebimentos["DataRec_OrdemServiços"].fillna('')
    
    
        # Adiciona a coluna Nome_cliente ao DataFrame novastarefas_checklist_filtrados
        # após o merge
        novastarefas_checklist_filtrados["ID_Ordem"] = novastarefas_checklist_filtrados["ID_Ordem"].fillna('')

        # Pega os IDs dos Ordem Recebimento únicos
        ids_clientes_unicos = novastarefas_checklist_filtrados["ID"].unique()

        # Carrega a folha Cliente
        clientes_aba = arquivo().worksheet_by_title("Cliente")
        dados_clientes = clientes_aba.get_all_values()
        df_clientes = pd.DataFrame(data=dados_clientes[1:], columns=dados_clientes[0])

        # Filtra os clientes usando os IDs únicos
        clientes_selecionados = df_clientes[df_clientes["ID"].isin(ids_clientes_unicos)][["ID", "Nome_cliente"]]

         #print("Clientes Selecionados:")
         #print(clientes_selecionados)

        # Realiza o merge com os checklists
        novastarefas_checklist_filtrados = pd.merge(novastarefas_checklist_filtrados, clientes_selecionados, left_on="ID", right_on="ID", how="left")
    
        # Adiciona a coluna Nome_cliente ao DataFrame novastarefas_checklist_filtrados
        # após o merge
        novastarefas_checklist_filtrados["Nome_cliente"] = novastarefas_checklist_filtrados["Nome_cliente"].fillna('')

        # Pega os IDs dos produtos únicos
        ids_produtos_unicos = novastarefas_checklist_filtrados["Cod_Produto"].unique()

        # Carrega a folha Produto
        produtos_aba = arquivo().worksheet_by_title("Produto")
        dados_produtos = produtos_aba.get_all_values()
        df_produtos = pd.DataFrame(data=dados_produtos[1:], columns=dados_produtos[0])

        # Filtra os produtos usando os IDs únicos
        produtos_selecionados = df_produtos[df_produtos["Cod_Produto"].isin(ids_produtos_unicos)][["Cod_Produto", "nome_produto", "idGrupo", "idoperacaoServico", "ID_Componente", "ID_PostoTrabalho"]]

         #print("Produtos Selecionados:")
         #print(produtos_selecionados)

        # Realiza o merge com os checklists
        novastarefas_checklist_filtrados = pd.merge(novastarefas_checklist_filtrados, produtos_selecionados, on="Cod_Produto", how="left")

        # Pega os IDs dos grupos únicos
        ids_grupos_unicos = novastarefas_checklist_filtrados["idGrupo"].unique()

        # Carrega a folha Grupo Produto
        grupos_aba = arquivo().worksheet_by_title("Grupo Produto")
        dados_grupos = grupos_aba.get_all_values()
        df_grupos = pd.DataFrame(data=dados_grupos[1:], columns=dados_grupos[0])

        # Filtra os grupos usando os IDs únicos
        grupos_selecionados = df_grupos[df_grupos["Id"].isin(ids_grupos_unicos)][["Id", "nome"]]

         #print("Grupos Selecionados:")
         #print(grupos_selecionados)

         # Realiza o merge com os checklists
        novastarefas_checklist_filtrados = pd.merge(novastarefas_checklist_filtrados, grupos_selecionados, left_on="idGrupo", right_on="Id", how="left")

        # Pega os IDs das operações únicas
        ids_operacoes_unicas = novastarefas_checklist_filtrados["idoperacaoServico"].unique()

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
        ids_componetes_unicas = novastarefas_checklist_filtrados["ID_Componente"].unique()

        # Carrega a folha Operacao
        componetes_aba = arquivo().worksheet_by_title("Componente")
        dados_componetes = componetes_aba.get_all_values()
        df_componetes = pd.DataFrame(data=dados_componetes[1:], columns=dados_componetes[0])

        # Filtra as operações usando os IDs únicos
        componetes_selecionadas = df_componetes[df_componetes["ID"].isin(ids_componetes_unicas)][["ID", "nome_Componente"]]

        # Preenche os valores nulos em "nome_operacao"
        componetes_selecionadas["nome_Componente"] = componetes_selecionadas["nome_Componente"].fillna('')

        # Converte o DataFrame resultante para um dicionário
        novastarefas_checklist_filtrados_lista = novastarefas_checklist_filtrados.fillna('').to_dict(orient="records")

        # Adiciona os resultados à resposta JSON
        resposta_json = {"retorno_especifico": novastarefas_checklist_filtrados_lista}

        return jsonify(resposta_json)

    except Exception as e:
        print(f"Erro ao carregar checklists específicos: {str(e)}")
        return jsonify({"error": f"Erro ao carregar checklists específicos: {str(e)}", "traceback": traceback.format_exc()})
    
@novas_Tarefas.route("/numeroControle_novastarefas_checklist_filtrados_Recebimento", methods=["POST"])
def numeroControle_novastarefas_checklist_filtrados_Recebimento_f():
    try:
        NovasTarefas_aba = arquivo().worksheet_by_title("ChecklistRecebimento2")
        dados_NovasTarefas = NovasTarefas_aba.get_all_values()
        df_NovasTarefas = pd.DataFrame(data=dados_NovasTarefas[1:], columns=dados_NovasTarefas[0])

        # Ordena os produtos pelo numero Ordem
        df_NovasTarefas =  df_NovasTarefas.sort_values(by="ID_Recebimento")

        # Pega os IDs dos Ordem Recebimento únicos
        ids_recebimentos_unicos =  df_NovasTarefas["ID_Recebimento"].unique()

        # print('ids_recebimentos_unicos', ids_recebimentos_unicos)

        recebimentos_aba = arquivo().worksheet_by_title("Recebimento_v2")
        dados_recebimentos = recebimentos_aba.get_all_values()
        df_recebimentos = pd.DataFrame(data=dados_recebimentos[1:], columns=dados_recebimentos[0])

       # Filtra os Recebimento usando os IDs únicos
        recebimento_selecionados = df_recebimentos[df_recebimentos["ID"].isin(ids_recebimentos_unicos)][["ID", "ID_Ordem", "DataRec_OrdemServiços"]]

        # Realiza o merge com os checklists
        novastarefas_checklist_filtrados = pd.merge(novastarefas_checklist_filtrados, recebimento_selecionados, left_on="ID_Recebimento", right_on="ID", how="left")

        # Adiciona a coluna   ID_Ordem ao DataFrame novastarefas_checklist_filtrados
        # após o merge
        novastarefas_checklist_filtrados["ID_Ordem"] = novastarefas_checklist_filtrados["ID_Ordem"].fillna('')

        novastarefas_checklist_filtrados_lista = novastarefas_checklist_filtrados.fillna('').to_dict(orient="records")

        # Adiciona os resultados à resposta JSON
        resposta_json = {"retorno_especifico": novastarefas_checklist_filtrados_lista}

        # print('Tony - resposta_json', resposta_json)
        return jsonify(resposta_json)

    except Exception as e:
        print(f"Erro ao carregar checklists específicos: {str(e)}")
        return jsonify({"error": f"Erro ao carregar checklists específicos: {str(e)}", "traceback": traceback.format_exc()})

@novas_Tarefas.route("/impressao_novastarefas_checklist_filtrados_Recebimento", methods=["POST"])
def impressao_novastarefas_checklist_filtrados_Recebimento_f():
    try:
         # Obter o período inicial e final do corpo da requisição
        id_checklist_Filtrado_frontend = request.json.get("dadosEnviados", [])

        # print('id_checklist_Filtrado_frontend', id_checklist_Filtrado_frontend)

        # Extrair apenas o campo "idPCP"
        id_pcp_list = [item.get("idPCP") for item in id_checklist_Filtrado_frontend]

        # Inicializar novastarefas_checklist_filtrados como um DataFrame vazio
        novastarefas_checklist_filtrados = pd.DataFrame()
        
        # Carrega dados da folha "ChecklistRecebimento2"
        NovasTarefas_aba = arquivo().worksheet_by_title("ChecklistRecebimento2")
        dados_NovasTarefas = NovasTarefas_aba.get_all_values()
        df_NovasTarefas = pd.DataFrame(data=dados_NovasTarefas[1:], columns=dados_NovasTarefas[0])

        # Verifica se a lista id_pcp_list não está vazia antes de fazer a comparação
        if id_pcp_list:
            novastarefas_checklist_filtrados =  df_NovasTarefas[ df_NovasTarefas["ID_Checklist"].isin(id_pcp_list)]
            
        # Imprime novastarefas_checklist_filtrados após atribuir valor a ele
        # print('novastarefas_checklist_filtrados', novastarefas_checklist_filtrados)

        # Ordena os produtos pelo numero Ordem
        novastarefas_checklist_filtrados = novastarefas_checklist_filtrados.sort_values(by="ID_Recebimento")

        # Pega os IDs dos Ordem Recebimento únicos
        ids_recebimentos_unicos =  df_NovasTarefas["ID_Recebimento"].unique()
        # print('ids_recebimentos_unicos', ids_recebimentos_unicos)

        # Carrega dados da folha "Recebimento_v2"
        recebimentos_aba = arquivo().worksheet_by_title("Recebimento_v2")
        dados_recebimentos = recebimentos_aba.get_all_values()
        df_recebimentos = pd.DataFrame(data=dados_recebimentos[1:], columns=dados_recebimentos[0])

        # Filtra os Recebimento usando os IDs únicos
        recebimento_selecionados = df_recebimentos[df_recebimentos["ID"].isin(ids_recebimentos_unicos)][["ID", "ID_Ordem", "DataRec_OrdemServiços"]]

        # Realiza o merge com os checklists
        novastarefas_checklist_filtrados = pd.merge(novastarefas_checklist_filtrados, recebimento_selecionados, left_on="ID_Recebimento", right_on="ID", how="left")

        # Converte a coluna "DataRec_OrdemServiços" para o tipo datetime considerando o formato dd/mm/aaaa
        df_recebimentos["DataRec_OrdemServiços"] = pd.to_datetime(df_recebimentos["DataRec_OrdemServiços"], format="%d/%m/%Y", errors='coerce')
        # Substitui os valores NaN na coluna "DataRec_OrdemServiços" por uma string vazia
        df_recebimentos["DataRec_OrdemServiços"] = df_recebimentos["DataRec_OrdemServiços"].fillna('')

        # Adiciona a coluna Nome_cliente ao DataFrame novastarefas_checklist_filtrados após o merge
        novastarefas_checklist_filtrados["ID_Ordem"] = novastarefas_checklist_filtrados["ID_Ordem"].fillna('')

        # Pega os IDs dos Ordem Recebimento únicos
        ids_clientes_unicos = novastarefas_checklist_filtrados["ID"].unique()

        # Carrega a folha Cliente
        clientes_aba = arquivo().worksheet_by_title("Cliente")
        dados_clientes = clientes_aba.get_all_values()
        df_clientes = pd.DataFrame(data=dados_clientes[1:], columns=dados_clientes[0])

        # Filtra os clientes usando os IDs únicos
        clientes_selecionados = df_clientes[df_clientes["ID"].isin(ids_clientes_unicos)][["ID", "Nome_cliente"]]

         #print("Clientes Selecionados:")
         #print(clientes_selecionados)

        # Realiza o merge com os checklists
        novastarefas_checklist_filtrados = pd.merge(novastarefas_checklist_filtrados, clientes_selecionados, left_on="ID", right_on="ID", how="left")
    
        # Adiciona a coluna Nome_cliente ao DataFrame novastarefas_checklist_filtrados
        # após o merge
        novastarefas_checklist_filtrados["Nome_cliente"] = novastarefas_checklist_filtrados["Nome_cliente"].fillna('')

        # Pega os IDs dos produtos únicos
        ids_produtos_unicos = novastarefas_checklist_filtrados["Cod_Produto"].unique()

        # Carrega a folha Produto
        produtos_aba = arquivo().worksheet_by_title("Produto")
        dados_produtos = produtos_aba.get_all_values()
        df_produtos = pd.DataFrame(data=dados_produtos[1:], columns=dados_produtos[0])

        # Filtra os produtos usando os IDs únicos
        produtos_selecionados = df_produtos[df_produtos["Cod_Produto"].isin(ids_produtos_unicos)][["Cod_Produto", "nome_produto", "idGrupo", "idoperacaoServico", "ID_Componente", "ID_PostoTrabalho"]]

         #print("Produtos Selecionados:")
         #print(produtos_selecionados)

        # Realiza o merge com os checklists
        novastarefas_checklist_filtrados = pd.merge(novastarefas_checklist_filtrados, produtos_selecionados, on="Cod_Produto", how="left")

        # Pega os IDs dos grupos únicos
        ids_grupos_unicos = novastarefas_checklist_filtrados["idGrupo"].unique()

        # Carrega a folha Grupo Produto
        grupos_aba = arquivo().worksheet_by_title("Grupo Produto")
        dados_grupos = grupos_aba.get_all_values()
        df_grupos = pd.DataFrame(data=dados_grupos[1:], columns=dados_grupos[0])

        # Filtra os grupos usando os IDs únicos
        grupos_selecionados = df_grupos[df_grupos["Id"].isin(ids_grupos_unicos)][["Id", "nome"]]

         #print("Grupos Selecionados:")
         #print(grupos_selecionados)

         # Realiza o merge com os checklists
        novastarefas_checklist_filtrados = pd.merge(novastarefas_checklist_filtrados, grupos_selecionados, left_on="idGrupo", right_on="Id", how="left")

        # Pega os IDs das operações únicas
        ids_operacoes_unicas = novastarefas_checklist_filtrados["idoperacaoServico"].unique()

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
        ids_componetes_unicas = novastarefas_checklist_filtrados["ID_Componente"].unique()

        # Carrega a folha Operacao
        componetes_aba = arquivo().worksheet_by_title("Componente")
        dados_componetes = componetes_aba.get_all_values()
        df_componetes = pd.DataFrame(data=dados_componetes[1:], columns=dados_componetes[0])

        # Filtra as operações usando os IDs únicos
        componetes_selecionadas = df_componetes[df_componetes["ID"].isin(ids_componetes_unicas)][["ID", "nome_Componente"]]

        # Preenche os valores nulos em "nome_operacao"
        componetes_selecionadas["nome_Componente"] = componetes_selecionadas["nome_Componente"].fillna('')
        
        # Lista das colunas desejadas na ordem desejada
        colunas_desejadas = ["ID_Checklist", "ID_Ordem", "Nome_cliente", "Qtd_Produto", "nome_produto", "Referencia_Produto",
                            "NotaInterna", "QUEIXA_CLIENTE", "DataRec_OrdemServiços", "Usuario_Cadastro", "LINK_PDF_CHECKLIST"]
        
        # Adiciona os resultados à resposta JSON, incluindo apenas as colunas desejadas
        resposta_json = {"retorno_especifico": novastarefas_checklist_filtrados[colunas_desejadas].fillna('').to_dict(orient="records")}

        # Adiciona os resultados à resposta JSON
        impressao_ChecklistRecebimento_aba = arquivo().worksheet_by_title("Impressao_ChecklistRecebimento")

        # Limpa todos os dados na planilha
        impressao_ChecklistRecebimento_aba.clear()

        # Adicione os dados à folha "Impressao_ChecklistRecebimento"
        impressao_ChecklistRecebimento_aba.set_dataframe(
            pd.DataFrame(resposta_json["retorno_especifico"]), start="A1"
        )

        # Chame a função para criar a cópia do documento
        print("Antes de chamar criar_copia_e_processar_documento()")
        if criar_copia_e_processar_documento():
            # Retorna um indicador de sucesso para o frontend
            response = jsonify({"success": True, "message": "Operação concluída com sucesso.", "resultados": resposta_json["retorno_especifico"]})
        else:
            response = jsonify({"success": False, "message": "Erro ao processar documento."})

        response.headers.add('Content-Type', 'application/json')
        print("Depois de chamar criar_copia_e_processar_documento()")
        return response  # Adicione este retorno
    
    
    except Exception as e:
        print(f"Erro ao carregar checklists específicos: {str(e)}")

        # Retornar um indicador de erro para o front-end
        return jsonify({"success": False, "error": f"Erro ao carregar checklists específicos: {str(e)}", "traceback": traceback.format_exc()})

# ........................................////.........................../////.............
@novas_Tarefas.route("/criar_copia_e_processar_documento", methods=["POST"])
def criar_copia_e_processar_documento():
    resultados_processados = []

    try:
        
        # Atribua os valores às variáveis
        modeloId = '1VIrF8PyUYe-DCIeDBv3Nmiy8if7pIPhl9zA7jM50PhE'
        destinoId = '1fstEX_fgNPnzBEeu1szOvZ43AdMTPTjk'
        
        # Obtenha os dados do modelo_id e destino_id da requisição
        modelo_id = modeloId
        destino_id = destinoId

        # Inicialize o objeto google_docs_handler com as credenciais
        google_docs_handler = GoogleDocsHandler(
            credenciais_sheets, credenciais_drive, service_file_path
        )

        # Obtenha os dados da planilha usando o método da classe
        resultados = google_docs_handler.obter_dados_google_sheets()
        print("TONY RESULTADO", resultados)

        # Itera sobre os dados da requisição
        for dados_linha in resultados:
           # print("TONY - dados_linha", dados_linha)

            # Verifique se Nome_funcionario não está vazio ou nulo
            if dados_linha["ID_Ordem"]:
                try:
                    # Chame a função para criar a cópia do documento
                    doc_copiado_id = google_docs_handler.criar_copia_do_doc(
                        modelo_id, destino_id, dados_linha["ID_Ordem"]
                    )
                      # Vprint("doc_copiado_id", doc_copiado_id)

                    # Obter o link da cópia do documento
                    link_documento_copiado = google_docs_handler.obter_link_documento_copiado(
                        doc_copiado_id
                    )
                      # Vprint("link_documento_copiado", link_documento_copiado)

                    # Adicionar o Link GoogleDoc GoogleSheet
                    google_docs_handler.adicionar_link_para_linha(
                        doc_copiado_id,
                        link_documento_copiado,
                        dados_linha["ID_Ordem"],
                    )
                    print("adicionar_link_para_linha")

                    # Abrir o documento para edição
                    google_docs_handler.abrir_documento_para_edicao(
                        doc_copiado_id, dados_linha
                    )

                    # Armazenar resultados
                    resultados_processados.append(
                        {
                            "doc_copiado_id": doc_copiado_id,
                            "link_documento_copiado": link_documento_copiado,
                            "dados_linha": dados_linha,
                        }
                    )

                except Exception as e:
                    # Tratar erros específicos se necessário
                    print(f"Erro ao processar linha: {str(e)}")

    except Exception as e:
        # Tratar erros específicos se necessário
        print(f"Erro ao processar requisição: {str(e)}")
        resultados_processados = []  # Garante que a variável seja inicializada

    # Extraia apenas os links de documento copiado da lista resultados_processados
    links_documentos_copiados = [resultado["link_documento_copiado"] for resultado in resultados_processados]

    # print('TONY NORTHCROMO  - resultados_processados', links_documentos_copiados)
    return jsonify({"status": "success", "resultados": links_documentos_copiados})