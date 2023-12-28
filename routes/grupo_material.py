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

grupo_material = Blueprint(
    "grupo_material",
    __name__,
    static_folder="static",
    template_folder="templates",
)

# Variáveis globais para armazenar os DataFrames  - BIBLIOTECA PANDAS X GOOGLESHEET
df_grupo_material = None


@grupo_material.route("/adicionar_atualizar_grupo_material", methods=["POST"])
def adicionar_atualizar_grupo_material_f():
    try:
        # Selecione a aba correta (você já deve ter esse código)
        aba = arquivo().worksheet_by_title("grupo_material_suelo")
        dados_da_planilha = aba.get_all_values()

        coluna_sequencia = [int(value) for value in aba.get_col(1)[1:] if value.strip()]
        prox_id = max(coluna_sequencia, default=0) + 1

        # Receba os dados do front-end
        dados = request.get_json()

        # Validação de dados do frontend
        if not dados or not isinstance(dados, dict):
            return jsonify(retorno="Dados inválidos."), 400

        # Obtenha o ID do grupo_material
        id_grupo_material = dados.get("id_grupo_material", 0)

        if id_grupo_material == 0:
            # Use o próximo ID como "id_grupo_material" nos dados
            id_grupo_material = prox_id
            dados["id_grupo_material"] = id_grupo_material
        else:
            # Verifica se o ID existe na planilha
            if id_grupo_material not in coluna_sequencia:
                return jsonify(retorno="ID do grupo_material não encontrado."), 404

            # Obtém a linha correspondente ao ID
            linha_index = coluna_sequencia.index(id_grupo_material) + 2
            linha = aba.row_values(linha_index)

            # Transforma a linha em um objeto
            grupo_material_existente = {
                "id_grupo_material": int(linha[0]),
                "nome_grupo_material": linha[1],
                "data_atualizacao": linha[2],
                "hora_atualizacao": linha[3],
            }

            # Atualiza os demais campos no objeto com os novos dados
            grupo_material_existente.update({
                "nome_grupo_material": dados.get("nome_grupo_material", grupo_material_existente["nome_grupo_material"]),
                # Adicione os outros campos aqui conforme necessário
            })

            # Atualiza a linha correspondente no Google Sheets
            aba.update([list(grupo_material_existente.values())], start=f"A{linha_index}")

            return jsonify(retorno="Deu certo!", dados=grupo_material_existente)

        # Mapeie os campos do frontend para as colunas do Google Sheets
        mapeamento = {
            "id_grupo_material": "id_grupo_material",
            "nome_grupo_material": "nome_grupo_material",
            "data_atualizacao": "data_atualizacao",
            "hora_atualizacao": "hora_atualizacao",
        }

        # Crie um dicionário de valores a serem inseridos/atualizados no Google Sheets
        valores = {}

        # Itere pelos campos do frontend e mapeie-os para as colunas correspondentes
        for campo_frontend, coluna_sheet in mapeamento.items():
            if campo_frontend in dados:
                valores[coluna_sheet] = dados[campo_frontend]
            else:
                # Define para vazio se o campo não estiver presente nos dados
                valores[coluna_sheet] = ""

        # Obtém a data e hora atuais
        data_hora_atual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        # Adiciona data e hora da atualização
        valores["data_atualizacao"] = data_hora_atual.split()[0]
        valores["hora_atualizacao"] = data_hora_atual.split()[1]

        # Converta os valores em uma lista antes de inseri-los
        valores_list = list(valores.values())

        # Adiciona ou atualiza a linha com os dados
        if id_grupo_material in coluna_sequencia:
            # Atualiza a linha correspondente no Google Sheets
            linha_index = coluna_sequencia.index(id_grupo_material) + 2
            aba.update([valores_list], start=f"A{linha_index}")
        else:
            # Insere uma nova linha com os dados
            aba.append_table(
                values=[valores_list],
                start="A2",
                end=None,
                dimension="ROWS",
                overwrite=False,
            )

        return jsonify(retorno="Deu certo!", dados=valores)
    except Exception as e:
        return jsonify(retorno="Algo deu errado."), 500
    
