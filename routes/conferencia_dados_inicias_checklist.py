from flask import Blueprint, render_template, jsonify, request
import pandas as pd
import os
import pygsheets
from datetime import datetime
from routes.funcoesGerais import *
import logging
import numpy as np
from cachetools import cached, TTLCache
import hashlib

# Configurar o logging para imprimir mensagens de depuração
logging.basicConfig(level=logging.DEBUG)


conferencia_dados_inicias_checklist = Blueprint(
    "conferencia_programacao_dados_iniciais_Checklist",
    __name__,
    static_folder="static",
    template_folder="templates",
)  

COLUNA_LINK = 'LINK'
COLUNA_ID = 'ID'

class CacheDados:
    def __init__(self):
        self.hash_dados_recebimento = None
        self.dados_em_cache_recebimento = None

        self.hash_dados_cliente = None
        self.dados_em_cache_cliente = None
        
        self.hash_dados_produto = None
        self.dados_em_cache_produto = None
        
        self.hash_dados_operacao = None
        self.dados_em_cache_operacao = None
                
        self.hash_dados_ChecklistRecebimento = None
        self.dados_em_cache_ChecklistRecebimento = None
                       
cache_dados = CacheDados()

# Limpar cache
@conferencia_dados_inicias_checklist.route("/limpar_cache", methods=["GET"])
def limpar_cache():
    with conferencia_dados_inicias_checklist.app_context():
        cache_dados.clear()
    return "Cache limpo com sucesso!"

# Função para carregar dados de uma aba
def carregar_dados_gs(aba):
    dados_da_planilha = aba.get_all_values()
    df = pd.DataFrame(dados_da_planilha[1:], columns=dados_da_planilha[0])
    return df

# Função para obter dados da folha "Recebimento" com caching
@cached(cache=TTLCache(maxsize=500, ttl=600))  # Cache válido por 10 minutos  maxsize = Número de linhas ttl= tempo 
def obter_dados_recebimento():
    sheet_recebimento = arquivo().worksheet_by_title("Recebimento")
    dados_recebimento = sheet_recebimento.get_all_values()
    df_recebimento = pd.DataFrame(dados_recebimento[1:], columns=dados_recebimento[0])
    
     # Calcular o hash dos dados
    hash_dados = hashlib.md5(df_recebimento.to_json().encode()).hexdigest()
    
    # Verificar se os dados mudaram
    if cache_dados.hash_dados_recebimento == hash_dados:
        return cache_dados.dados_em_cache_recebimento
    else:
       #  logging.debug("Atualizando cache para obter_dados_recebimento.")
        # Atualizar o cache
        cache_dados.hash_dados_recebimento = hash_dados
        cache_dados.dados_em_cache_recebimento = df_recebimento
    return df_recebimento

# Função para obter dados da folha "Cliente" com caching
@cached(cache=TTLCache(maxsize=500, ttl=3600))  # Cache válido por 1 Hora
def obter_dados_cliente():
    sheet_cliente = arquivo().worksheet_by_title("Cliente")
    dados_cliente = sheet_cliente.get_all_values()
    df_cliente = pd.DataFrame(dados_cliente[1:], columns=dados_cliente[0])
    
     # Calcular o hash dos dados
    hash_dados = hashlib.md5(df_cliente.to_json().encode()).hexdigest()
    
     # Calcular o hash dos dados
    hash_dados = hashlib.md5(df_cliente.to_json().encode()).hexdigest()
    
    # Verificar se os dados mudaram
    if cache_dados.hash_dados_cliente == hash_dados:
        return cache_dados.dados_em_cache_cliente
    else:
        # Atualizar o cache
        cache_dados.hash_dados_cliente = hash_dados
        cache_dados.dados_em_cache_cliente = df_cliente
    return df_cliente

# Função para obter dados da folha "Produto" com caching
@cached(cache=TTLCache(maxsize=9000, ttl=3600))  # Cache válido por 1 Hora
def obter_dados_produto():
    sheet_produto = arquivo().worksheet_by_title("Produto")
    dados_produto = sheet_produto.get_all_values()
    df_produto = pd.DataFrame(dados_produto[1:], columns=dados_produto[0])
    
     # Calcular o hash dos dados
    hash_dados = hashlib.md5(df_produto.to_json().encode()).hexdigest()
    
     # Calcular o hash dos dados
    hash_dados = hashlib.md5(df_produto.to_json().encode()).hexdigest()
    
    # Verificar se os dados mudaram
    if cache_dados.hash_dados_produto == hash_dados:
        return cache_dados.dados_em_cache_produto
    else:
        # Atualizar o cache
        cache_dados.hash_dados_produto = hash_dados
        cache_dados.dados_em_cache_produto = df_produto
    return df_produto

