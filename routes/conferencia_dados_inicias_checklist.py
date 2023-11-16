from flask import Blueprint, render_template, jsonify, request
import pandas as pd
import os
import pygsheets
from datetime import datetime
from routes.funcoesGerais import *

conferencia_dados_inicias_checklist = Blueprint(
    "conferencia_programacao_dados_iniciais_Checklist",
    __name__,
    static_folder="static",
    template_folder="templates",
)

# Função para carregar dados de uma aba

def carregar_dados_gs(aba):
    dados_da_planilha = aba.get_all_values()
    df = pd.DataFrame(dados_da_planilha[1:], columns=dados_da_planilha[0])
    return df

def obter_dados_produto():
    sheet_produto = arquivo().worksheet_by_title("Produto")
    dados_produto = sheet_produto.get_all_values()
    df_produto = pd.DataFrame(dados_produto[1:], columns=dados_produto[0])

    # Adicione esta linha para imprimir as colunas
    print("Colunas do DataFrame Produto:", df_produto.columns)

    # Restante do código permanece inalterado
    colunas_numericas = ['Cod_Produto', 'idGrupo', 'idoperacaoServico']
    df_produto[colunas_numericas] = df_produto[colunas_numericas].apply(pd.to_numeric, errors='coerce')

    print("df_produto:", df_produto)
    return df_produto

def realizar_conversao_colunas_numericas(df, colunas_numericas):
    df_copy = df.copy()
    
    for coluna in colunas_numericas:
        df_copy[coluna] = df_copy[coluna].apply(lambda x: pd.to_numeric(x.replace(',', '.'), errors='coerce') if isinstance(x, str) else x)

    return df_copy

def filtrar_e_reformular_linhas_vazias(df_checklist, df_produto):
    linhas_vazias = df_checklist, df_produto[df_checklist, df_produto['LINK'].isin(["", " ", None])].copy()

    # Lista de folhas e suas respectivas colunas desejadas
    folhas_colunas = {
        'Produto': ['Cod_Produto', 'nome_produto', 'idGrupo', 'idoperacaoServico'],
        'Operacao': ['Id_operacao', 'grupo_Processo', 'nome_Processo'],
        'Componente': ['ID_Componente', 'nome_Componente', 'ID_componente', 'nome_Componente'],
        'PostoTrabalho': ['Id_Posto', 'nome_Posto'],
        'ChecklistRecebimento': ['Id_Checklist', 'ID_Ordem', 'DataRec_OrdemServiços', 'HoraInicial_Ordem', 'ID_cliente', 'Cod_Produto', 'NotaInterna', 'Quantidade', 'Refencia_Produto', 'LINK', 'Observacao_Checklist', 'Status_Tarefa', 'DataChecklist_OrdemServiços']
    }


    # Define colunas que precisam de conversão para numérico
    colunas_numericas_checklist = ['Id_Checklist', 'ID_Ordem', 'ID_cliente', 'Cod_Produto']
    colunas_numericas_produto = ['Cod_Produto', 'idGrupo', 'idoperacaoServiço']

    # Converte colunas numéricas na DataFrame de linhas vazias usando .loc
    linhas_vazias.loc[:, colunas_numericas_checklist] = linhas_vazias.loc[:, colunas_numericas_checklist].apply(pd.to_numeric, errors='coerce')

    # Dicionário para armazenar os DataFrames filtrados
    dataframes_filtrados = {}

    for folha, colunas in folhas_colunas.items():
        # Seleciona apenas as colunas desejadas
        df_folha = linhas_vazias[colunas]
        print(df_folha)

        # Realiza a conversão de colunas numéricas se aplicável
        colunas_numericas = colunas_numericas_checklist if folha == 'ChecklistRecebimento' else colunas_numericas_produto
        df_folha[colunas_numericas] = df_folha[colunas_numericas].apply(pd.to_numeric, errors='coerce')

        # Realiza merge com a folha correspondente se aplicável
        if folha == 'ChecklistRecebimento':
            df_produto = obter_dados_produto()[['Cod_Produto', 'nome_produto']]
            
            # Adicione esta linha para imprimir as colunas antes do merge
            print(f"Colunas do DataFrame {folha} Antes do Merge:", df_folha.columns)

            
            df_folha = pd.merge(
                df_folha,
                df_produto,  # Usando o DataFrame df_produto já obtido
                left_on='Cod_Produto',
                right_on='Cod_Produto',
                how='left'
            )
            
        # Adicione esta linha para imprimir as colunas após o merge
        print(f"Colunas do DataFrame {folha} Após o Merge:", df_folha.columns)
    
        # # Converte colunas numéricas na DataFrame resultante após o merge usando .loc
        df_folha.loc[:, colunas_numericas_produto] = df_folha.loc[:, colunas_numericas_produto].apply(pd.to_numeric, errors='coerce')


        # Seleciona colunas relevantes
        colunas_selecionadas = ['ID_Ordem', 'ID_cliente', 'Cod_Produto', 'LINK', 'Quantidade', 'Refencia_Produto', 'DataRec_OrdemServiços', 'Observacao_Checklist']

        # Filtra colunas
        df_folha = df_folha[colunas_selecionadas]

        # Inicia a lista para armazenar as linhas reformuladas
        linhas_reformuladas = []

        for _, row in df_folha.iterrows():
            id_cliente = int(row['ID_cliente'])
            id_descricao = int(row['Cod_Produto'])
            valor_produto = buscar_valor_por_id_na_folha_produto(id_descricao)

            id_registro = int(row['ID_Ordem'])
            qtde_produto = int(row['Quantidade'])
            referencia_produto = row['Refencia_Produto']

            data_formatada = formatar_data(row['DataRec_OrdemServiços'])
            observacoes_recebimento = row['Observacao_Checklist']

            numero_controle_encontrado = get_numero_controle_from_recebimento_by_id(id_registro)
            nome_cliente_encontrado = get_nome_cliente_by_id(id_cliente)
            nome_descricao_encontrado = get_nome_descricao_by_id(id_descricao)
            operacao = buscar_operacao_por_id_servico(valor_produto)

            linha_reformulada = [
                data_formatada,
                numero_controle_encontrado,
                nome_cliente_encontrado,
                nome_descricao_encontrado,
                row['LINK'],
                id_registro,
                referencia_produto,
                qtde_produto,
                operacao,
                id_descricao,
                observacoes_recebimento
            ]
            linhas_reformuladas.append(linha_reformulada)

        # Armazena as linhas reformuladas no dicionário
        dataframes_filtrados[folha] = linhas_reformuladas

    return dataframes_filtrados

