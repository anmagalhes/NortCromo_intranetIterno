import threading
import traceback
from flask import Flask, render_template, jsonify, request, redirect, url_for
import requests
import pygsheets
import os
import json
import random
import string
import numpy as np
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from googleapiclient.discovery import build
from threading import Lock
import pandas as pd


credencias = pygsheets.authorize(
    service_file=os.getcwd() + "/sistemasuelopro_googleConsole.json"
)


# Defina a variável de trava para evitar problemas de concorrência
lock = threading.Lock()

def gerar_ids(aba, quantidade):
    try:
        # Obtenha a sequência atual da coluna de IDs
        coluna_sequencia = aba.get_col(1)[1:]

        # Converta os valores não vazios para inteiros e obtenha o máximo
        coluna_sequencia = [
            int(value) if value.strip() != "" else 0 for value in coluna_sequencia
        ]

        # Calcule o próximo ID na sequência
        max_id = int(max(coluna_sequencia, default=0))
        proximos_ids = list(range(max_id + 1, max_id + 1 + quantidade))

        return proximos_ids

    except Exception as e:
        print("Erro ao gerar IDs. Erro:", str(e))
        return []


def inserir_linhas(aba, valores, ids):
    try:
        with lock:
            # Obtenha a primeira coluna (coluna de IDs)
            coluna_ids = aba.get_col(1)

        # Converta os valores não vazios para inteiros e obtenha o máximo
        ids_existentes = [int(value) for value in coluna_ids[1:] if value.strip()]

        # Obtenha o próximo ID na sequência
        proximo_id = int(max(ids_existentes, default=0)) + 1

        # Converta os IDs para string antes de adicionar à lista de valores
        valores[0] = str(proximo_id)

        # Certifique-se de que todos os valores sejam convertidos para strings
        # antes da inserção
        valores = [str(val) if val is not None else "" for val in valores]

        # Insira uma nova linha com os dados atualizados
        aba.append_table(
            values=[valores],
            start=None,
            end=None,
            dimension="ROWS",
            overwrite=False,
        )

        return True, proximo_id

    except Exception as e:
        print("Erro ao inserir linha. Valores:", valores)
        print("Erro:", str(e))
        return False, None


app = Flask(__name__)  # Declarar o Objeto do Flask.

arquivo = credencias.open_by_url(
    "https://docs.google.com/spreadsheets/d/1v654Gt4hmzRPZmsd4W85yiLf2gSeBiKNsMjdnvC8W9A/"
)

# Variáveis globais para armazenar os DataFrames  - BIBLIOTECA PANDAS X GOOGLESHEET
df_funcionarios = None
df_obras = None
df_presenca_obras = None
df_relatorio_detalhado = None
df_relatorio_acumulado = None

# Carregar dados das planilhas - BIBLIOTECA PANDAS X GOOGLESHEET
def carregar_dados_gs(aba):
    dados = aba.get_all_values()
    return pd.DataFrame(data=dados[1:], columns=dados[0])

# Defina o DataFrame inicial como vazio
df_relatorio_detalhado = pd.DataFrame()

# Rota para processar o formulário e gerar os DataFrames - BILIBOTECA PANDAS 
@app.route('/gerar_relatorio', methods=['POST'])
def gerar_relatorio():
        try:
            
            global df_funcionarios, df_obras, df_presenca_obras, df_relatorio_detalhado, df_relatorio_acumulado
            
            # Carregar dados da planilha "Funcionarios"
            funcionarios_aba = arquivo.worksheet_by_title("funcionarios")
            df_funcionarios = carregar_dados_gs(funcionarios_aba)


            # Carregar dados da planilha "Obras"
            obras_aba = arquivo.worksheet_by_title("obras")
            df_obras = carregar_dados_gs(obras_aba)


            # Carregar dados da planilha "Presenca_Obras"
            presenca_obras_aba = arquivo.worksheet_by_title("presenca_Obras")
            df_presenca_obras = carregar_dados_gs(presenca_obras_aba)
        

            # Unir DataFrames
            df_relatorio_detalhado = pd.merge(df_presenca_obras, df_funcionarios, on='Id_funcionario', how='inner')
            df_relatorio_detalhado = pd.merge(df_relatorio_detalhado, df_obras, on='id_Obra', how='inner')

            # Exemplo de relatório detalhado
            # df_relatorio_detalhado.to_csv('/caminho/para/relatorio_detalhado.csv', index=False)

            # Exemplo de relatório acumulado
            df_relatorio_acumulado = df_relatorio_detalhado.groupby(['Nome_funcionario', 'Cpf_funcionario', 'Nome_obra', 'Periodo_Presenca']).agg({
                'Valor_servico': 'sum',
                'Outra_Coluna': 'mean',  # Adicione mais colunas conforme necessário
            }).reset_index()

            return jsonify({'status': 'success'})

        except Exception as e:
            print("Erro ao gerar relatório:", str(e))
            return jsonify({'error': f'Erro ao gerar relatório: {str(e)}'})

