import os
import pygsheets


def arquivo():
    credencias = pygsheets.authorize(
        service_file=os.getcwd() + "/sistemasuelopro_googleConsole.json"
    )

    arquivo = credencias.open_by_url(
        "https://docs.google.com/spreadsheets/d/15Jyo4qMmVK0JTSB95__JaVJveAOflbS1qR0qNOucEgI/"
    )
    return arquivo