# Função para obter dados da folha "Operacao" com caching
@cached(cache=TTLCache(maxsize=100, ttl=3600))  # Cache válido por 1 Hora
def obter_dados_operacao():
    sheet_operacao = arquivo().worksheet_by_title("Operacao")
    dados_operacao = sheet_operacao.get_all_values()
    df_operacao = pd.DataFrame(dados_operacao[1:], columns=dados_operacao[0])
    
      # Calcular o hash dos dados
    hash_dados = hashlib.md5(df_operacao.to_json().encode()).hexdigest()
    
     # Calcular o hash dos dados
    hash_dados = hashlib.md5(df_operacao.to_json().encode()).hexdigest()
    
    # Verificar se os dados mudaram
    if cache_dados.hash_dados_operacao == hash_dados:
        return cache_dados.dados_em_cache_operacao
    else:
        # Atualizar o cache
        cache_dados.hash_dados_operacao = hash_dados
        cache_dados.dados_em_cache_operacao = df_operacao
    return df_operacao

# Função para obter dados da folha "ChecklistRecebimento" com caching
@cached(cache=TTLCache(maxsize=900, ttl=600))  # Cache válido por 10 minutos
def obter_dados_ChecklistRecebimento():
    global cache_dados  # Certifique-se de que a variável global seja acessada
    sheet_ChecklistRecebimento = arquivo().worksheet_by_title("ChecklistRecebimento")
    dados_ChecklistRecebimento = sheet_ChecklistRecebimento.get_all_values()
    df_ChecklistRecebimento = pd.DataFrame(dados_ChecklistRecebimento[1:], columns=dados_ChecklistRecebimento[0])
      
      # Calcular o hash dos dados
    hash_dados = hashlib.md5(df_ChecklistRecebimento.to_json().encode()).hexdigest()
    
     # Calcular o hash dos dados
    hash_dados = hashlib.md5(df_ChecklistRecebimento.to_json().encode()).hexdigest()
    
    # Verificar se os dados mudaram
    if cache_dados.hash_dados_ChecklistRecebimento == hash_dados:
        return cache_dados.dados_em_cache_ChecklistRecebimento
    else:
        # Atualizar o cache
        cache_dados.hash_dados_ChecklistRecebimento = hash_dados
        cache_dados.dados_em_cache_ChecklistRecebimento = df_ChecklistRecebimento
    return df_ChecklistRecebimento

# Função para formatar a data
def formatar_data(raw_date):
    try:
        if pd.notna(raw_date):
            # Se a coluna for 'DataRec_OrdemServiços', use o formato "%m/%d/%Y"
            if 'DataRec_OrdemServiços' in raw_date:
                date_object = datetime.strptime(str(raw_date), "%m/%d/%Y")
            else:
                date_object = datetime.strptime(str(raw_date), "%Y-%m-%d")

            return date_object.strftime("%d/%m/%Y")
    except ValueError:
        pass
    return "-"

# Função para obter o valor da coluna O (índice 14) da "Recebimento" pelo ID
def get_valor_coluna_o_from_recebimento_by_id(id, df_recebimento, coluna_link):
    # Filtra o DataFrame para encontrar o ID desejado
    linha_selecionada = df_recebimento[df_recebimento['ID'] == id]

    if not linha_selecionada.empty:
        # Retorna o valor da coluna 'LINK' (substitua pelo nome real da coluna O)
        return linha_selecionada[coluna_link].iloc[0]

    return None  # Se o ID não foi encontrado, retornamos None

# Função para remover pontos de uma string e converter para numérico
def remover_pontos_e_converter(valor):
    if pd.notna(valor):
        # Remover pontos e espaços em branco e, em seguida, tentar converter para numérico
        valor_sem_pontos = str(valor).replace('.', '').strip()
        if valor_sem_pontos:  # Verificar se não é uma string vazia
            return pd.to_numeric(valor_sem_pontos, errors='coerce')
    return valor