@grupo_material.route("/selecionar_grupo_material_especificos", methods=["POST"])
def selecionar_grupo_material_especificos_f():
    try:
        grupo_material_aba = arquivo().worksheet_by_title("grupo_material_suelo")
        dados_grupo_material = grupo_material_aba.get_all_values()
        df_grupo_material = pd.DataFrame(data=dados_grupo_material[1:], columns=dados_grupo_material[0])
        
        # Filtra os registros com base no período fornecido
        grupo_material_especificos = df_grupo_material[(df_grupo_material["id_grupo_material"].notna()) & (df_grupo_material["id_grupo_material"] != "0") & (df_grupo_material["id_grupo_material"] != "")]
    
        # Ordena os produtos pelo numero Ordem
        grupo_material_especificos = grupo_material_especificos.sort_values(by="nome_grupo_material")

        grupo_material_especificos_lista = grupo_material_especificos.fillna('').to_dict(orient="records")
        
        # Adiciona os resultados à resposta JSON
        resposta_json = {"retorno_especifico": grupo_material_especificos_lista}
        
        print('resposta_json', resposta_json)

        return jsonify(resposta_json)

    except Exception as e:
        print(f"Erro ao carregar grupo_material específicos: {str(e)}")
        return jsonify({"error": f"Erro ao carregar grupo_material específicos: {str(e)}", "traceback": traceback.format_exc()})


@grupo_material.route("/selecionar_grupo_material_especificos_Recebimento", methods=["POST"])
def selecionar_grupo_material_especificos_Recebimento_f():
    try:
        
        # Obter o período inicial e final do corpo da requisição
        id_recebimento_Filtrado_frontend = request.json["ID_Recebimento"]
        
        grupo_material_aba = arquivo().worksheet_by_title("ChecklistRecebimento2")
        dados_grupo_material = grupo_material_aba.get_all_values()
        df_grupo_material = pd.DataFrame(data=dados_grupo_material[1:], columns=dados_grupo_material[0])
        
        # Filtra os registros com base no ID_Recebimento fornecido
        grupo_material_especificos = df_grupo_material[df_grupo_material["ID_Recebimento"] == id_recebimento_Filtrado_frontend]
        
        # Ordena os produtos pelo numero Ordem
        grupo_material_especificos = grupo_material_especificos.sort_values(by="ID_Recebimento")

        # Pega os IDs dos Ordem Recebimento únicos
        ids_recebimentos_unicos = grupo_material_especificos["ID_Recebimento"].unique()
        
        # print('ids_recebimentos_unicos', ids_recebimentos_unicos)
        
        recebimentos_aba = arquivo().worksheet_by_title("Recebimento_v2")
        dados_recebimentos = recebimentos_aba.get_all_values()
        df_recebimentos = pd.DataFrame(data=dados_recebimentos[1:], columns=dados_recebimentos[0])

        # Filtra os Recebimento usando os IDs únicos
        recebimento_selecionados = df_recebimentos[df_recebimentos["ID_Ordem"].isin(ids_recebimentos_unicos)][["ID", "ID_Ordem", "DataRec_OrdemServiços"]]

        # Realiza o merge com os grupo_material
        grupo_material_especificos = pd.merge(grupo_material_especificos, recebimento_selecionados, left_on="ID_Recebimento", right_on="ID", how="left")

        # Converte a coluna "DataRec_OrdemServiços" para o tipo datetime considerando o formato dd/mm/aaaa
        df_recebimentos["DataRec_OrdemServiços"] = pd.to_datetime(df_recebimentos["DataRec_OrdemServiços"], format="%d/%m/%Y", errors='coerce')
        # Substitui os valores NaN na coluna "DataRec_OrdemServiços" por uma string vazia
        df_recebimentos["DataRec_OrdemServiços"] = df_recebimentos["DataRec_OrdemServiços"].fillna('')
    
    
        # Adiciona a coluna Nome_cliente ao DataFrame grupo_material_especificos
        # após o merge
        grupo_material_especificos["ID_Ordem"] = grupo_material_especificos["ID_Ordem"].fillna('')

        # Pega os IDs dos Ordem Recebimento únicos
        ids_clientes_unicos = grupo_material_especificos["ID"].unique()

        # Carrega a folha Cliente
        clientes_aba = arquivo().worksheet_by_title("Cliente")
        dados_clientes = clientes_aba.get_all_values()
        df_clientes = pd.DataFrame(data=dados_clientes[1:], columns=dados_clientes[0])

        # Filtra os clientes usando os IDs únicos
        clientes_selecionados = df_clientes[df_clientes["ID"].isin(ids_clientes_unicos)][["ID", "Nome_cliente"]]

         #print("Clientes Selecionados:")
         #print(clientes_selecionados)

        # Realiza o merge com os grupo_material
        grupo_material_especificos = pd.merge(grupo_material_especificos, clientes_selecionados, left_on="ID", right_on="ID", how="left")
    
        # Adiciona a coluna Nome_cliente ao DataFrame grupo_material_especificos
        # após o merge
        grupo_material_especificos["Nome_cliente"] = grupo_material_especificos["Nome_cliente"].fillna('')

        # Pega os IDs dos produtos únicos
        ids_produtos_unicos = grupo_material_especificos["Cod_Produto"].unique()

        # Carrega a folha Produto
        produtos_aba = arquivo().worksheet_by_title("Produto")
        dados_produtos = produtos_aba.get_all_values()
        df_produtos = pd.DataFrame(data=dados_produtos[1:], columns=dados_produtos[0])

        # Filtra os produtos usando os IDs únicos
        produtos_selecionados = df_produtos[df_produtos["Cod_Produto"].isin(ids_produtos_unicos)][["Cod_Produto", "nome_produto", "idGrupo", "idoperacaoServico", "ID_Componente", "ID_PostoTrabalho"]]

         #print("Produtos Selecionados:")
         #print(produtos_selecionados)

        # Realiza o merge com os grupo_material
        grupo_material_especificos = pd.merge(grupo_material_especificos, produtos_selecionados, on="Cod_Produto", how="left")

        # Pega os IDs dos grupos únicos
        ids_grupos_unicos = grupo_material_especificos["idGrupo"].unique()

        # Carrega a folha Grupo Produto
        grupos_aba = arquivo().worksheet_by_title("Grupo Produto")
        dados_grupos = grupos_aba.get_all_values()
        df_grupos = pd.DataFrame(data=dados_grupos[1:], columns=dados_grupos[0])

        # Filtra os grupos usando os IDs únicos
        grupos_selecionados = df_grupos[df_grupos["Id"].isin(ids_grupos_unicos)][["Id", "nome"]]

         #print("Grupos Selecionados:")
         #print(grupos_selecionados)

         # Realiza o merge com os grupo_material
        grupo_material_especificos = pd.merge(grupo_material_especificos, grupos_selecionados, left_on="idGrupo", right_on="Id", how="left")

        # Pega os IDs das operações únicas
        ids_operacoes_unicas = grupo_material_especificos["idoperacaoServico"].unique()

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
        ids_componetes_unicas = grupo_material_especificos["ID_Componente"].unique()

        # Carrega a folha Operacao
        componetes_aba = arquivo().worksheet_by_title("Componente")
        dados_componetes = componetes_aba.get_all_values()
        df_componetes = pd.DataFrame(data=dados_componetes[1:], columns=dados_componetes[0])

        # Filtra as operações usando os IDs únicos
        componetes_selecionadas = df_componetes[df_componetes["ID"].isin(ids_componetes_unicas)][["ID", "nome_Componente"]]

        # Preenche os valores nulos em "nome_operacao"
        componetes_selecionadas["nome_Componente"] = componetes_selecionadas["nome_Componente"].fillna('')


        # Imprime as colunas antes da conversão para dicionário
        #print("Colunas em grupo_material_especificos:")
        #print(grupo_material_especificos.columns)
        # Converte o DataFrame resultante para um dicionário
        grupo_material_especificos_lista = grupo_material_especificos.fillna('').to_dict(orient="records")

        # Adiciona os resultados à resposta JSON
        resposta_json = {"retorno_especifico": grupo_material_especificos_lista}

        return jsonify(resposta_json)

    except Exception as e:
        print(f"Erro ao carregar grupo_material específicos: {str(e)}")
        return jsonify({"error": f"Erro ao carregar grupo_material específicos: {str(e)}", "traceback": traceback.format_exc()})
    
