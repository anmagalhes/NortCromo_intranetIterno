from flask_caching import Cache
import pandas as pd
from routes.clientes import arquivo  # Substitua "your_module_path" pelo caminho do seu módulo

cache = Cache(config={'CACHE_TYPE': 'simple'})

# Função para obter os dados dos clientes
@cache.cached(timeout=3600, key_prefix='clientes_data')
def obter_dados_clientes():
    try:
        print("Tentando obter dados do cache...")
        clientes_aba = arquivo().worksheet_by_title("Cliente")
        dados_clientes = clientes_aba.get_all_values()
        df_clientes = pd.DataFrame(data=dados_clientes[1:], columns=dados_clientes[0])

        # Seleciona apenas as colunas desejadas
        colunas_desejadas = ["ID", "Nome_cliente"]
        df_selecionado = df_clientes[colunas_desejadas]

        # Filtra os registros onde a coluna "Nome_cliente" é diferente de vazio ou nulo
        clientes_ok = df_selecionado[df_selecionado["Nome_cliente"].notna()]

        # Classifica os clientes pelo nome em ordem alfabética
        clientes_ok.sort_values(by="Nome_cliente", inplace=True)

        # Converte o DataFrame resultante para um dicionário
        clientes_lista = clientes_ok.to_dict(orient="records")

        print("Clientes carregados com sucesso:", clientes_lista)
        return clientes_lista

    except Exception as e:
        print(f"Erro ao carregar clientes: {str(e)}")
        return []
