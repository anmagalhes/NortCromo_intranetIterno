from flask import Blueprint, render_template, jsonify, request
import pandas as pd
import os
import pygsheets
from routes.funcoesGerais import *


consulta_pedreiros = Blueprint(
    "consulta_pedreiros",
    __name__,
    static_folder="static",
    template_folder="templates",
)


@consulta_pedreiros.route("/consulta_pedreiros", methods=["GET"])
def consulta_pedreiros_f():
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
