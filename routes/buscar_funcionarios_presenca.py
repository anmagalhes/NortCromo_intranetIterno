from flask import Blueprint, render_template, jsonify, request
import pandas as pd
import os
import pygsheets
from routes.funcoesGerais import *


buscar_funcionarios_presenca = Blueprint(
    "buscar_funcionarios_presenca",
    __name__,
    static_folder="static",
    template_folder="templates",
)


@buscar_funcionarios_presenca.route("/buscar_funcionarios_presenca", methods=["POST"])
def buscar_funcionarios_presenca_f():
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