# ..........................................///..........................................///......................
# Rota para obter relatório detalhado
@app.route('/relatorio_detalhado', methods=['GET'])
def obter_relatorio_detalhado():
    try:
        # Verifique se o DataFrame possui dados
        if df_relatorio_detalhado.empty:
            return jsonify({'error': 'O relatório detalhado ainda não foi gerado.'})
        else:
            return jsonify(df_relatorio_detalhado.to_dict(orient='records'))
    except Exception as e:
        print("Erro ao obter relatório detalhado:", str(e))
        return jsonify({'error': f'Erro ao obter relatório detalhado: {str(e)}'})

# Rota para obter relatório acumulado
@app.route('/relatorio_acumulado', methods=['GET'])
def obter_relatorio_acumulado():
    try:
        # Verifique se o DataFrame possui dados
        if df_relatorio_acumulado.empty:
            return jsonify({'error': 'O relatório acumulado ainda não foi gerado.'})
        else:
            return jsonify(df_relatorio_acumulado.to_dict(orient='records'))
    except Exception as e:
        print("Erro ao obter relatório acumulado:", str(e))
        return jsonify({'error': f'Erro ao obter relatório acumulado: {str(e)}'})
    
    
# INICIAR TODAS AS ROTAS COMPLETAS
@app.route("/lista_obras")
def lista_obras():
    try:
        obras_aba = arquivo.worksheet_by_title("obras")
        dados_obras = obras_aba.get_all_values()
        df_obras = pd.DataFrame(data=dados_obras[1:], columns=dados_obras[0])
        obras_ok = df_obras[df_obras["Status"] == "OK"]
        obras_lista = obras_ok.to_dict(orient="records")

        print("Obras carregadas com sucesso:", obras_lista)  # Adicione logs
        return jsonify({"obras": obras_lista})

    except Exception as e:
        return jsonify({"error": f"Erro ao carregar obras: {str(e)}"})


@app.route("/detalhes_obra/<obra_id>", methods=["GET", "POST"])
def detalhes_obra(obra_id):
    try:
        obras_aba = arquivo.worksheet_by_title("obras")
        dados_obras = obras_aba.get_all_values()
        df_obras = pd.DataFrame(data=dados_obras[1:], columns=dados_obras[0])
        print(df_obras)

        # Ajuste para o nome correto da coluna que representa o ID da obra
        obra_selecionada = df_obras[df_obras["id_Obra"] == obra_id].to_dict(
            orient="records"
        )

        # Retorna os detalhes da obra como JSON
        return jsonify(obra_selecionada[0])

    except Exception as e:
        app.logger.error(f"Erro ao carregar detalhes da obra: {str(e)}")
        return jsonify({"error": f"Erro ao carregar detalhes da obra: {str(e)}"})


@app.route("/detalhes_obra", methods=["GET", "POST"])
def detalhes_obra_sem_id():
    try:
        # Obtenha os parâmetros da consulta
        obra_id = request.args.get("id_Obra")
        obra_nome = request.args.get("obra_nome")

        print(obra_nome)
        print(obra_id)

        # Renderize a nova página com os detalhes da obra
        return render_template(
            "detalhes_obra.html", id_Obra=obra_id, obra_nome=obra_nome
        )

    except Exception as e:
        app.logger.error(f"Erro ao carregar detalhes da obra: {str(e)}")
        return jsonify({"error": f"Erro ao carregar detalhes da obra: {str(e)}"})


