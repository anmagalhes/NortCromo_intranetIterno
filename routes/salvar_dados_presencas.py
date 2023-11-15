import traceback
from flask import Blueprint, render_template, jsonify, request
import pandas as pd
import os
import datetime
import pygsheets
import threading
from routes.funcoesGerais import *
from threading import Lock

lock = threading.Lock()

salvar_dados_presencas = Blueprint(
    "salvar_dados_presencas",
    __name__,
    static_folder="static",
    template_folder="templates",
)


@salvar_dados_presencas.route("/salvar_dados_presencas", methods=["POST"])
def salvar_dados_presencas_f():
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
