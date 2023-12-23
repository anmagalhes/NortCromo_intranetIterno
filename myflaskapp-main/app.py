from flask import Flask, render_template, jsonify, request
import pygsheets
import os
import json
import random
import string

credencias = pygsheets.authorize(service_file = os.getcwd() + "/flask.json")

## Vamos colocar no PythonAnywhere.

app = Flask(__name__) ## Declarar o Objeto do Flask.

@app.route("/", methods=['GET'])
def index_1(): ## associa uma função a esta rota.
    return render_template('index.html')

@app.route("/verificador_inicial", methods=['POST'])
def verificador_inicial(): 
    userName = request.form['userName']
    token = request.form['token']
    
    if confere_token(userName, token) == True:
        return render_template('estrutura.html')
    else:
        return render_template('tela_de_login.html')


def gera_token():
    token = ''.join(random.choice(string.ascii_letters + string.digits ) for _ in range(50))
    return token

def confere_token(userName, token):
    arquivo = credencias.open_by_url("https://docs.google.com/spreadsheets/d/1q0uYu5eB5M37ho2PqFbGigoTvsHP88OMydYFXz0_mgc/")
    aba = arquivo.worksheet_by_title("usuarios")
    dados = aba.get_all_values()
    
    for i in range(len(dados)):
        if dados[i][0] == userName:
            if dados[i][2] == token:
                return True
    return False

@app.route("/verifica_usuario", methods=['POST'])
def verifica_usuario():
    userName = request.form['userName']
    password = request.form['password']

    arquivo = credencias.open_by_url("https://docs.google.com/spreadsheets/d/1q0uYu5eB5M37ho2PqFbGigoTvsHP88OMydYFXz0_mgc/")
    aba = arquivo.worksheet_by_title("usuarios")
    dados = aba.get_all_values()
    
    for i in range(len(dados)):
        if dados[i][0] == userName:
            if dados[i][1] == password:
                token = gera_token()
                aba.update_value((i + 1, 3), token)
                return jsonify(retorno = 'Usuário Válido!', token=token, userName=dados[i][0]) 
    return jsonify(retorno = "Usuário Inválido!")

@app.route("/muda_de_tela", methods=['POST'])
def muda_de_tela(): ## associa uma função a esta rota.
    qual_template = request.form['qual_template']
    return render_template(qual_template) 

@app.route("/index_2", methods=['GET'])
def index_2(): ## associa uma função a esta rota.
    return render_template('index_2.html') ## Retorna o resultado desta rota.

@app.route("/ler_dados_clientes", methods=['POST'])
def ler_dados_clientes(): 
    arquivo = credencias.open_by_url("https://docs.google.com/spreadsheets/d/1q0uYu5eB5M37ho2PqFbGigoTvsHP88OMydYFXz0_mgc/")
    aba = arquivo.worksheet_by_title("clientes")
    dados = aba.get_all_values()
    return jsonify(retorno = dados)

@app.route("/ler_dados_produtos", methods=['POST'])
def ler_dados_produtos(): 
    arquivo = credencias.open_by_url("https://docs.google.com/spreadsheets/d/1q0uYu5eB5M37ho2PqFbGigoTvsHP88OMydYFXz0_mgc/")
    aba = arquivo.worksheet_by_title("produtos")
    dados = aba.get_all_values()
    return jsonify(retorno = dados)

@app.route("/adiciona_produto", methods=['POST'])
def adiciona_produto():
    try:
        json_data = request.data.decode('utf-8')
        o_que_escrever = json.loads(json_data)
        
        arquivo = credencias.open_by_url("https://docs.google.com/spreadsheets/d/1q0uYu5eB5M37ho2PqFbGigoTvsHP88OMydYFXz0_mgc/")
        aba = arquivo.worksheet_by_title("produtos")

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

@app.route("/exclui_produto", methods=['POST'])
def exclui_produto():
    try:
        json_data = request.data.decode('utf-8')
        o_que_escrever = json.loads(json_data)
        
        arquivo = credencias.open_by_url("https://docs.google.com/spreadsheets/d/1q0uYu5eB5M37ho2PqFbGigoTvsHP88OMydYFXz0_mgc/")
        aba = arquivo.worksheet_by_title("produtos")

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

@app.route("/adiciona_cliente", methods=['POST'])
def adiciona_cliente():
    try:
        json_data = request.data.decode('utf-8')
        o_que_escrever = json.loads(json_data)
        
        arquivo = credencias.open_by_url("https://docs.google.com/spreadsheets/d/1q0uYu5eB5M37ho2PqFbGigoTvsHP88OMydYFXz0_mgc/")
        aba = arquivo.worksheet_by_title("clientes")

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
        aba = arquivo.worksheet_by_title("clientes")

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