@app.route('/presenca_funcionarios/<obra_id>', methods=['GET'])
def presenca_funcionarios(obra_id):
    # Lógica para obter e retornar a presença dos funcionários para a obra com ID igual a obra_id
    # ...

 @app.route('/relatorio_presenca/<obra_id>', methods=['GET'])
 def relatorio_presenca(obra_id):
    # Lógica para obter e retornar o relatório de presença para a obra com ID igual a obra_id
    # ...

  @app.route("/adiciona_funcionario", methods=["POST"])
  def adiciona_funcionario():
    try:
        # Selecione a aba correta (você já deve ter esse código)
        aba = arquivo.worksheet_by_title("funcionarios")
        dados_da_planilha = aba.get_all_values()

        coluna_sequencia = aba.get_col(1)
        coluna_sequencia = coluna_sequencia[1:]
        coluna_sequencia = [
            int(value) if value.strip() != "" else 0 for value in coluna_sequencia
        ]
        coluna_sequencia = int(max(coluna_sequencia)) + 1

        # Receba os dados do front-end
        dados = request.get_json()

        # Obtenha o próximo ID "Id_funcionario"
        prox_id = coluna_sequencia

        # Use o próximo ID como "Id_funcionario" nos dados
        dados["Id_funcionario"] = prox_id

        # Mapeie os campos do frontend para as colunas do Google Sheets
        mapeamento = {
            "Id_funcionario": "idPCP",
            "nomeCompleto": "Nome_funcionario",
            "cpf": "Cpf_funcionario",
            "rg": "Rg_funcionario",
            "dataAdminisao": "DataAdminisao_funcionario",
            "ufRg": "Uf_Rg_funcionario",
            "sexo": "Sexo_funcionario",
            "dataNascimento": "DataNascimento_funcionario",
            "tituloEleitoral": "TituloEleitoral_funcionario",
            "zona": "Zona_funcionario",
            "secao": "Secao_funcionario",
            "dataEmissaoTitulo": "DataEmissaoTitulo_funcionario",
            "municipio": "Municipio_funcionario",
            "": "",
            "pis": "Pis_funcionario",
            "": "",
            "cep": "Cep_funcionario",
            "rua": "Rua_funcionario",
            "bairro": "Bairro_funcionario",
            "uf": "Uf_funcionario",
            "cidade": "Cidade_funcionario",
            "numero": "Numero",
            "complemento": "Complemento",
            "ddFuncionario": "DD_Funcionario",
            "fixoFuncionario": "telefones2",
            "whatsFuncionario": "telefones3",
            "funcao": "Cargo_Funcionario",
            "statusFuncionario": "Status_Funcionario",
            "salario": "SalarioMensal_Funcionario",
            "valorUltimoSalario": "Valor_UltimoSalario",
            "diaristaFuncionario": "Diarista_Funcionario",
            "valeTransporteFuncionario": "ValeTransporte_Funcionario",
            "valorTranporteUlimoFuncionario": "ValorTranporteUlimo_Funcionario",
            "descontoAlimentacaoFuncionario": "Desconto_Alimentacao_Funcionario",
            "tipoSalario": "tipoSalario_Funcionario",
            "caixa": "Caixa_Pagamento",
            "formapag": "Forma_Pagamento",
            # Mapeie outros campos aqui
        }

        # Crie um dicionário de valores a serem inseridos/atualizados no Google
        # Sheets
        valores = {}

        # Itere pelos campos do frontend e mapeie-os para as colunas
        # correspondentes
        for campo_frontend, coluna_sheet in mapeamento.items():
            if campo_frontend in dados:
                valores[coluna_sheet] = dados[campo_frontend]
            else:
                # Define para vazio se o campo não estiver presente nos dados
                valores[coluna_sheet] = ""

        # Converta os valores em uma lista antes de inseri-los
        valores_list = list(valores.values())

        # Insira uma nova linha com os dados
        aba.append_table(
            values=[valores_list],
            start="A2",
            end=None,
            dimension="ROWS",
            overwrite=False,
        )

        return jsonify(retorno="Deu certo!")
    except Exception as e:
        return jsonify(retorno="Algo deu errado: " + str(e))


