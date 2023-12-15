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
import sys
from routes.funcoesGerais import *


credencias = pygsheets.authorize(
    service_file=os.getcwd() + "/sistemaNortrCromo_googleConsole.json"
)

app = Flask(__name__)

from routes.lista_obras import lista_obras
from routes.adiciona_funcionario import adiciona_funcionario
from routes.buscar_funcionarios_presenca import buscar_funcionarios_presenca
from routes.detalhes_obra import detalhes_obra
from routes.formulario_relatorio2 import formulario_relatorio2
from routes.get_pedreiros_data import get_pedreiros_data
from routes.ler_dadosFuncionarios import ler_dadosFuncionarios
from routes.lista_obras import lista_obras
from routes.consulta_pedreiros import consulta_pedreiros
from routes.salvar_dados_presencas import salvar_dados_presencas
from routes.usuarios import verifica_usuario
from routes.produtos import produtos
from routes.recebimentos import recebimentos
from routes.conferencia_dados_inicias_checklist import (
    conferencia_dados_inicias_checklist,
)

from routes.clientes import clientes

app.register_blueprint(lista_obras, url_prefix="")
app.register_blueprint(adiciona_funcionario, url_prefix="")
app.register_blueprint(buscar_funcionarios_presenca, url_prefix="")
app.register_blueprint(detalhes_obra, url_prefix="")
app.register_blueprint(formulario_relatorio2, url_prefix="")
app.register_blueprint(get_pedreiros_data, url_prefix="")
app.register_blueprint(ler_dadosFuncionarios, url_prefix="")
app.register_blueprint(consulta_pedreiros, url_prefix="")
app.register_blueprint(salvar_dados_presencas, url_prefix="")
app.register_blueprint(verifica_usuario, url_prefix="")
app.register_blueprint(clientes, url_prefix="")

app.register_blueprint(conferencia_dados_inicias_checklist, url_prefix="")
app.register_blueprint(produtos, url_prefix="")
app.register_blueprint(recebimentos, url_prefix="")

arquivo = credencias.open_by_url(
    "https://docs.google.com/spreadsheets/d/15Jyo4qMmVK0JTSB95__JaVJveAOflbS1qR0qNOucEgI/"
)

df_funcionarios = None
df_obras = None
df_presenca_obras = None
df_relatorio_detalhado = None
df_relatorio_acumulado = None

df_relatorio_detalhado = pd.DataFrame()


@app.route("/TESTE")
def formulario_relatorio():
    return render_template("formulario_relatorio.html")


def confere_token(userName, token):
    # arquivo = arquivo()
    aba = arquivo.worksheet_by_title("usuarios")
    dados = aba.get_all_values()

    for i in range(len(dados)):
        if dados[i][0] == userName:
            if dados[i][2] == token:
                return True
    return False


@app.route("/ss", methods=["GET"])
def index_12():
    return render_template("camera.html")


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


@app.route("/muda_de_tela", methods=["POST"])
def muda_de_tela():  # associa uma função a esta rota.
    if verificaSeOUsuarioTemPermissao("tony", "/muda_de_tela"):
        qual_template = request.form["qual_template"]
        return render_template(qual_template)
    else:
        return "<div>Sem Permissão</div>"


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


@app.route("/submenu_muda_de_tela", methods=["POST"])
def submenu_muda_de_tela():
    print("Requisição recebida")  # Adicione esta linha
    qual_template = request.form["qual_template"]
    return render_template(qual_template)


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


def image_to_base64(image_path):
    import base64

    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
        return encoded_string


@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("file")
    # Get the current date and time
    now = datetime.now()

    # Format the date and time into the desired string format
    formatted_string = now.strftime("%Y%m%d_%H%M%S")

    if file:
        file.save("uploads/" + formatted_string + ".png")
        return jsonify({"sucesso": "Arquivo armazenado"})
    else:
        return jsonify({"error": "Não veio nenhum arquivo."})


if __name__ == "__main__":
    app.run(debug=False)