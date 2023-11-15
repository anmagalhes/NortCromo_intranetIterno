from flask import Blueprint, render_template, jsonify, request
import pandas as pd
import os
import pygsheets
from routes.funcoesGerais import *

ler_dadosFuncionarios = Blueprint(
    "ler_dadosFuncionarios",
    __name__,
    static_folder="static",
    template_folder="templates",
)


@ler_dadosFuncionarios.route("/ler_dadosFuncionarios", methods=["POST"])
def ler_dadosFuncionarios_f():
    try:
        # Selecione a aba correta (você já deve ter esse código)
        aba = arquivo.worksheet_by_title("funcionarios")

        # Obtenha todos os valores da planilha
        dados_da_planilha = aba.get_all_values()

        # A primeira linha contém os nomes das colunas, que serão usados para
        # mapeamento
        colunas = dados_da_planilha[0]

        # Os dados começam da segunda linha em diante
        dados = dados_da_planilha[1:]

        # Mapeamento de colunas (mesmo mapeamento usado na função de adicionar
        # funcionário)
        mapeamento = {
            "Id_funcionario": "idPCP",
            "Nome_funcionario": "nomeCompleto",
            "Cpf_funcionario": "cpf",
            "Rg_funcionario": "rg",
            "dataAdminisao": "dataAdminisao",
            "Uf_Rg_funcionario": "ufRg",
            "Sexo_funcionario": "sexo",
            "DataNascimento_funcionario": "dataNascimento",
            "TituloEleitoral_funcionario": "tituloEleitoral",
            "Zona_funcionario": "zona",
            "Secao_funcionario": "secao",
            "DataEmissaoTitulo_funcionario": "dataEmissaoTitulo",
            "Municipio_funcionario": "municipio",
            "": "",
            "Pis_funcionario": "pis",
            "": "",
            "Cep_funcionario": "cep",
            "Rua_funcionario": "rua",
            "Bairro_funcionario": "bairro",
            "Uf_funcionario": "uf",
            "Cidade_funcionario": "cidade",
            "numero": "Numero",
            "complemento": "Complemento",
            "ddFuncionario": "DD_Funcionario",
            "fixoFuncionario": "telefones2",
            "whatsFuncionario": "telefones3",
            "Cargo_Funcionario": "funcao",
            "statusFuncionario": "Status_Funcionario",
            "salario": "SalarioMensal_Funcionario",
            "valorUltimoSalario": "Valor_UltimoSalario",
            "diaristaFuncionario": "Diarista_Funcionario",
            "valeTransporteFuncionario": "ValeTransporte_Funcionario",
            "valorTranporteUlimoFuncionario": "ValorTranporteUlimoFuncionario",
            "descontoAlimentacaoFuncionario": "Desconto_Alimentacao_Funcionario",
            "tipoSalario_Funcionario": "tipoSalario",
            "Caixa_Pagamento": "caixa",
            "Forma_Pagamento": "formapag",
            # Mapeie outros campos aqui
        }

        # Inicialize uma lista para armazenar os dados mapeados
        dados_mapeados = []

        # Itere pelas linhas da planilha
        for linha in dados:
            dados_mapeados.append(
                {mapeamento[coluna]: valor for coluna, valor in zip(mapeamento, linha)}
            )

        print(dados_mapeados)
        # Retorne os dados mapeados como JSON
        return jsonify(retorno=dados_mapeados)
    except Exception as e:
        return jsonify(retorno="Algo deu errado: " + str(e))