@app.route("/ler_dadosFuncionarios", methods=["POST"])
def ler_dadosFuncionarios():
    try:
        # Selecione a aba correta (você já deve ter esse código)
        aba = arquivo.worksheet_by_title("funcionarios")

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
            "Id_funcionario": "idPCP",
            "Nome_funcionario": "nomeCompleto",
            "Cpf_funcionario": "cpf",
            "Rg_funcionario": "rg",
            "dataAdminisao": "dataAdminisao",
            "Uf_Rg_funcionario": "ufRg",
            "Sexo_funcionario": "sexo",
            "DataNascimento_funcionario": "dataNascimento",
            "TituloEleitoral_funcionario": "tituloEleitoral",
            "Zona_funcionario": "zona",
            "Secao_funcionario": "secao",
            "DataEmissaoTitulo_funcionario": "dataEmissaoTitulo",
            "Municipio_funcionario": "municipio",
            "": "",
            "Pis_funcionario": "pis",
            "": "",
            "Cep_funcionario": "cep",
            "Rua_funcionario": "rua",
            "Bairro_funcionario": "bairro",
            "Uf_funcionario": "uf",
            "Cidade_funcionario": "cidade",
            "numero": "Numero",
            "complemento": "Complemento",
            "ddFuncionario": "DD_Funcionario",
            "fixoFuncionario": "telefones2",
            "whatsFuncionario": "telefones3",
            "Cargo_Funcionario": "funcao",
            "statusFuncionario": "Status_Funcionario",
            "salario": "SalarioMensal_Funcionario",
            "valorUltimoSalario": "Valor_UltimoSalario",
            "diaristaFuncionario": "Diarista_Funcionario",
            "valeTransporteFuncionario": "ValeTransporte_Funcionario",
            "valorTranporteUlimoFuncionario": "ValorTranporteUlimoFuncionario",
            "descontoAlimentacaoFuncionario": "Desconto_Alimentacao_Funcionario",
            "tipoSalario_Funcionario": "tipoSalario",
            "Caixa_Pagamento": "caixa",
            "Forma_Pagamento": "formapag",
            # Mapeie outros campos aqui
        }

        # Inicialize uma lista para armazenar os dados mapeados
        dados_mapeados = []

        # Itere pelas linhas da planilha
        for linha in dados:
            dados_mapeados.append(
                {mapeamento[coluna]: valor for coluna, valor in zip(mapeamento, linha)}
            )

        print(dados_mapeados)
        # Retorne os dados mapeados como JSON
        return jsonify(retorno=dados_mapeados)
    except Exception as e:
        return jsonify(retorno="Algo deu errado: " + str(e))


@app.route("/", methods=["GET"])
def index_1():
    userName = request.cookies.get("userName")
    token = request.cookies.get("token")

    if userName and token and confere_token(userName, token):
        # O usuário já está autenticado, redirecione para outra página (por
        # exemplo, 'estrutura.html').
        return render_template("estrutura.html")
    else:
        # O usuário não está autenticado, então redirecione para a página de
        # login.
        return render_template("tela_de_login.html")


@app.route("/verificador_inicial", methods=["POST"])
def verificador_inicial():
    userName = request.form["userName"]
    token = request.form["token"]

    if confere_token(userName, token):
        return render_template("estrutura.html")
    else:
        return render_template("tela_de_login.html")


def gera_token():
    token = "".join(
        random.choice(string.ascii_letters + string.digits) for _ in range(50)
    )
    return token


def confere_token(userName, token):
    aba = arquivo.worksheet_by_title("usuarios")
    dados = aba.get_all_values()

    for i in range(len(dados)):
        if dados[i][0] == userName:
            if dados[i][2] == token:
                return True
    return False


@app.route("/verifica_usuario", methods=["POST"])
def verifica_usuario():
    userName = request.form["userName"]
    password = request.form["password"]
    aba = arquivo.worksheet_by_title("usuarios")
    dados = aba.get_all_values()

    for i in range(len(dados)):
        if dados[i][0] == userName:
            if dados[i][1] == password:
                token = gera_token()
                aba.update_value((i + 1, 3), token)
                return jsonify(
                    retorno="Usuário Válido!", token=token, userName=dados[i][0]
                )
    return jsonify(retorno="Usuário Inválido!")


