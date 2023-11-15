from flask import Blueprint, render_template, jsonify, request
import pandas as pd
import os
import pygsheets
import datetime
from routes.funcoesGerais import *

adiciona_cliente = Blueprint(
    "adiciona_cliente",
    __name__,
    static_folder="static",
    template_folder="templates",
)


@adiciona_cliente.route("/adiciona_cliente", methods=["POST"])
def adiciona_cliente_f():
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
