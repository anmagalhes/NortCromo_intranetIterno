from flask import Flask, render_template, jsonify, request
import pygsheets
import os
import json

credencias = pygsheets.authorize(service_file = os.getcwd() + "/flask.json")

app = Flask(__name__) ## Declarar o Objeto do Flask.

@app.route("/", methods=['GET'])
def index_1(): ## associa uma função a esta rota.
    return render_template('index_1.html') ## Retorna o resultado desta rota.

@app.route("/index_2", methods=['GET'])
def index_2(): ## associa uma função a esta rota.
    return render_template('index_2.html') ## Retorna o resultado desta rota.

@app.route("/ler_dados_clientes", methods=['POST'])
def ler_dados_clientes(): 
    arquivo = credencias.open_by_url("https://docs.google.com/spreadsheets/d/1q0uYu5eB5M37ho2PqFbGigoTvsHP88OMydYFXz0_mgc/")
    aba = arquivo.worksheet_by_title("base_de_dados")
    dados = aba.get_all_values()
    return jsonify(retorno = dados)

@app.route("/escrever", methods=['POST'])
def escrever(): 
    o_que_escrever = request.form['o_que_escrever']
    arquivo = credencias.open_by_url("https://docs.google.com/spreadsheets/d/1q0uYu5eB5M37ho2PqFbGigoTvsHP88OMydYFXz0_mgc/")
    aba = arquivo.worksheet_by_title("base_de_dados")
    aba.update_values("A1", values=[[o_que_escrever]])
    return jsonify(retorno = "Tudo Certo")

@app.route("/adiciona_cliente", methods=['POST'])
def adiciona_cliente():
    try:
        json_data = request.data.decode('utf-8')
        o_que_escrever = json.loads(json_data)
        
        arquivo = credencias.open_by_url("https://docs.google.com/spreadsheets/d/1q0uYu5eB5M37ho2PqFbGigoTvsHP88OMydYFXz0_mgc/")
        aba = arquivo.worksheet_by_title("base_de_dados")

        coluna1 = aba.get_col(1)
        coluna1 = coluna1[1:] ## tirar o cabeçalho
        
        # i começa do zero, google sheets começa na 1
        # Mais por causa do cabeçalho !


        if o_que_escrever[0] == "":
            meu_id = int(max(coluna1)) + 1
            o_que_escrever[0] = meu_id
            aba.append_table(values=[o_que_escrever], start="A1", end=None, dimension='ROWS', overwrite=False)
            return jsonify(retorno = "Dado Adicionado!")
        else:
            for i in range(len(coluna1)):
                if coluna1[i] == o_que_escrever[0]:
                    aba.update_row(i + 2, o_que_escrever)
                    return jsonify(retorno = "Dado Alterado!")
        
    except Exception as e:
        return jsonify(retorno = e)

@app.route("/exclui_cliente", methods=['POST'])
def exclui_cliente():
    try:
        json_data = request.data.decode('utf-8')
        o_que_escrever = json.loads(json_data)
        
        arquivo = credencias.open_by_url("https://docs.google.com/spreadsheets/d/1q0uYu5eB5M37ho2PqFbGigoTvsHP88OMydYFXz0_mgc/")
        aba = arquivo.worksheet_by_title("base_de_dados")

        coluna1 = aba.get_col(1)
        coluna1 = coluna1[1:] ## tirar o cabeçalho
        
        # i começa do zero, google sheets começa na 1
        # Mais por causa do cabeçalho !

        if o_que_escrever[0] == "":
            meu_id = int(max(coluna1)) + 1
            o_que_escrever[0] = meu_id
            aba.append_table(values=[o_que_escrever], start="A1", end=None, dimension='ROWS', overwrite=False)
            return jsonify(retorno = "Dado Adicionado!")
        else:
            for i in range(len(coluna1)):
                if coluna1[i] == o_que_escrever[0]:
                    aba.delete_rows(i + 2)
                    return jsonify(retorno = "Dado Excluído!")
        
    except Exception as e:
        return jsonify(retorno = e)


if __name__ == '__main__':
    app.run(debug=True)
