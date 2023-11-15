from flask import Blueprint, render_template, jsonify
import pandas as pd
import os
import pygsheets
from routes.funcoesGerais import *

detalhes_obra = Blueprint(
    "detalhes_obra", __name__, static_folder="static", template_folder="templates"
)


@detalhes_obra.route("/detalhes_obra/<obra_id>", methods=["GET", "POST"])
def detalhes_obra_f(obra_id):
    try:
        obras_aba = arquivo().worksheet_by_title("obras")
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
        detalhes_obra.logger.error(f"Erro ao carregar detalhes da obra: {str(e)}")
        return jsonify({"error": f"Erro ao carregar detalhes da obra: {str(e)}"})