@app.route("/cadastrar_usuario_v2", methods=["POST"])
def cadastrar_usuario():
    userName = request.form["userName"]
    password = request.form["password"]
    token = gera_token()

    # Adicionar novo usuário ao Google Sheets
    aba = arquivo.worksheet_by_title("usuarios")
    nova_linha = [userName, password, "Não Confirmado", token]
    aba.append_table(nova_linha)

    # Redirecionar para a página de cadastro após o cadastro bem-sucedido
    return jsonify(
        retorno="Usuário cadastrado com sucesso!", token=token, userName=userName
    )


@app.route("/alterar_senha_v2", methods=["POST"])
def alterar_senha():
    userName = request.form["userName"]
    password = request.form["password"]
    token = gera_token()

    # Localize o usuário pelo nome de usuário e, se encontrado, atualize a
    # senha e o token
    aba = arquivo.worksheet_by_title("usuarios")
    dados = aba.get_all_values()

    for i in range(len(dados)):
        if dados[i][0] == userName:
            aba.update_value((i + 1, 1), password)
            aba.update_value((i + 1, 3), token)
            return jsonify(
                retorno="Senha alterada com sucesso!", token=token, userName=userName
            )

    return jsonify(retorno="Usuário não encontrado")


# Mantenha a rota /cadastro existente para exibir o formulário de cadastro


@app.route("/cadastrar_novo_usuario", methods=["POST"])  # Altere a rota aqui
def cadastrar_novo_usuario():
    return render_template("cadastrar_usuario.html")


@app.route("/buscar_funcionarios_presenca", methods=["POST"])
def buscar_funcionarios_presenca():
    try:
        # Configurar filtros padrão
        filtros = ["PEDREIRO", "SERVENTE", "DIARISTA"]

        # Selecione a aba correta (você já deve ter esse código)
        aba = arquivo.worksheet_by_title("funcionarios")

        # Obtenha todos os valores da planilha
        dados_da_planilha = aba.get_all_values()

        # Filtra as linhas com base no filtro de cargo
        resultados = []

        for row in dados_da_planilha:
            # Verifique se a coluna Z (índice 25) corresponde ao filtro de
            # cargo
            if len(row) > 25 and row[25] in filtros:
                print(filtros)
                resultado = {
                    "Id_funcionario": row[0],
                    "Nome_funcionario": row[1]
                    # Adicione outros campos aqui conforme necessário
                }
                resultados.append(resultado)

        return jsonify(resultados)

    except Exception as e:
        return jsonify({"error": str(e)})


@app.route("/muda_de_tela", methods=["POST"])
def muda_de_tela():  # associa uma função a esta rota.
    qual_template = request.form["qual_template"]
    return render_template(qual_template)


@app.route("/muda_de_tela_login", methods=["POST"])
def muda_de_tela_login():
    qual_template = request.form.get("qual_template")
    if qual_template:
        # Aqui você pode adicionar lógica adicional, se necessário, para verificar se qual_template é válido.
        # Por exemplo, você pode limitar quais templates os usuários podem
        # acessar.
        return render_template(qual_template)
    else:
        return "Erro: Nenhum template especificado na solicitação POST", 400


@app.route("/muda_de_tela_presenca", methods=["POST"])
def muda_de_tela_presenca():  # associa uma função a esta rota.
    qual_template = request.form["qual_template"]
    return render_template(qual_template)


@app.route("/get_pedreiros_data", methods=["GET"])
def get_pedreiros_data():
    aba = arquivo.worksheet_by_title("base_de_dados")
    all_data = aba.get_all_records()
    pedreiros_data = [
        {"ID": row["ID"], "Nome": row["Nome"]}
        for row in all_data
        if row["Cargo"] == "Pedreiro"
    ]
    return jsonify(pedreiros_data)


@app.route("/submenu_muda_de_tela", methods=["POST"])
def submenu_muda_de_tela():
    print("Requisição recebida")  # Adicione esta linha
    qual_template = request.form["qual_template"]
    return render_template(qual_template)