@conferencia_dados_inicias_checklist.route("/conferencia_programacao_dados_iniciais_Checklist", methods=["GET", "POST"])
def conferencia_programacao_dados_iniciais_Checklist_f():
    try:
        aba = arquivo().worksheet_by_title("ChecklistRecebimento")
        df = carregar_dados_gs(aba)
        print(df)
        linhas_reformuladas = filtrar_e_reformular_linhas_vazias(df)
        return jsonify({"dados_filtrados_e_reformatados": linhas_reformuladas})

    except Exception as error:
        print("Erro: ", str(error))
        return jsonify({"error": str(error)}), 500
        
    
# Função para atualizar a coluna K com dados de Recebimento
def atualizar_coluna_k_com_dados_de_recebimento():
    # Formata a coluna O na folha "Recebimento" para maiúsculas
    formatar_coluna_o_recebimento_para_maiusculas()

    # Substitua "ChecklistRecebimento" pelo nome real da folha de dados
    sheet_checklist = arquivo().worksheet_by_title("ChecklistRecebimento")
    df_checklist = carregar_dados_gs(sheet_checklist)

    # Loop através de cada linha no DataFrame
    for i, row in df_checklist.iterrows():
        coluna_k = row['LINK']  # A coluna K é a coluna 'LINK'
        id_registro = int(row['ID_Ordem'])  # ID na coluna 'ID_Ordem'

        if pd.isna(coluna_k):  # Se a coluna K estiver vazia
            valor_coluna_o = get_valor_coluna_o_from_recebimento_by_id(id_registro)

            if valor_coluna_o:
                df_checklist.at[i, 'LINK'] = valor_coluna_o  # Atualiza o valor na coluna K

    # Atualize os dados na folha "ChecklistRecebimento" com os novos valores da coluna K
    sheet_checklist.clear()
    sheet_checklist.set_dataframe(df_checklist, start='A1')



# Função para buscar a operação por ID de serviço
def buscar_operacao_por_id_servico(id_servico):
    # Substitua "Operacao" pelo nome da sua folha de dados
    sheet_operacao = arquivo().worksheet_by_title("Operacao")
    dados_operacao = sheet_operacao.get_all_values()

    print(sheet_operacao, dados_operacao)
    
    for row in dados_operacao:
        if row[0] == id_servico:
            return row[1]

    return None  # Operação não encontrada


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

# Função para buscar o valor por ID na folha Produto

def buscar_valor_por_id_na_folha_produto(id_descricao):
    try:
        # Substitua "Produto" pelo nome da sua folha de dados
        sheet_produto = arquivo().worksheet_by_title("Produto")
        dados_produto = sheet_produto.get_all_values()
        
        print("produto", dados_produto)

        # Obtém os dados das colunas A e D
        coluna_a = [int(row[0]) if row[0].isdigit() else row[0] for row in dados_produto]
        coluna_d = [float(row[3]) if row[3].replace('.', '').replace(',', '').isdigit() else row[3] for row in dados_produto]

        # Encontra o índice do id_descricao na coluna A
        index = coluna_a.index(int(id_descricao))

        # Retorna o valor correspondente da coluna D
        return coluna_d[index]
    except ValueError as ve:
        print(f"Erro ao buscar valor por ID na folha Produto. Valor não numérico: {id_descricao}")
        return None
    except Exception as error:
        print("Erro geral ao buscar valor por ID na folha Produto:", str(error))
        return None


