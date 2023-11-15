from flask import Blueprint, render_template, jsonify, request
import pandas as pd
import os
import pygsheets
from routes.funcoesGerais import *


adiciona_funcionario = Blueprint(
    "adiciona_funcionario",
    __name__,
    static_folder="static",
    template_folder="templates",
)


@adiciona_funcionario.route("/adiciona_funcionario", methods=["POST"])
def adiciona_funcionario_f():
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