@app.route("/lancar_venda", methods=['POST'])
def lancar_venda():
    try:
            
        arquivo = credencias.open_by_url("https://docs.google.com/spreadsheets/d/1q0uYu5eB5M37ho2PqFbGigoTvsHP88OMydYFXz0_mgc/")
        aba = arquivo.worksheet_by_title("vendas")
        
        dados_da_planilha = aba.get_all_values()

        coluna_sequencia = aba.get_col(1)
        
        coluna_sequencia = coluna_sequencia[1:]
        coluna_sequencia = list(map(int, coluna_sequencia))
        coluna_sequencia = int(max(coluna_sequencia)) + 1
        
        dados = request.get_json()

        

        if len(dados['id_da_venda_ref']) > 0: ## Alteração da Venda
            for i in range(len(dados_da_planilha)):
                if dados_da_planilha[i][1] == dados['id_da_venda_ref'][0]:
                    aba.update_value((i + 1, 2), 'a' + dados['id_da_venda_ref'][0])
                    print(i)
                    print(dados_da_planilha[i])
            
            coluna_id_da_venda = dados['id_da_venda_ref'][0]
            
            id_cliente_escolhido = dados['id_cliente_escolhido']
            cliente_escolhido = dados['cliente_escolhido']
            produtos_escolhidos = dados['produtos_escolhidos']
            
            dados_para_lancar = []

            for i in produtos_escolhidos:
                outras_quatro = [
                    str(coluna_sequencia),
                    str(coluna_id_da_venda),
                    id_cliente_escolhido,
                    cliente_escolhido
                ]
                dados_para_lancar.append(outras_quatro + i)
                coluna_sequencia = coluna_sequencia + 1

            
            aba.append_table(values=dados_para_lancar, start="A1", end=None, dimension='ROWS', overwrite=False)

            return jsonify(retorno="Deu certo!")
        else: ## Nova Venda
            coluna_id_da_venda = aba.get_col(2)
            # 'a4'
            nova_list = []
            for i in coluna_id_da_venda:
                if i[0] != 'a':
                    nova_list.append(i)
            
            coluna_id_da_venda = nova_list

            coluna_id_da_venda = int(max(coluna_id_da_venda[1:])) + 1

            id_cliente_escolhido = dados['id_cliente_escolhido']
            cliente_escolhido = dados['cliente_escolhido']
            produtos_escolhidos = dados['produtos_escolhidos']
            
            dados_para_lancar = []

            for i in produtos_escolhidos:
                outras_quatro = [
                    str(coluna_sequencia),
                    str(coluna_id_da_venda),
                    id_cliente_escolhido,
                    cliente_escolhido
                ]
                dados_para_lancar.append(outras_quatro + i)
                coluna_sequencia = coluna_sequencia + 1

            print(dados_para_lancar)


            aba.append_table(values=dados_para_lancar, start="A1", end=None, dimension='ROWS', overwrite=False)

            return jsonify(retorno="Deu certo!")
    except Exception as e:
        print(e)
        return jsonify(retorno="Algo deu errado!")

@app.route("/ler_dados_vendas", methods=['POST'])
def ler_dados_vendas(): 
    arquivo = credencias.open_by_url("https://docs.google.com/spreadsheets/d/1q0uYu5eB5M37ho2PqFbGigoTvsHP88OMydYFXz0_mgc/")
    aba = arquivo.worksheet_by_title("vendas")
    dados = aba.get_all_values()
    
    id_da_venda = aba.get_col(2)
    nome_cliente = aba.get_col(4)
    valor_total = aba.get_col(9)

    dados = list(zip(id_da_venda, nome_cliente, valor_total))

    result = []
    valores_totais = {}

    for row in dados[1:]:
        id_da_venda, _, valor_total = row
        valor_total = float(valor_total)

        if id_da_venda[0] != "a":
            if id_da_venda in valores_totais:
                valores_totais[id_da_venda] += valor_total
            else:
                valores_totais[id_da_venda] = valor_total
    
    for row in dados[1:]:
        id_da_venda, nome_cliente, valor_total = row
        
        if id_da_venda in valores_totais:
           result.append([id_da_venda, nome_cliente, valores_totais[id_da_venda]]) 
           del valores_totais[id_da_venda]
    
    dados = result
    

    return jsonify(retorno = dados)

@app.route("/ler_linha_venda", methods=['POST'])
def ler_linha_venda():
    id_da_venda = request.form['id_da_venda']

    arquivo = credencias.open_by_url("https://docs.google.com/spreadsheets/d/1q0uYu5eB5M37ho2PqFbGigoTvsHP88OMydYFXz0_mgc/")
    aba = arquivo.worksheet_by_title("vendas")
    dados = aba.get_all_values()
    
    result = []

    for i in dados:
        if str(i[1]) == str(id_da_venda):
            result.append(i)
    
    
    return jsonify(retorno='Deu certo!', dados=result)

if __name__ == '__main__':
    app.run(debug=True)
