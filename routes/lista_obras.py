from flask import Blueprint, render_template, jsonify
import pandas as pd
import os
import pygsheets
from routes.funcoesGerais import *

lista_obras = Blueprint(
    "lista_obras", __name__, static_folder="static", template_folder="templates"
)


@lista_obras.route("/lista_obras")
def lista_obras_f():
    try:
        obras_aba = arquivo().worksheet_by_title("obras")
        dados_obras = obras_aba.get_all_values()
        df_obras = pd.DataFrame(data=dados_obras[1:], columns=dados_obras[0])
        obras_ok = df_obras[df_obras["Status"] == "OK"]
        obras_lista = obras_ok.to_dict(orient="records")

        print("Obras carregadas com sucesso:", obras_lista)
        return jsonify({"obras": obras_lista})

    except Exception as e:
        return jsonify({"error": f"Erro ao carregar obras: {str(e)}"})