@app.route("/consulta_pedreiros", methods=["GET"])
def consulta_pedreiros():
    aba = arquivo.worksheet_by_title("base_de_dados")

    registros = aba.get_all_values(returnas="matrix")

    # Filtra os registros pela coluna F (índice 5) onde o valor é 'pedreiro'
    pedreiros = [row for row in registros if row[5].lower() == "pedreiro"]

    # Formata a resposta para enviar de volta ao cliente
    resposta = []
    for pedreiro in pedreiros:
        resposta.append(
            {
                # ajuste os índices conforme a sua planilha
                "nome": pedreiro[0],
                "integral": False,
                "meio_dia": False,
            }
        )

    return jsonify(resposta)


@app.route("/upload", methods=["POST"])
def upload():
    if "photo" in request.files:
        photo = request.files["photo"]
        photo.save(os.path.join("uploads", photo.filename))
        return "uploaded foto,  realizada com sucesso"
    return "falhar na foto"


@app.route("/index_2", methods=["GET"])
def index_2():  # associa uma função a esta rota.
    # Retorna o resultado desta rota.
    return render_template("produtoDate.html")


@app.route("/meu_request", methods=["POST"])
def meu_request():
    aba = arquivo.worksheet_by_title("base_de_dados")
    celula_A1 = aba.get_row(1)[0]
    return jsonify(retorno=celula_A1)


@app.route("/escrever", methods=["POST"])
def escrever():
    o_que_escrever = request.form["o_que_escrever"]

    aba = arquivo.worksheet_by_title("base_de_dados")
    aba.update_values("A1", values=[[o_que_escrever]])
    return jsonify(retorno="Tudo Certo")


@app.route("/adiciona_cliente", methods=["POST"])
def adiciona_cliente():
    try:
        o_que_escrever = request.form["o_que_escrever"]

        aba = arquivo.worksheet_by_title("base_de_dados")

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


