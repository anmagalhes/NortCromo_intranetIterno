from flask import Blueprint, render_template, jsonify, request
import pandas as pd
import os
import pygsheets
from routes.funcoesGerais import *


formulario_relatorio2 = Blueprint(
    "formulario_relatorio2",
    __name__,
    static_folder="static",
    template_folder="templates",
)


@formulario_relatorio2.route("/formulario_relatorio2", methods=["POST"])
def formulario_relatorio2_f():
    try:
        global df_funcionarios, df_obras, df_presenca_obras, df_relatorio_detalhado, df_relatorio_acumulado

        # Obter parâmetros do formulário
        data = request.get_json()
        obra_id = data.get("obra_id")
        periodo_inicial = data.get("periodo_inicial")
        periodo_final = data.get("periodo_final")

        # Carregar dados da planilha "Funcionarios"
        funcionarios_aba = arquivo().worksheet_by_title("funcionarios")
        df_funcionarios = carregar_dados_gs(funcionarios_aba)
        print(df_funcionarios)

        # Carregar dados da planilha "Obras"
        obras_aba = arquivo().worksheet_by_title("obras")
        df_obras = carregar_dados_gs(obras_aba)
        print(df_obras)

        # Carregar dados da planilha "Presenca_Obras"
        presenca_obras_aba = arquivo().worksheet_by_title("presenca_Obras")
        df_presenca_obras = carregar_dados_gs(presenca_obras_aba)

        # Filtrar DataFrames com base nos parâmetros do formulário
        df_funcionarios_filtrado = df_funcionarios[
            df_funcionarios["obra_id"] == obra_id
        ]
        df_obras_filtrado = df_obras[df_obras["obra_id"] == obra_id]
        df_presenca_obras_filtrado = df_presenca_obras[
            (df_presenca_obras["obra_id"] == obra_id)
            & (df_presenca_obras["data"] >= periodo_inicial)
            & (df_presenca_obras["data"] <= periodo_final)
        ]

        # Unir DataFrames
        df_relatorio_detalhado = pd.merge(
            df_presenca_obras_filtrado,
            df_funcionarios_filtrado,
            on="Id_funcionario",
            how="inner",
        )
        df_relatorio_detalhado = pd.merge(
            df_relatorio_detalhado, df_obras_filtrado, on="id_Obra", how="inner"
        )

        # Retornar os DataFrames como dicionários
        relatorio_detalhado_dict = df_relatorio_detalhado.to_dict(orient="records")
        relatorio_acumulado_dict = df_relatorio_acumulado.to_dict(orient="records")

        # Retorne ambos os relatórios em um único objeto JSON
        return jsonify(
            {
                "status": "success",
                "relatorio_detalhado": relatorio_detalhado_dict,
                "relatorio_acumulado": relatorio_acumulado_dict,
            }
        )

    except Exception as e:
        print("Erro ao gerar relatório:", str(e))
        return jsonify({"error": f"Erro ao gerar relatório: {str(e)}"})
