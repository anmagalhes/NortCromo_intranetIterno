from flask import Blueprint, render_template, jsonify, request
import pandas as pd
import os
import pygsheets
from routes.funcoesGerais import *

get_pedreiros_data = Blueprint(
    "get_pedreiros_data",
    __name__,
    static_folder="static",
    template_folder="templates",
)


@get_pedreiros_data.route("/get_pedreiros_data", methods=["GET"])
def get_pedreiros_data_f():
    aba = arquivo.worksheet_by_title("base_de_dados")
    all_data = aba.get_all_records()
    pedreiros_data = [
        {"ID": row["ID"], "Nome": row["Nome"]}
        for row in all_data
        if row["Cargo"] == "Pedreiro"
    ]
    return jsonify(pedreiros_data)