@grupo_material.route("/numeroControle_grupo_material_especificos_Recebimento", methods=["POST"])
def numeroControle_grupo_material_especificos_Recebimento_f():
    try:
        grupo_material_aba = arquivo().worksheet_by_title("ChecklistRecebimento2")
        dados_grupo_material = grupo_material_aba.get_all_values()
        df_grupo_material = pd.DataFrame(data=dados_grupo_material[1:], columns=dados_grupo_material[0])

        # Ordena os produtos pelo numero Ordem
        df_grupo_material = df_grupo_material.sort_values(by="ID_Recebimento")

        # Pega os IDs dos Ordem Recebimento únicos
        ids_recebimentos_unicos = df_grupo_material["ID_Recebimento"].unique()

        # print('ids_recebimentos_unicos', ids_recebimentos_unicos)

        recebimentos_aba = arquivo().worksheet_by_title("Recebimento_v2")
        dados_recebimentos = recebimentos_aba.get_all_values()
        df_recebimentos = pd.DataFrame(data=dados_recebimentos[1:], columns=dados_recebimentos[0])

       # Filtra os Recebimento usando os IDs únicos
        recebimento_selecionados = df_recebimentos[df_recebimentos["ID"].isin(ids_recebimentos_unicos)][["ID", "ID_Ordem", "DataRec_OrdemServiços"]]

        # Realiza o merge com os grupo_material
        grupo_material_especificos = pd.merge(grupo_material_especificos, recebimento_selecionados, left_on="ID_Recebimento", right_on="ID", how="left")

        # Adiciona a coluna   ID_Ordem ao DataFrame grupo_material_especificos
        # após o merge
        grupo_material_especificos["ID_Ordem"] = grupo_material_especificos["ID_Ordem"].fillna('')

        grupo_material_especificos_lista = grupo_material_especificos.fillna('').to_dict(orient="records")

        # Adiciona os resultados à resposta JSON
        resposta_json = {"retorno_especifico": grupo_material_especificos_lista}

        # print('Tony - resposta_json', resposta_json)
        return jsonify(resposta_json)

    except Exception as e:
        print(f"Erro ao carregar grupo_material específicos: {str(e)}")
        return jsonify({"error": f"Erro ao carregar grupo_material específicos: {str(e)}", "traceback": traceback.format_exc()})