@conferencia_dados_inicias_checklist.route("/conferencia_programacao_dados_iniciais_Checklist", methods=["GET", "POST"])
def conferencia_programacao_dados_iniciais_Checklist_f():

    try:
        
        # Se o cache não estiver disponível, carregar os dados da folha "ChecklistRecebimento"
        aba_checklist = arquivo().worksheet_by_title("ChecklistRecebimento")
        df_checklist = carregar_dados_gs(aba_checklist)
        
        # Remova espaços em branco antes e depois do valor na coluna 'ID_Ordem'
        df_checklist['ID_Ordem'] = df_checklist['ID_Ordem'].str.strip()
        
        
        # Filtrar as linhas onde a coluna 'LINK' não está vazia e 'id_Checklist' é diferente de vazio
        df_checklist = df_checklist[~df_checklist['LINK'].str.startswith('https://drive.') & ~df_checklist['id_Checklist'].astype(str).str.strip().eq('')]

        # Otimizando a leitura dos DataFrames Cliente, Recebimento, Produto e Operacao
        df_recebimento = obter_dados_recebimento()
        df_cliente = obter_dados_cliente()
        df_produto = obter_dados_produto()
        df_operacao = obter_dados_operacao()
        
        # Convertendo colunas em df_cliente
        df_produto['Cod_Produto'] = pd.to_numeric(df_produto['Cod_Produto'], errors='coerce')
        df_produto['idGrupo'] = pd.to_numeric(df_produto['idGrupo'], errors='coerce')
        df_produto['idoperacaoServico'] = pd.to_numeric(df_produto['idoperacaoServico'], errors='coerce')
        df_produto['Cod_Produto'] = pd.to_numeric(df_produto['Cod_Produto'], errors='coerce')
        
        # Convertendo colunas em df_recebimento
        df_checklist['ID_Ordem'] = pd.to_numeric(df_checklist['ID_Ordem'], errors='coerce')
        df_checklist['ID_cliente'] = pd.to_numeric(df_checklist['ID_cliente'], errors='coerce')
        df_checklist['Cod_Produto'] = pd.to_numeric(df_checklist['Cod_Produto'], errors='coerce')
        df_checklist['Quantidade'] = pd.to_numeric(df_checklist['Quantidade'], errors='coerce')
        df_checklist['id_Checklist'] = pd.to_numeric(df_checklist['id_Checklist'], errors='coerce')

        # Convertendo colunas em df_recebimento
        df_recebimento['ID_Ordem'] = pd.to_numeric(df_recebimento['ID_Ordem'], errors='coerce')

        # Convertendo colunas em df_cliente
        df_cliente['ID_Cliente'] = pd.to_numeric(df_cliente['ID_Cliente'], errors='coerce')
        
        # Certifique-se de que os nomes das colunas estejam corretos
        df_checklist['DataRec_OrdemServiços_Recebimento'] = df_checklist['ID_Ordem'].map(df_recebimento.set_index('ID_Ordem')['DataRec_OrdemServiços'])
        df_checklist['HoraInicial_Ordem_Recebimento'] = df_checklist['ID_Ordem'].map(df_recebimento.set_index('ID_Ordem')['HoraInicial_Ordem'])
        df_checklist['ID_Vendedor_Recebimento'] = df_checklist['ID_Ordem'].map(df_recebimento.set_index('ID_Ordem')['ID_Vendedor'])
        df_checklist['Nome_cliente'] = df_checklist['ID_cliente'].map(df_cliente.set_index('ID_Cliente')['Nome_cliente'])

        colunas_produto = ['Cod_Produto', 'nome_produto', 'idGrupo', 'idoperacaoServico', 'ID_Componente', 'ID_PostoTrabalho']
        df_checklist = pd.merge(df_checklist, df_produto[colunas_produto], how='left', on='Cod_Produto')
        
        colunas_recebimento = ['ID_Ordem', 'Recebimento', 'QUEIXA_CLIENTE']
        df_checklist = pd.merge(df_checklist, df_recebimento[colunas_recebimento], how='left', on='ID_Ordem')
        
          #print("df_checklist após numero:")
          #print(df_checklist.dtypes)
          #print(df_checklist.head())
        
        # Selecione apenas as colunas desejadas
        colunas_desejadas = ['id_Checklist','Recebimento', 'Nome_cliente','Cod_Produto','nome_produto','Refencia_Produto', 'Quantidade','NotaInterna', 'QUEIXA_CLIENTE']

        df_checklist_selecionado = df_checklist[colunas_desejadas]
        
        # print("df_checklist_selecionado_tabela:")
        # print(df_checklist_selecionado.dtypes)
        # print(df_checklist_selecionado.head())
    
          #print("Valores únicos em 'id_Checklist' antes da seleção:")
          #print(df_checklist['id_Checklist'].unique())
    
        # Converta o DataFrame diretamente para JSON usando jsonify
        result_json = df_checklist_selecionado.to_json(orient='records')

        # Retorne os dados mapeados como JSON
        return jsonify(retorno=result_json)
    
    except Exception as error:
        print("Erro: ", str(error))
        return jsonify(retorno="Algo deu errado: " + str(error)), 500