# Função para obter o nome do cliente pelo ID
def get_nome_cliente_by_id(id_cliente):
    # Substitua "Cliente" pelo nome da sua folha de dados
    sheet_cliente = arquivo().worksheet_by_title("Cliente")
    dados_cliente = sheet_cliente.get_all_values()

    for row in dados_cliente:
        if int(row[0]) == id_cliente:
            return row[2]  # Assumindo que o nome do cliente está na coluna C (índice 2)

    return None  # Cliente não encontrado


# PELO O IDORDEM TRANSFORMAR DESCRIÇÃO, IRA PARA TABELA
def get_nome_descricao_by_id(idDescricao):
    sheet_produto = arquivo().worksheet_by_title("Produto")
    dados_produto = sheet_produto.get_all_values()
    
    for row in dados_produto[1:]:
        if int(row[0]) == idDescricao:
            return row[1]  # Assumindo que o nome do Descrição esteja na coluna B (index 1)
    
    return None  # Descrição não encontrado

# PELO O IDORDEM TRANSFORMAR CLIENTE, IRA PARA TABELA
def get_nome_cliente_by_id(idCliente):
    sheet_cliente = arquivo().worksheet_by_title("Cliente")
    dados_cliente = sheet_cliente.get_all_values()
    
    for row in dados_cliente[1:]:
        if int(row[0]) == idCliente:
            return row[2]  # Assumindo que o nome do cliente esteja na coluna C (index 2)
    
    return None  # Cliente não encontrado

# Função para formatar a coluna O (índice 14) para maiúsculas em "Recebimento"
def formatar_coluna_o_recebimento_para_maiusculas():
    # Substitua "Recebimento" pelo nome real da folha de dados
    sheet_recebimento = arquivo().worksheet_by_title("Recebimento")
    df_recebimento = carregar_dados_gs(sheet_recebimento)

    # Converte para maiúsculas os valores na coluna 'Recebimento' (assumindo que seja a coluna 'LINK')
    df_recebimento['LINK'] = df_recebimento['LINK'].str.upper()

    # Atualiza os dados formatados na folha "Recebimento"
    sheet_recebimento.clear()
    sheet_recebimento.set_dataframe(df_recebimento, start='A1')

# Função para obter o valor da coluna O (índice 14) da "Recebimento" pelo ID
def get_valor_coluna_o_from_recebimento_by_id(id, df_recebimento):
    # Filtra o DataFrame para encontrar o ID desejado
    linha_selecionada = df_recebimento[df_recebimento['ID'] == id]

    if not linha_selecionada.empty:
        # Retorna o valor da coluna 'LINK' (substitua pelo nome real da coluna O)
        return linha_selecionada['LINK'].iloc[0]
    
    return None  # Se o ID não foi encontrado, retornamos None
# Função para mapear observações por ID
def mapear_observacoes_por_id(id, folhas):
    observacoes_completas = []

    for folha_nome, coluna_observacao in folhas.items():
        folha = arquivo().worksheet_by_title(folha_nome)
        df = carregar_dados_gs(folha)

        # Encontrar a linha com o ID desejado
        linha_encontrada = df[df['ID'] == str(id)]

        if not linha_encontrada.empty:
            observacao = linha_encontrada[coluna_observacao].iloc[0]
            observacoes_completas.append(f"{folha_nome}: {observacao}")

    # Junta todas as observações com um separador
    return " | ".join(observacoes_completas)

# Função para obter a observação de uma folha pelo ID
def get_observacao_from_sheet_by_id(sheet_name, id, column_index):
    folha = arquivo().worksheet_by_title(sheet_name)
    df = carregar_dados_gs(folha)

    # Encontrar a linha com o ID desejado
    linha_encontrada = df[df['ID'] == str(id)]

    if not linha_encontrada.empty:
        return linha_encontrada.iloc[0][column_index]

    return None

# Função para formatar observações
def formatar_observacoes(obs):
    return {
        'recebimento': f"Observação de Recebimento: {obs['Recebimento']}" if obs['Recebimento'] else "Sem observação de recebimento.",
        'checklist': f"Observação de Checklist: {obs['ChecklistRecebimento']}" if obs['ChecklistRecebimento'] else "Sem observação de checklist.",
        'apontamento': f"Observação de Apontamento: {obs['NovasTarefas_Realizar']}" if obs['NovasTarefas_Realizar'] else "Sem observação de apontamento.",
        'andamentoProducao': f"Observação de Andamento da Produção: {obs['ProgramacaoPCP']}" if obs['ProgramacaoPCP'] else "Sem observação de andamento da produção."
    }
    
def get_numero_controle_from_recebimento_by_id(id):
     return f"Controle{id}"

def merge_checklist_produto(df_checklist, df_produto):
    # Realiza merge com a folha "Produto"
    df_checklist = pd.merge(
        df_checklist,
        df_produto[['Cod_Produto', 'nome_produto', 'idGrupo', 'idoperacaoServico']],
        left_on='Cod_Produto',
        right_on='Cod_Produto',
        how='left'
    )
    
     # Renomeia as colunas para evitar conflitos
    df_checklist = df_checklist.rename(columns={
        'nome_produto': 'NomeProduto',
        'idGrupo': 'IdGrupoProduto',
        'idoperacaoServico': 'IdOperacaoServico'
    })
    
       return df_checklist