import pygsheets
import os

os.getcwd()
gc = pygsheets.authorize(service_file=os.getcwd() +
                         "/sistemasuelopro_googleConsole.json")
arquivo = gc.open_by_url(
    'https://docs.google.com/spreadsheets/d/15Jyo4qMmVK0JTSB95__JaVJveAOflbS1qR0qNOucEgI/')
aba = arquivo.worksheet_by_title('main')
header = aba.get_row(1)[0]
print(header)