@grupo_material.route("/impressao_grupo_material_especificos_Recebimento", methods=["POST"])
def impressao_grupo_material_especificos_Recebimento_f():
    try:
         # Obter o período inicial e final do corpo da requisição
        id_grupo_material_Filtrado_frontend = request.json.get("dadosEnviados", [])

        # print('id_grupo_material_Filtrado_frontend', id_grupo_material_Filtrado_frontend)

        # Extrair apenas o campo "idPCP"
        id_pcp_list = [item.get("idPCP") for item in id_grupo_material_Filtrado_frontend]

        # Inicializar grupo_material_especificos como um DataFrame vazio
        grupo_material_especificos = pd.DataFrame()
        
        # Carrega dados da folha "ChecklistRecebimento2"
        grupo_material_aba = arquivo().worksheet_by_title("ChecklistRecebimento2")
        dados_grupo_material = grupo_material_aba.get_all_values()
        df_grupo_material = pd.DataFrame(data=dados_grupo_material[1:], columns=dados_grupo_material[0])

        # Verifica se a lista id_pcp_list não está vazia antes de fazer a comparação
        if id_pcp_list:
            grupo_material_especificos = df_grupo_material[df_grupo_material["id_grupo_material"].isin(id_pcp_list)]
            
        # Imprime grupo_material_especificos após atribuir valor a ele
        # print('grupo_material_especificos', grupo_material_especificos)

        # Ordena os produtos pelo numero Ordem
        grupo_material_especificos = grupo_material_especificos.sort_values(by="ID_Recebimento")

        # Pega os IDs dos Ordem Recebimento únicos
        ids_recebimentos_unicos = df_grupo_material["ID_Recebimento"].unique()
        # print('ids_recebimentos_unicos', ids_recebimentos_unicos)

        # Carrega dados da folha "Recebimento_v2"
        recebimentos_aba = arquivo().worksheet_by_title("Recebimento_v2")
        dados_recebimentos = recebimentos_aba.get_all_values()
        df_recebimentos = pd.DataFrame(data=dados_recebimentos[1:], columns=dados_recebimentos[0])

        # Filtra os Recebimento usando os IDs únicos
        recebimento_selecionados = df_recebimentos[df_recebimentos["ID"].isin(ids_recebimentos_unicos)][["ID", "ID_Ordem", "DataRec_OrdemServiços"]]

        # Realiza o merge com os grupo_material
        grupo_material_especificos = pd.merge(grupo_material_especificos, recebimento_selecionados, left_on="ID_Recebimento", right_on="ID", how="left")

        # Converte a coluna "DataRec_OrdemServiços" para o tipo datetime considerando o formato dd/mm/aaaa
        df_recebimentos["DataRec_OrdemServiços"] = pd.to_datetime(df_recebimentos["DataRec_OrdemServiços"], format="%d/%m/%Y", errors='coerce')
        # Substitui os valores NaN na coluna "DataRec_OrdemServiços" por uma string vazia
        df_recebimentos["DataRec_OrdemServiços"] = df_recebimentos["DataRec_OrdemServiços"].fillna('')

        # Adiciona a coluna Nome_cliente ao DataFrame grupo_material_especificos após o merge
        grupo_material_especificos["ID_Ordem"] = grupo_material_especificos["ID_Ordem"].fillna('')

        # Pega os IDs dos Ordem Recebimento únicos
        ids_clientes_unicos = grupo_material_especificos["ID"].unique()

        # Carrega a folha Cliente
        clientes_aba = arquivo().worksheet_by_title("Cliente")
        dados_clientes = clientes_aba.get_all_values()
        df_clientes = pd.DataFrame(data=dados_clientes[1:], columns=dados_clientes[0])

        # Filtra os clientes usando os IDs únicos
        clientes_selecionados = df_clientes[df_clientes["ID"].isin(ids_clientes_unicos)][["ID", "Nome_cliente"]]

         #print("Clientes Selecionados:")
         #print(clientes_selecionados)

        # Realiza o merge com os grupo_material
        grupo_material_especificos = pd.merge(grupo_material_especificos, clientes_selecionados, left_on="ID", right_on="ID", how="left")
    
        # Adiciona a coluna Nome_cliente ao DataFrame grupo_material_especificos
        # após o merge
        grupo_material_especificos["Nome_cliente"] = grupo_material_especificos["Nome_cliente"].fillna('')

        # Pega os IDs dos produtos únicos
        ids_produtos_unicos = grupo_material_especificos["Cod_Produto"].unique()

        # Carrega a folha Produto
        produtos_aba = arquivo().worksheet_by_title("Produto")
        dados_produtos = produtos_aba.get_all_values()
        df_produtos = pd.DataFrame(data=dados_produtos[1:], columns=dados_produtos[0])

        # Filtra os produtos usando os IDs únicos
        produtos_selecionados = df_produtos[df_produtos["Cod_Produto"].isin(ids_produtos_unicos)][["Cod_Produto", "nome_produto", "idGrupo", "idoperacaoServico", "ID_Componente", "ID_PostoTrabalho"]]

         #print("Produtos Selecionados:")
         #print(produtos_selecionados)

        # Realiza o merge com os grupo_material
        grupo_material_especificos = pd.merge(grupo_material_especificos, produtos_selecionados, on="Cod_Produto", how="left")

        # Pega os IDs dos grupos únicos
        ids_grupos_unicos = grupo_material_especificos["idGrupo"].unique()

        # Carrega a folha Grupo Produto
        grupos_aba = arquivo().worksheet_by_title("Grupo Produto")
        dados_grupos = grupos_aba.get_all_values()
        df_grupos = pd.DataFrame(data=dados_grupos[1:], columns=dados_grupos[0])

        # Filtra os grupos usando os IDs únicos
        grupos_selecionados = df_grupos[df_grupos["Id"].isin(ids_grupos_unicos)][["Id", "nome"]]

         #print("Grupos Selecionados:")
         #print(grupos_selecionados)

         # Realiza o merge com os grupo_material
        grupo_material_especificos = pd.merge(grupo_material_especificos, grupos_selecionados, left_on="idGrupo", right_on="Id", how="left")

        # Pega os IDs das operações únicas
        ids_operacoes_unicas = grupo_material_especificos["idoperacaoServico"].unique()

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
        ids_componetes_unicas = grupo_material_especificos["ID_Componente"].unique()

        # Carrega a folha Operacao
        componetes_aba = arquivo().worksheet_by_title("Componente")
        dados_componetes = componetes_aba.get_all_values()
        df_componetes = pd.DataFrame(data=dados_componetes[1:], columns=dados_componetes[0])

        # Filtra as operações usando os IDs únicos
        componetes_selecionadas = df_componetes[df_componetes["ID"].isin(ids_componetes_unicas)][["ID", "nome_Componente"]]

        # Preenche os valores nulos em "nome_operacao"
        componetes_selecionadas["nome_Componente"] = componetes_selecionadas["nome_Componente"].fillna('')
        
        # Lista das colunas desejadas na ordem desejada
        colunas_desejadas = ["id_grupo_material", "ID_Ordem", "Nome_cliente", "Qtd_Produto", "nome_produto", "Referencia_Produto",
                            "NotaInterna", "QUEIXA_CLIENTE", "DataRec_OrdemServiços", "Usuario_Cadastro", "LINK_PDF_CHECKLIST"]
        
        # Adiciona os resultados à resposta JSON, incluindo apenas as colunas desejadas
        resposta_json = {"retorno_especifico": grupo_material_especificos[colunas_desejadas].fillna('').to_dict(orient="records")}

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
        print(f"Erro ao carregar grupo_material específicos: {str(e)}")

        # Retornar um indicador de erro para o front-end
        return jsonify({"success": False, "error": f"Erro ao carregar grupo_material específicos: {str(e)}", "traceback": traceback.format_exc()})

# ........................................////.........................../////.............
@grupo_material.route("/criar_copia_e_processar_documento", methods=["POST"])
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