@conferencia_dados_inicias_checklist.route("/recebimento_linhas_unicas_checklist", methods=["GET", "POST"])
def recebimento_linhas_unicas_checklist():
    try:
        # Carregar dados da folha "ChecklistRecebimento"
        aba_checklist = arquivo().worksheet_by_title("ChecklistRecebimento")
        df_checklist = carregar_dados_gs(aba_checklist)

        # Carregar dados da folha "Recebimento"
        aba_recebimento = arquivo().worksheet_by_title("Recebimento")
        df_recebimento = carregar_dados_gs(aba_recebimento)

        # Filtrar linhas únicas da coluna 'Recebimento' com base em 'ID_Ordem'
        linhas_unicas_checklist = df_checklist['ID_Ordem'].dropna().unique()
        df_recebimento_filtrado = df_recebimento[df_recebimento['ID_Ordem'].isin(linhas_unicas_checklist)]
        linhas_unicas_recebimento = df_recebimento_filtrado['Recebimento'].dropna().unique()

        # Selecionar apenas a coluna 'Recebimento'
        df_recebimento_selecionado = df_recebimento_filtrado[['Recebimento']]
        
        # print("df_checklist_selecionado:")
        # print(df_recebimento_selecionado.dtypes)
        # print(df_recebimento_selecionado.head())

        # Converta o DataFrame selecionado para JSON usando jsonify
        result_json = df_recebimento_selecionado.to_json(orient='records')

        # Retorne os dados mapeados como JSON
        return jsonify(retorno=result_json)

    except Exception as error:
        print("Erro: ", str(error))
        return jsonify(retorno="Algo deu errado: " + str(error)), 500

# Função para forçar a limpeza do cache
def limpar_cache():
    obter_dados_recebimento.cache_clear()
    obter_dados_cliente.cache_clear()
    obter_dados_produto.cache_clear()
    obter_dados_operacao.cache_clear()
    obter_dados_ChecklistRecebimento.clear()
    
# Rota para limpar o cache
@conferencia_dados_inicias_checklist.route("/limpar_cache", methods=["GET"])
def limpar_cache_rota():
    limpar_cache()
    return jsonify(retorno="Cache limpo com sucesso.")

