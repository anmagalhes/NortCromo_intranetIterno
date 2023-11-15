from flask import Blueprint, render_template, jsonify, request
import pandas as pd
import os
import pygsheets
import datetime
from routes.funcoesGerais import *

verifica_usuario = Blueprint(
    "verifica_usuario",
    __name__,
    static_folder="static",
    template_folder="templates",
)


@verifica_usuario.route("/verifica_usuario", methods=["POST"])
def verifica_usuario_f():
    userName = request.form["userName"]
    password = request.form["password"]
    aba = arquivo().worksheet_by_title("usuarios")
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


@verifica_usuario.route("/cadastrar_usuario_v2", methods=["POST"])
def cadastrar_usuario():
    userName = request.form["userName"]
    password = request.form["password"]
    token = gera_token()

    # Adicionar novo usuário ao Google Sheets
    aba = arquivo().worksheet_by_title("usuarios")
    nova_linha = [userName, password, "Não Confirmado", token]
    aba.append_table(nova_linha)

    # Redirecionar para a página de cadastro após o cadastro bem-sucedido
    return jsonify(
        retorno="Usuário cadastrado com sucesso!", token=token, userName=userName
    )


@verifica_usuario.route("/alterar_senha_v2", methods=["POST"])
def alterar_senha():
    userName = request.form["userName"]
    password = request.form["password"]
    token = gera_token()

    # Localize o usuário pelo nome de usuário e, se encontrado, atualize a
    # senha e o token
    aba = arquivo().worksheet_by_title("usuarios")
    dados = aba.get_all_values()

    for i in range(len(dados)):
        if dados[i][0] == userName:
            aba.update_value((i + 1, 1), password)
            aba.update_value((i + 1, 3), token)
            return jsonify(
                retorno="Senha alterada com sucesso!", token=token, userName=userName
            )

    return jsonify(retorno="Usuário não encontrado")


@verifica_usuario.route("/cadastrar_novo_usuario", methods=["POST"])
def cadastrar_novo_usuario():
    return render_template("cadastrar_usuario.html")