@app.route("/salvar_dados_presencas", methods=["POST"])
def salvar_dados_presencas():
    try:
        # Selecione a aba correta (você já deve ter esse código)
        aba = arquivo.worksheet_by_title("presenca_Obras")
        aba_funcionarios = arquivo.worksheet_by_title("funcionarios")

        # Leitura dos dados para DataFrames
        df_presenca_obras = aba.get_as_df()
        df_funcionarios = aba_funcionarios.get_as_df()

        # Obtenha os dados da solicitação POST
        dados = request.get_json()
        print("Dados recebidos:", dados)

        # Obtenha o número de IDs a serem gerados
        num_ids = len(dados)

        # Gere os IDs necessários
        ids = gerar_ids(aba, num_ids)

        # Verifique se houve algum problema na geração de IDs
        if not ids:
            return jsonify(retorno="Erro ao gerar IDs.")

        # Crie um DataFrame vazio para armazenar os resultados
        result_df = pd.DataFrame()

        # Use um loop para iterar sobre os dados e IDs
        for item, id_presenca in zip(dados, ids):
            # Crie um DataFrame temporário com base nos dados do front-end
            temp_df = pd.DataFrame(
                {
                    "Id_funcionario": [int(item.get("id", ""))],
                    "Nome_funcionario": [item.get("nome", "").upper()],
                    "TipoSalario_Funcionario": [
                        item.get("tipoSalario_Funcionario", "")
                    ],
                    "SalarioMensal_Funcionario": [
                        float(item.get("SalarioMensal_Funcionario", 0))
                    ],
                    "Valor_UltimoSalario": [float(item.get("Valor_UltimoSalario", 0))],
                    "Periodo_Presenca": [item.get("Periodo_Presenca", "")],
                }
            )

            # Concatene o DataFrame temporário com o resultado principal
            result_df = pd.concat([result_df, temp_df], ignore_index=True)

            # Verifique se a coluna 'Nome_funcionario' está presente no
            # DataFrame
            if "Nome_funcionario" in result_df.columns:
                # Formate as colunas conforme necessário
                result_df["Nome_funcionario"] = result_df[
                    "Nome_funcionario"
                ].str.upper()

                # Verifique se a coluna 'Periodo_Presenca' está presente no
                # DataFrame
                if (
                    "SalarioMensal_Funcionario" in result_df.columns
                    and "Periodo_Presenca" in result_df.columns
                ):
                    # Realize os cálculos condicionais
                    for index, row in result_df.iterrows():
                        id_funcionario = int(row["Id_funcionario"])
                        periodo_presenca = row["Periodo_Presenca"]

                        # Verifique se Valor_UltimoSalario está vazio ou nulo
                        if (
                            pd.isnull(row["Valor_UltimoSalario"])
                            or row["Valor_UltimoSalario"] == ""
                        ):
                            # Se Valor_UltimoSalario estiver vazio, use
                            # SalarioMensal_Funcionario
                            result_df.at[index, "Valor_UltimoSalario"] = row[
                                "SalarioMensal_Funcionario"
                            ]
                        else:
                            # Se não estiver vazio, ajuste conforme necessário
                            if periodo_presenca == "DIA INTEIRO":
                                # Divida por 2 se o tipo for DIA INTEIRO
                                result_df.at[index, "Valor_UltimoSalario"] /= 2
                            elif periodo_presenca == "1/2 PERIODO":
                                # Multiplique por 2 se o tipo for 1/2 PERIODO
                                result_df.at[index, "Valor_UltimoSalario"] *= 2
                else:
                    print(
                        "A coluna 'Periodo_Presenca' não foi encontrada no DataFrame."
                    )

                # Adicione a nova coluna "Nome_Usuario" ao seu mapeamento e
                # obtenha o nome de usuário
                nome_usuario = request.cookies.get("userName").upper()

                # Adicione a nova coluna "Data_Hora" com a data e hora atual
                data_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

                # Formate as colunas conforme necessário
                nome_funcionario = item.get("nome", "").upper()
                valorInputObra = item.get("valorInputObra", "").upper()
                id_funcionario = int(item.get("id", ""))
                Data_presenca_Obras = datetime.strptime(
                    item.get("dataCapturada", ""), "%Y-%m-%d"
                ).strftime("%d/%m/%Y")

                # Inicialize a variável tipo_salario antes do bloco condicional
                tipo_salario = ""
                salario_meio_periodo = 0  # Defina um valor padrão

                # Agora você pode continuar com os cálculos condicionais para
                # Valor_servico
                if "checkboxDiaInteiro" in item and item["checkboxDiaInteiro"]:
                    print(item["checkboxDiaInteiro"])

                    # Obtenha o valor do SalarioMensal_Funcionario para o ID
                    # correspondente
                    id_funcionario = int(item.get("id", ""))
                    salario_dia_inteiro = df_funcionarios.loc[
                        df_funcionarios["Id_funcionario"] == id_funcionario,
                        "SalarioMensal_Funcionario",
                    ].iloc[0]

                    # Calcule o Valor_servico com base no
                    # SalarioMensal_Funcionario e no tipoSalario_Funcionario
                    valor_servico = (
                        salario_dia_inteiro / 2
                    )  # Divida por 2 para "DIA INTEIRO"

                    # Adicione uma verificação para 'TipoSalario_Funcionario'
                    if "TipoSalario_Funcionario" in df_funcionarios.columns:
                        tipo_salario = df_funcionarios.loc[
                            df_funcionarios["Id_funcionario"] == id_funcionario,
                            "TipoSalario_Funcionario",
                        ].iloc[0]

                    # Obtenha o valor do SalarioMensal_Funcionario para o ID
                    # correspondente
                    id_funcionario = int(item.get("id", ""))
                    salario_dia_inteiro = df_funcionarios.loc[
                        df_funcionarios["Id_funcionario"] == id_funcionario,
                        "SalarioMensal_Funcionario",
                    ].iloc[0]

                    # Verifique se já está configurado como "DIA INTEIRO" e o
                    # checkbox está marcado como "MEIO PERIODO"
                    if (
                        tipo_salario == "DIA INTEIRO"
                        and "checkboxMeioPeriodo" in item
                        and item["checkboxMeioPeriodo"]
                    ):
                        # Divida por 2 para "DIA INTEIRO" com checkbox "MEIO
                        # PERIODO"
                        valor_servico = salario_meio_periodo / 2
                    else:
                        valor_servico = (
                            salario_meio_periodo  # Mantenha o valor original
                        )

                    # Crie um novo dicionário para armazenar os valores
                    valores = {
                        "Id_presenca": id_presenca,
                        "Nome_funcionario": nome_funcionario,
                        "Data_presenca_Obras": Data_presenca_Obras,
                        "id_Obra": item.get("valorInputObra", ""),
                        "Valor_servico": item.get("Valor_servico", ""),
                        "Nome_Usuario": nome_usuario,
                        "Data_salvamento": data_hora,
                        "Id_funcionario": id_funcionario,
                        "Periodo_Presenca": "DIA INTEIRO",
                    }

                elif "checkboxMeioPeriodo" in item and item["checkboxMeioPeriodo"]:
                    # Obtenha o valor do SalarioMensal_Funcionario para o ID
                    # correspondente
                    id_funcionario = int(item.get("id", ""))

                    # Adicione uma verificação antes de acessar a coluna
                    if "TipoSalario_Funcionario" in df_funcionarios.columns:
                        tipo_salario = df_funcionarios.loc[
                            df_funcionarios["Id_funcionario"] == id_funcionario,
                            "TipoSalario_Funcionario",
                        ].iloc[0]
                    else:
                        # Faça algo se a coluna não estiver presente (ex:
                        # imprima uma mensagem de aviso)
                        print(
                            "A coluna 'TipoSalario_Funcionario' não está presente no DataFrame."
                        )
                        # Pode ser necessário retornar uma resposta adequada
                        # para o usuário ou registrar informações sobre o
                        # problema.

                    salario_meio_periodo = df_funcionarios.loc[
                        df_funcionarios["Id_funcionario"] == id_funcionario,
                        "SalarioMensal_Funcionario",
                    ].iloc[0]

                    # Verifique se já está configurado como "DIA INTEIRO" e o
                    # checkbox está marcado como "MEIO PERIODO"
                    if (
                        tipo_salario == "DIA INTEIRO"
                        and "checkboxMeioPeriodo" in item
                        and item["checkboxMeioPeriodo"]
                    ):
                        # Divida por 2 para "DIA INTEIRO" com checkbox "MEIO
                        # PERIODO"
                        valor_servico = salario_meio_periodo / 2
                    else:
                        valor_servico = (
                            salario_meio_periodo  # Mantenha o valor original
                        )

                    # Crie um novo dicionário para armazenar os valores
                    valores = {
                        "Id_presenca": id_presenca,
                        "Nome_funcionario": nome_funcionario,
                        "Data_presenca_Obras": Data_presenca_Obras,
                        "id_Obra": item.get("valorInputObra", ""),
                        "Valor_servico": valor_servico,
                        "Nome_Usuario": nome_usuario,
                        "Data_salvamento": data_hora,
                        "Id_funcionario": id_funcionario,
                        "Periodo_Presenca": "1/2 PERIODO",
                    }

                    # Ajuste do Valor_UltimoSalario se necessário
                    if (
                        pd.isnull(row["Valor_UltimoSalario"])
                        or row["Valor_UltimoSalario"] == ""
                    ):
                        # Se Valor_UltimoSalario estiver vazio, use
                        # SalarioMensal_Funcionario
                        result_df.at[index, "Valor_UltimoSalario"] = row[
                            "SalarioMensal_Funcionario"
                        ]
                    else:
                        # Se não estiver vazio, ajuste conforme necessário
                        # Exemplo: multiplicar por 2 para "Meio Período"
                        result_df.at[index, "Valor_UltimoSalario"] *= 2
            else:
                continue  # Pula a linha se ambos os checkboxes são undefined

            # Certifique-se de que todos os valores sejam convertidos para
            # strings antes da inserção
            valores = [str(val) if val is not None else "" for val in valores.values()]

            # Insira uma nova linha com os dados atualizados
            success, _ = inserir_linhas(aba, valores, None)

            # Se ocorrer algum erro, pare o loop
            if not success:
                raise Exception("Erro ao inserir linhas.")

        return jsonify(retorno="Dados salvos com sucesso!")

    except Exception as e:
        traceback.print_exc()
        print("Algo deu errado:", str(e))
        return jsonify(retorno="Algo deu errado: " + str(e))





if __name__ == "__main__":
    app.run(debug=True)