# Função para obter dados da folha "ChecklistRecebimento" com caching
@cached(cache=TTLCache(maxsize=10, ttl=20))
@conferencia_dados_inicias_checklist.route("/consultar_numero_controle_Checklist", methods=["GET", "POST"])
def consultar_numero_controle_Checklist():
    try:
        # Carregar dados da folha "ChecklistRecebimento" e outros DataFrames
        df_ChecklistRecebimento = obter_dados_ChecklistRecebimento()
        df_recebimento = obter_dados_recebimento()
        df_cliente = obter_dados_cliente()
        df_produto = obter_dados_produto()

        # Remover espaços em branco nas colunas 'ID_Ordem' dos DataFrames
        for df in [df_ChecklistRecebimento, df_recebimento]:
            if pd.api.types.is_string_dtype(df['ID_Ordem']):
                df['ID_Ordem'] = df['ID_Ordem'].str.strip()

        # Obter o valor do frontend (substitua 'valor_do_frontend' pelo valor real recebido do frontend)
        numerocontrole = request.json.get('numControleValue')

        # Filtrar os dados com base no valor recebido do frontend
        df_recebimento_filtrado = df_recebimento[df_recebimento['Recebimento'] == numerocontrole]

        # Verificar se há linhas correspondentes no DataFrame filtrado
        if not df_recebimento_filtrado.empty:

            # Obter o valor de 'ID_Ordem' correspondente ao primeiro registro
            id_ordem_correspondente = df_recebimento_filtrado['ID_Ordem'].values[0]

            # Filtrar df_ChecklistRecebimento para incluir apenas as linhas com o mesmo ID_Ordem
            df_ChecklistRecebimento_filtrado = df_ChecklistRecebimento[df_ChecklistRecebimento['ID_Ordem'] == id_ordem_correspondente]

            # Convertendo colunas em df_cliente
            df_produto['Cod_Produto'] = pd.to_numeric(df_produto['Cod_Produto'], errors='coerce')
            df_produto['idGrupo'] = pd.to_numeric(df_produto['idGrupo'], errors='coerce')
            df_produto['idoperacaoServico'] = pd.to_numeric(df_produto['idoperacaoServico'], errors='coerce')
            df_produto['Cod_Produto'] = pd.to_numeric(df_produto['Cod_Produto'], errors='coerce')
         
            df_recebimento['ID_Ordem'] = pd.to_numeric(df_recebimento['ID_Ordem'], errors='coerce')
            df_ChecklistRecebimento_filtrado['ID_Ordem'] = pd.to_numeric(df_ChecklistRecebimento_filtrado['ID_Ordem'], errors='coerce')
            df_recebimento_filtrado['ID_Ordem'] = pd.to_numeric(df_recebimento_filtrado['ID_Ordem'], errors='coerce')
        
            # Convertendo colunas em df_recebimento
            df_ChecklistRecebimento['ID_Ordem'] = pd.to_numeric(df_ChecklistRecebimento['ID_Ordem'], errors='coerce')
            df_ChecklistRecebimento['ID_cliente'] = pd.to_numeric(df_ChecklistRecebimento['ID_cliente'], errors='coerce')
            df_ChecklistRecebimento['Cod_Produto'] = pd.to_numeric(df_ChecklistRecebimento['Cod_Produto'], errors='coerce')
            df_ChecklistRecebimento['Quantidade'] = pd.to_numeric(df_ChecklistRecebimento['Quantidade'], errors='coerce')
            df_ChecklistRecebimento['id_Checklist'] = pd.to_numeric(df_ChecklistRecebimento['id_Checklist'], errors='coerce')

            # Certifique-se de que os nomes das colunas estejam corretos
            df_ChecklistRecebimento['DataRec_OrdemServiços_Recebimento'] = df_ChecklistRecebimento['ID_Ordem'].map(
                df_recebimento.set_index('ID_Ordem')['DataRec_OrdemServiços'])
            df_ChecklistRecebimento['HoraInicial_Ordem_Recebimento'] = df_ChecklistRecebimento['ID_Ordem'].map(
                df_recebimento.set_index('ID_Ordem')['HoraInicial_Ordem'])
            df_ChecklistRecebimento['ID_Vendedor_Recebimento'] = df_ChecklistRecebimento['ID_Ordem'].map(
                df_recebimento.set_index('ID_Ordem')['ID_Vendedor'])
            df_ChecklistRecebimento['Nome_cliente'] = df_ChecklistRecebimento['ID_cliente'].map(
                df_cliente.set_index('ID_Cliente')['Nome_cliente'])

            colunas_produto = ['Cod_Produto', 'nome_produto', 'idGrupo', 'idoperacaoServico', 'ID_Componente',
                               'ID_PostoTrabalho']
            df_ChecklistRecebimento = pd.merge(df_ChecklistRecebimento, df_produto[colunas_produto], how='left',
                                               on='Cod_Produto')

            colunas_recebimento = ['ID_Ordem', 'Recebimento', 'QUEIXA_CLIENTE']
            df_ChecklistRecebimento = pd.merge(df_ChecklistRecebimento, df_recebimento[colunas_recebimento], how='left',
                                               on='ID_Ordem')

            # Selecione apenas as colunas desejadas
            colunas_desejadas = ['id_Checklist', 'Recebimento', 'Nome_cliente', 'Cod_Produto', 'nome_produto',
                                 'Refencia_Produto', 'Quantidade', 'NotaInterna', 'QUEIXA_CLIENTE']
            df_checklist_selecionado = df_ChecklistRecebimento[colunas_desejadas].head(1)

            # Converta o DataFrame diretamente para JSON usando jsonify
            result_json = df_checklist_selecionado.to_json(orient='records')

            print("TONY result_json_tabela_teste:", result_json)

            # Retorne os dados mapeados como JSON
            return jsonify(retorno=result_json)

    except Exception as error:
        print("Erro: ", str(error))
        return jsonify(retorno="Algo deu errado: " + str(error)), 500
