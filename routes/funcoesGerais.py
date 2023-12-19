import os
import pygsheets
import pandas as pd

import random
import string
import threading
from threading import Lock
import json

lock = threading.Lock()


from flask import Blueprint, render_template, jsonify, request, redirect, url_for
import pandas as pd
import os
import pygsheets
import datetime
from routes.funcoesGerais import *

import threading
import traceback

import re
import json
from flask import send_file
import random
import string
import numpy as np
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from googleapiclient.discovery import build
from threading import Lock
from functools import lru_cache
from datetime import datetime, timedelta
from cachetools import cached, TTLCache

from google.auth.transport.requests import Request
from google.auth.credentials import AnonymousCredentials
from google.auth import impersonated_credentials
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from google.oauth2.service_account import Credentials
from io import BytesIO
from google.oauth2 import service_account
from docx import Document
from googleapiclient.http import MediaIoBaseUpload
from docx.shared import Pt
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from googleapiclient.errors import HttpError

from googleapiclient import discovery
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

import io

# credencias = pygsheets.authorize(
#     service_file=os.getcwd() + "/sistemaNortrCromo_googleConsole.json"
# )

# arquivo = credencias.open_by_url(
#     "https://docs.google.com/spreadsheets/d/15Jyo4qMmVK0JTSB95__JaVJveAOflbS1qR0qNOucEgI/"
# )


def gera_token():
    token = "".join(
        random.choice(string.ascii_letters + string.digits) for _ in range(50)
    )
    return token


def arquivo():
    # Construa o caminho absoluto para o arquivo de credenciais
    caminho_credenciais = os.path.join(os.getcwd(), "sistemaNortrCromo_googleConsole.json")

    # Verifique se o arquivo de credenciais existe
    if not os.path.exists(caminho_credenciais):
        raise FileNotFoundError(f"O arquivo de credenciais não foi encontrado em: {caminho_credenciais}")

    # Autorize o acesso ao Google Sheets
    credenciais = pygsheets.authorize(service_file=caminho_credenciais)

    # Abra a planilha pelo URL (ou você pode usar o método `open` diretamente se tiver o ID da planilha)
    arquivo = credenciais.open_by_url(
        "https://docs.google.com/spreadsheets/d/15Jyo4qMmVK0JTSB95__JaVJveAOflbS1qR0qNOucEgI/"
    )
    
    return arquivo

def carregar_dados_gs(aba):
    dados = aba.get_all_values()
    return pd.DataFrame(data=dados[1:], columns=dados[0])


def gerar_ids(aba, quantidade):
    try:
        # Obtenha a sequência atual da coluna de IDs
        coluna_sequencia = aba.get_col(1)[1:]

        # Converta os valores não vazios para inteiros e obtenha o máximo
        coluna_sequencia = [
            int(value) if value.strip() != "" else 0 for value in coluna_sequencia
        ]

        # Calcule o próximo ID na sequência
        max_id = int(max(coluna_sequencia, default=0))
        proximos_ids = list(range(max_id + 1, max_id + 1 + quantidade))

        return proximos_ids

    except Exception as e:
        print("Erro ao gerar IDs. Erro:", str(e))
        return []


def inserir_linhas(aba, valores, ids):
    try:
        with lock:
            # Obtenha a primeira coluna (coluna de IDs)
            coluna_ids = aba.get_col(1)

        # Converta os valores não vazios para inteiros e obtenha o máximo
        ids_existentes = [int(value) for value in coluna_ids[1:] if value.strip()]

        # Obtenha o próximo ID na sequência
        proximo_id = int(max(ids_existentes, default=0)) + 1

        # Converta os IDs para string antes de adicionar à lista de valores
        valores[0] = str(proximo_id)

        # Certifique-se de que todos os valores sejam convertidos para strings
        # antes da inserção
        valores = [str(val) if val is not None else "" for val in valores]

        # Insira uma nova linha com os dados atualizados
        aba.append_table(
            values=[valores],
            start=None,
            end=None,
            dimension="ROWS",
            overwrite=False,
        )

        return True, proximo_id

    except Exception as e:
        print("Erro ao inserir linha. Valores:", valores)
        print("Erro:", str(e))
        return False, None


def verificaSeOUsuarioTemPermissao(usuario, rota):
    # usuario = "tony"
    # rota = "rota1"
    aba_usuarios = arquivo().worksheet_by_title("usuarios")
    coluna1 = aba_usuarios.get_col(1)
    coluna1 = coluna1[1:]
    for i in range(len(coluna1)):
        if coluna1[i] == usuario:
            rotasPermitidas = json.loads(aba_usuarios.get_col(4)[i + 1])
            for rotas in rotasPermitidas:
                if rotas == rota:
                    return True
    return False

# Função para converter a data do frontend para o mesmo formato do DataFrame
def converter_data_frontend(data_frontend):
    # Supondo que a data do frontend esteja em formato 'DD/MM/YYYY'
    return pd.to_datetime(data_frontend, format="%d/%m/%Y")




class SomeOtherSpecificError(Exception):
    """Exceção específica para indicar um erro particular."""

    pass


class GoogleDocsHandler:
    PDF_MIME_TYPE = "application/pdf"

    def __init__(
        self,
        credentials_sheets=None,
        credentials_drive=None,
        credentials_docs=None,
        service_file_path=None,
    ):
        self.credentials_sheets = credentials_sheets
        self.credentials_drive = credentials_drive
        self.credentials_docs = credentials_docs
        self.gc = None
        self.aba_Impressao_ChecklistRecebimento = None

        self.nomes_colunas_resumoFuncionario = None
        self.resultados_numeroLinha_resumoFuncionario = None
        self.docs_service = None

        if service_file_path:
            self.configure_credentials(service_file_path)
            self.authorize_sheets(service_file_path)
            self.authorize_docs(service_file_path)

    def configure_credentials(self, service_file_path):
        try:
            if service_file_path:
                with open(service_file_path, "r") as f:
                    credentials_info = json.load(f)

                # Use from_service_account_file diretamente
                self.credentials_sheets = (
                    service_account.Credentials.from_service_account_file(
                        service_file_path,
                        scopes=["https://www.googleapis.com/auth/spreadsheets"],
                    )
                )

                self.credentials_drive = (
                    service_account.Credentials.from_service_account_file(
                        service_file_path,
                        scopes=["https://www.googleapis.com/auth/drive"],
                    )
                )

                # Crie as credenciais_docs manualmente
                self.credentials_docs = (
                    service_account.Credentials.from_service_account_info(
                        credentials_info,
                        scopes=["https://www.googleapis.com/auth/documents"],
                    )
                )
                return (
                    self.credentials_sheets,
                    self.credentials_drive,
                    self.credentials_docs,
                )

            else:
                raise ValueError("Caminho do arquivo de serviço não fornecido.")
        except Exception as e:
            logging.error(f"Erro ao configurar Sheets, Drive e Docs: {str(e)}")
            raise RuntimeError(f"Erro ao configurar Sheets, Drive e Docs: {str(e)}")

    def authorize_docs(self, service_file_path):
        try:
             # Inicialize o serviço do Google Docs
            creds = service_account.Credentials.from_service_account_file(
                service_file_path,
                scopes=["https://www.googleapis.com/auth/documents"],
            )
            # Inicialize o serviço do Google Docs corretamente
            self.docs_service = build("docs", "v1", credentials=creds)

        except Exception as e:
            logging.error(f"Erro ao autorizar o acesso ao Google Docs: {str(e)}")
            raise RuntimeError(f"Erro ao autorizar o acesso ao Google Docs: {str(e)}")
    
    def authorize_drive(self, service_file_path):
        try:
            # Autorize o acesso usando o arquivo de serviço
            creds = service_account.Credentials.from_service_account_file(
                service_file_path,
                scopes=['https://www.googleapis.com/auth/drive']
            )

            # Crie o serviço do Google Drive
            drive_service = build('drive', 'v3', credentials=creds)

            return drive_service

        except Exception as e:
            logging.error(f"Erro ao autorizar o acesso ao Google Drive: {str(e)}")
            raise RuntimeError(f"Erro ao autorizar o acesso ao Google Drive: {str(e)}")
    
    def salvar_documento(self, service, doc_copiado_id, body):
          #print("salvar_documento")
        try:
            resultado = (
                service.documents()
                .batchUpdate(documentId=doc_copiado_id, body=body)
                .execute()
            )
              #print("TONY - Documento salvo com sucesso!", resultado)
            
        # Obtenha o link de visualização do documento
            document_link = f"https://docs.google.com/document/d/{doc_copiado_id}/edit"

            return document_link

        except Exception as e:
                print(f"Erro ao salvar o documento: {str(e)}")
                import traceback
                traceback.print_exc()
                raise RuntimeError(f"Erro ao salvar o documento: {str(e)}")
            
    def criar_copias_e_processar_documentos(self, service, quantidade, ID_Ordem, corpo_documento):
            links_documentos = []

            for _ in range(quantidade):
                # Crie uma cópia do modelo
                copia = self.criar_copia_documento(service, corpo_documento)

                # Salve a cópia e obtenha o link do documento
                link_documento = self.salvar_documento(service, copia["documentId"], corpo_documento)

                # Adicione o link à lista
                links_documentos.append(link_documento)

            # print('TONY -  links_documentos',  links_documentos)
            
            # Retorna a lista de links dos documentos criados
            return links_documentos
                    
    def upload_to_google_drive(self, file_path, folder_id, nome_arquivo):
        try:
            file_metadata = {'name': nome_arquivo, 'parents': [folder_id]}
            media = MediaFileUpload(file_path, mimetype='application/pdf', resumable=True)
            file = self.drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            file_id = file.get('id')
            print(f'Arquivo enviado para o Google Drive com o ID: {file_id}')
        except Exception as e:
            print(f"Erro ao fazer upload para o Google Drive: {str(e)}")
            raise RuntimeError(f"Erro ao fazer upload para o Google Drive: {str(e)}")
        
    def get_inline_object_image(self, inline_object_id, doc_id):
        try:
            # Obtém os dados da imagem do objeto inline
            img_data = self.docs_service.documents().get(
                documentId=doc_id, inlineObjectId=inline_object_id
            ).execute()

            # Recupera a URL da imagem
            img_url = img_data["inlineObject"]["inlineObjectProperties"]["embeddedObject"]["image"]["contentUri"]

            # Baixa a imagem e retorna os dados binários
            response = self.docs_service.documents().get(
                documentId=doc_id, resourceId=inline_object_id, alt="media"
            ).execute()

            # Converte a imagem para bytes
            img_bytes = io.BytesIO(response.content).read()

            return img_bytes

        except Exception as e:
            logging.error(f"Erro ao obter dados da imagem inline: {str(e)}")
            raise RuntimeError(f"Erro ao obter dados da imagem inline: {str(e)}")

    def convert_to_pdf_and_upload(self, doc_copiado_id, folder_id, nome_arquivo):
        try:
            # Certifique-se de que doc_copiado_id é uma string
            doc_copiado_id = str(doc_copiado_id)

            # Obtenha o documento
            documento = self.docs_service.documents().get(documentId=doc_copiado_id).execute()

            # Salva o documento localmente (opcional)
            caminho_temporario = f"{doc_copiado_id}_temp.docx"
            with open(caminho_temporario, "w", encoding="utf-8") as temp_file:
                temp_file.write(str(documento))

            print(f"Documento salvo em: {caminho_temporario}")

            # Define o nome desejado para o arquivo PDF no Google Drive
            nome_arquivo_pdf = f"{doc_copiado_id}.pdf"

            # Converte o documento Google Doc para PDF
            pdf_content = self.convert_to_pdf(documento, doc_copiado_id)
            with open(nome_arquivo_pdf, "wb") as pdf_file:
                pdf_file.write(pdf_content)

            # Envia o documento PDF para o Google Drive na mesma pasta do documento original
            self.upload_to_google_drive(nome_arquivo_pdf, folder_id, nome_arquivo_pdf)

            # Remove os arquivos temporários locais
            os.remove(caminho_temporario)
            os.remove(nome_arquivo_pdf)

            print(f"PDF salvo em: {nome_arquivo_pdf}")

            return nome_arquivo_pdf  # Retorna o nome do arquivo PDF no Google Drive

        except Exception as e:
            print(f"Erro ao abrir o documento para leitura: {str(e)}")
            raise RuntimeError(f"Erro ao abrir o documento para leitura: {str(e)}")        
            
    def authorize_sheets(self, service_file_path):
        try:
            # Autorize o acesso usando o arquivo de serviço
            credenciais = pygsheets.authorize(service_file=service_file_path)

            # Abra a planilha pelo URL
            arquivo_url = "https://docs.google.com/spreadsheets/d/15Jyo4qMmVK0JTSB95__JaVJveAOflbS1qR0qNOucEgI/"
            arquivo = credenciais.open_by_url(arquivo_url)
            
            # Selecione a aba correta VALIDADO
            self.aba_Impressao_ChecklistRecebimento = arquivo.worksheet_by_title(
                "Impressao_ChecklistRecebimento"
            )

            # Verifique se a guia foi encontrada
            if self.aba_Impressao_ChecklistRecebimento is None:
                raise RuntimeError(
                    "A guia 'Impressao_ChecklistRecebimento' não foi encontrada na planilha."
                )

        except Exception as e:
            logging.error(f"Erro ao autorizar o acesso ao Google Sheets: {str(e)}")
            raise RuntimeError(f"Erro ao autorizar o acesso ao Google Sheets: {str(e)}")

    def get_credentials(self):
            SCOPES = ["https://www.googleapis.com/auth/documents"]
            SERVICE_ACCOUNT_FILE = "path/to/your/credentials.json"
            creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
            return creds
        
    
class SomeOtherSpecificError(Exception):
    """Exceção específica para indicar um erro particular."""

    pass


class GoogleDocsHandler:
    PDF_MIME_TYPE = "application/pdf"

    def __init__(
        self,
        credentials_sheets=None,
        credentials_drive=None,
        credentials_docs=None,
        service_file_path=None,
    ):
        self.credentials_sheets = credentials_sheets
        self.credentials_drive = credentials_drive
        self.credentials_docs = credentials_docs
        self.gc = None
        self.aba_Impressao_ChecklistRecebimento = None

        self.nomes_colunas_resumoFuncionario = None
        self.resultados_numeroLinha_resumoFuncionario = None
        self.docs_service = None

        if service_file_path:
            self.configure_credentials(service_file_path)
            self.authorize_sheets(service_file_path)
            self.authorize_docs(service_file_path)

    def configure_credentials(self, service_file_path):
        try:
            if service_file_path:
                with open(service_file_path, "r") as f:
                    credentials_info = json.load(f)

                # Use from_service_account_file diretamente
                self.credentials_sheets = (
                    service_account.Credentials.from_service_account_file(
                        service_file_path,
                        scopes=["https://www.googleapis.com/auth/spreadsheets"],
                    )
                )

                self.credentials_drive = (
                    service_account.Credentials.from_service_account_file(
                        service_file_path,
                        scopes=["https://www.googleapis.com/auth/drive"],
                    )
                )

                # Crie as credenciais_docs manualmente
                self.credentials_docs = (
                    service_account.Credentials.from_service_account_info(
                        credentials_info,
                        scopes=["https://www.googleapis.com/auth/documents"],
                    )
                )
                return (
                    self.credentials_sheets,
                    self.credentials_drive,
                    self.credentials_docs,
                )

            else:
                raise ValueError("Caminho do arquivo de serviço não fornecido.")
        except Exception as e:
            logging.error(f"Erro ao configurar Sheets, Drive e Docs: {str(e)}")
            raise RuntimeError(f"Erro ao configurar Sheets, Drive e Docs: {str(e)}")

    def authorize_docs(self, service_file_path):
        try:
             # Inicialize o serviço do Google Docs
            creds = service_account.Credentials.from_service_account_file(
                service_file_path,
                scopes=["https://www.googleapis.com/auth/documents"],
            )
            # Inicialize o serviço do Google Docs corretamente
            self.docs_service = build("docs", "v1", credentials=creds)

        except Exception as e:
            logging.error(f"Erro ao autorizar o acesso ao Google Docs: {str(e)}")
            raise RuntimeError(f"Erro ao autorizar o acesso ao Google Docs: {str(e)}")
    
    def authorize_drive(self, service_file_path):
        try:
            # Autorize o acesso usando o arquivo de serviço
            creds = service_account.Credentials.from_service_account_file(
                service_file_path,
                scopes=['https://www.googleapis.com/auth/drive']
            )

            # Crie o serviço do Google Drive
            drive_service = build('drive', 'v3', credentials=creds)

            return drive_service

        except Exception as e:
            logging.error(f"Erro ao autorizar o acesso ao Google Drive: {str(e)}")
            raise RuntimeError(f"Erro ao autorizar o acesso ao Google Drive: {str(e)}")

    def salvar_documento(self, service, doc_copiado_id, body):
        print("salvar_documento")
        try:
            resultado = (
                service.documents()
                .batchUpdate(documentId=doc_copiado_id, body=body)
                .execute()
            )
            print("TONY - Documento salvo com sucesso!", resultado)
            
        # Obtenha o link de visualização do documento
            document_link = f"https://docs.google.com/document/d/{doc_copiado_id}/edit"

            return document_link

        except Exception as e:
                print(f"Erro ao salvar o documento: {str(e)}")
                import traceback
                traceback.print_exc()
                raise RuntimeError(f"Erro ao salvar o documento: {str(e)}")
            
    def criar_copias_e_processar_documentos(self, service, quantidade, ID_Ordem, corpo_documento):
            links_documentos = []

            for _ in range(quantidade):
                # Crie uma cópia do modelo
                copia = self.criar_copia_documento(service, corpo_documento)

                # Salve a cópia e obtenha o link do documento
                link_documento = self.salvar_documento(service, copia["documentId"], corpo_documento)

                # Adicione o link à lista
                links_documentos.append(link_documento)

                print('TONY NORTHCROMO -  links_documentos',  links_documentos)
            
            # Retorna a lista de links dos documentos criados
            return links_documentos
                    
    def upload_to_google_drive(self, file_path, folder_id, nome_arquivo):
        try:
            file_metadata = {'name': nome_arquivo, 'parents': [folder_id]}
            media = MediaFileUpload(file_path, mimetype='application/pdf', resumable=True)
            file = self.drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            file_id = file.get('id')
            print(f'Arquivo enviado para o Google Drive com o ID: {file_id}')
        except Exception as e:
            print(f"Erro ao fazer upload para o Google Drive: {str(e)}")
            raise RuntimeError(f"Erro ao fazer upload para o Google Drive: {str(e)}")
        
    def get_inline_object_image(self, inline_object_id, doc_id):
        try:
            # Obtém os dados da imagem do objeto inline
            img_data = self.docs_service.documents().get(
                documentId=doc_id, inlineObjectId=inline_object_id
            ).execute()

            # Recupera a URL da imagem
            img_url = img_data["inlineObject"]["inlineObjectProperties"]["embeddedObject"]["image"]["contentUri"]

            # Baixa a imagem e retorna os dados binários
            response = self.docs_service.documents().get(
                documentId=doc_id, resourceId=inline_object_id, alt="media"
            ).execute()

            # Converte a imagem para bytes
            img_bytes = io.BytesIO(response.content).read()

            return img_bytes

        except Exception as e:
            logging.error(f"Erro ao obter dados da imagem inline: {str(e)}")
            raise RuntimeError(f"Erro ao obter dados da imagem inline: {str(e)}")

    def convert_to_pdf_and_upload(self, doc_copiado_id, folder_id, nome_arquivo):
        try:
            # Certifique-se de que doc_copiado_id é uma string
            doc_copiado_id = str(doc_copiado_id)

            # Obtenha o documento
            documento = self.docs_service.documents().get(documentId=doc_copiado_id).execute()

            # Salva o documento localmente (opcional)
            caminho_temporario = f"{doc_copiado_id}_temp.docx"
            with open(caminho_temporario, "w", encoding="utf-8") as temp_file:
                temp_file.write(str(documento))

            print(f"Documento salvo em: {caminho_temporario}")

            # Define o nome desejado para o arquivo PDF no Google Drive
            nome_arquivo_pdf = f"{doc_copiado_id}.pdf"

            # Converte o documento Google Doc para PDF
            pdf_content = self.convert_to_pdf(documento, doc_copiado_id)
            with open(nome_arquivo_pdf, "wb") as pdf_file:
                pdf_file.write(pdf_content)

            # Envia o documento PDF para o Google Drive na mesma pasta do documento original
            self.upload_to_google_drive(nome_arquivo_pdf, folder_id, nome_arquivo_pdf)

            # Remove os arquivos temporários locais
            os.remove(caminho_temporario)
            os.remove(nome_arquivo_pdf)

            print(f"PDF salvo em: {nome_arquivo_pdf}")

            return nome_arquivo_pdf  # Retorna o nome do arquivo PDF no Google Drive

        except Exception as e:
            print(f"Erro ao abrir o documento para leitura: {str(e)}")
            raise RuntimeError(f"Erro ao abrir o documento para leitura: {str(e)}")        
            
    def authorize_sheets(self, service_file_path):
        try:
            # Autorize o acesso usando o arquivo de serviço
            credenciais = pygsheets.authorize(service_file=service_file_path)

            # Abra a planilha pelo URL
            arquivo_url = "https://docs.google.com/spreadsheets/d/15Jyo4qMmVK0JTSB95__JaVJveAOflbS1qR0qNOucEgI/"
            arquivo = credenciais.open_by_url(arquivo_url)

            # Selecione a aba correta VALIDADO
            self.aba_Impressao_ChecklistRecebimento = arquivo.worksheet_by_title(
                "Impressao_ChecklistRecebimento"
            )

            # Verifique se a guia foi encontrada
            if self.aba_Impressao_ChecklistRecebimento is None:
                raise RuntimeError(
                    "A guia 'Impressao_ChecklistRecebimento' não foi encontrada na planilha."
                )

        except Exception as e:
            logging.error(f"Erro ao autorizar o acesso ao Google Sheets: {str(e)}")
            raise RuntimeError(f"Erro ao autorizar o acesso ao Google Sheets: {str(e)}")

    def get_credentials(self):
            SCOPES = ["https://www.googleapis.com/auth/documents"]
            SERVICE_ACCOUNT_FILE = "path/to/your/credentials.json"
            creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
            return creds

    def criar_copia_do_doc(self, modelo_id, destino_id, ID_Ordem):
        try:
            drive_service = build("drive", "v3", credentials=self.credentials_drive)

            # Construa o nome da cópia com o nome do funcionário
            nome_copia = f"Recibo - {ID_Ordem}"

            # Verifique se já existe uma cópia com o mesmo nome
            query = (
                f"name='{nome_copia}' and '{destino_id}' in parents and trashed=false"
            )
            existing_files = (
                drive_service.files().list(q=query).execute().get("files", [])
            )

            # Exclua cópias antigas se existirem
            for existing_file in existing_files:
                drive_service.files().delete(fileId=existing_file["id"]).execute()

            # Crie uma nova cópia
            copia_request = {"name": nome_copia, "parents": [destino_id]}
            copia = (
                drive_service.files()
                .copy(fileId=modelo_id, body=copia_request)
                .execute()
            )

            print("TONY criar_copia_do_doc - COPIA ID", copia["id"])
            return copia["id"]

        except Exception as e:
            logging.error(f"Erro ao criar cópia do documento: {str(e)}")
            raise RuntimeError(f"Erro ao criar cópia do documento: {str(e)}")

    def criar_copia_do_doc_e_exportar_pdf(
        self, modelo_id, destino_id, ID_Ordem
    ):
        try:
            drive_service = build("drive", "v3", credentials=self.credentials_drive)
            copia_request = {
                "name": f"Recebimento_{ID_Ordem}",
                "parents": [destino_id],
            }
            copia = (
                drive_service.files()
                .copy(fileId=modelo_id, body=copia_request)
                .execute()
            )

            pdf_export_request = {"mimeType": self.PDF_MIME_TYPE}
            pdf_export = drive_service.files().export(
                fileId=copia["id"], mimeType="application/pdf"
            )
            pdf_bytes = pdf_export.execute()

            pdf_file = BytesIO(pdf_bytes)
            media_body = MediaIoBaseUpload(
                pdf_file, mimetype="application/pdf", resumable=True
            )

            pdf_upload_request = drive_service.files().create(
                media_body=media_body,
                body={
                    "name": f"Recebimento_{ID_Ordem}.pdf",
                    "parents": [destino_id],
                },
            )
            pdf_upload_response = pdf_upload_request.execute()
            pdf_link = (
                drive_service.files()
                .get(fileId=pdf_upload_response["id"], fields="webViewLink")
                .execute()["webViewLink"]
            )

            return {"id": copia["id"], "pdf_link": pdf_link}

        except Exception as e:
            logging.error(f"Erro ao criar cópia do documento e exportar PDF: {str(e)}")
            return {
                "error": f"Erro ao criar cópia do documento e exportar PDF: {str(e)}"
            }

    def obter_link_documento_copiado(self, file_id):
        try:
            drive_service = build("drive", "v3", credentials=self.credentials_drive)
            file_metadata = (
                drive_service.files()
                .get(fileId=file_id, fields="webViewLink")
                .execute()
            )

            print("TONY - file_metadata", file_metadata["webViewLink"])
            return file_metadata["webViewLink"]

        except Exception as e:
            logging.error(
                f"Erro ao obter link do documento (File ID: {file_id}): {str(e)}"
            )
            raise RuntimeError(
                f"Erro ao obter link do documento (File ID: {file_id}): {str(e)}"
            )
              
    def abrir_documento_para_edicao(self, doc_copiado_id, dados_linha):
        try:
            print('NOTH CROMO - abrir_documento_para_edicao')

            SCOPES = ["https://www.googleapis.com/auth/documents"]

            # Carregue as credenciais do arquivo JSON
            creds = service_account.Credentials.from_service_account_file(
                os.path.join(os.getcwd(), "sistemaNortrCromo_googleConsole.json"),
                scopes=SCOPES,
            )

            # Crie um serviço Google Docs
            service = build("docs", "v1", credentials=creds)

            # Certifique-se de que doc_copiado_id é uma string
            doc_copiado_id = str(doc_copiado_id)

            # Obtenha o documento
            documento = service.documents().get(documentId=doc_copiado_id).execute()

            # Obtenha a data atual no formato desejado (dia/mês/ano)
            data_atual = datetime.now().strftime("%d/%m/%Y")

            # Adicione a data atual ao dicionário dados_linha
            dados_linha["DATA"] = data_atual

            print('NORTH CROMO - dados_linha', dados_linha)

            mapeamento_campos = {
                'Referencia_Produto': '{{o}}',
                'ID_Ordem': '{{a}}',
                'Nome_cliente': '{{cl}}',
                'Qtd_Produto': ' {{qtd}}',
                'nome_produto': '{{produto}}',
                'ID_Checklist': '{{doc.cl}}',
                'NotaInterna': '{{b}}',
                # Adicione outros campos conforme necessário
            }

            # Substitua os marcadores pelos valores correspondentes
            for pagina in documento["body"]["content"]:
                if "paragraph" in pagina:
                    for paragrafo in pagina.get("paragraph", {}).get("elements", []):
                        if "textRun" in paragrafo:
                            # Adicione esta linha para imprimir informações sobre o parágrafo
                            print(f"Parágrafo antes: {paragrafo}")

                            texto_original = paragrafo["textRun"]["content"]
                            texto = texto_original
                            print('texto_original', texto_original)

                            # Identificar marcadores no formato {{nome_do_marcador}}
                            marcadores_no_documento = set(re.findall(r"\{\{\s*(.*?)\s*\}\}", texto, flags=re.IGNORECASE))
                            marcadores_no_mapeamento = set(mapeamento_campos.values())

                            marcadores_faltando = marcadores_no_documento - marcadores_no_mapeamento

                            for marcador in marcadores_no_documento:
                                if marcador in mapeamento_campos:
                                    valor = str(mapeamento_campos[marcador])
                                    print('NOTHCROMO - valor', valor)

                                    # Substitua o marcador pelo valor correspondente
                                    texto = texto.replace(f"{{{{{marcador}}}}}", valor)

                                    # Atualize o texto no parágrafo
                                    paragrafo["textRun"]["content"] = texto

                                    # Adicione prints para verificar as alterações
                                    if texto != texto_original:
                                        print(f'NOTHCROMO - Marcadores substituídos em: {texto_original}')
                                        print(f'NOTHCROMO - Resultado final: {texto}')

            requests = []

            for marcador, valor in mapeamento_campos.items():
                for pagina in documento["body"]["content"]:
                    if "paragraph" in pagina:
                        for paragrafo in pagina.get("paragraph", {}).get("elements", []):
                            if "textRun" in paragrafo:
                                texto_original = paragrafo["textRun"]["content"]

                                # Identificar marcadores no formato {{nome_do_marcador}}
                                marcadores_no_documento = set(re.findall(r"\{\{\s*(.*?)\s*\}\}", texto_original, flags=re.IGNORECASE))

                                if marcador in marcadores_no_documento:
                                    # Substitua o marcador pelo valor correspondente
                                    texto_original = texto_original.replace(f"{{{{{marcador}}}}}", str(valor))

                                # Adicione prints para verificar as alterações
                                if texto_original != paragrafo["textRun"]["content"]:
                                    print(f'NOTHCROMO - Marcadores substituídos em: {texto_original}')
                                    print(f'NOTHCROMO - Resultado final: {paragrafo["textRun"]["content"]}')

                                # Atualize o texto no parágrafo
                                paragrafo["textRun"]["content"] = texto_original

            # Adicione uma única solicitação de lote para todas as atualizações
            requests.append({
                "replaceAllText": {
                    "containsText": {"text": "{{", "matchCase": True},
                    "replaceText": "",
                }
            })

            # Verifique se há pelo menos uma solicitação antes de tentar salvar
            if not requests:
                raise RuntimeError("Nenhuma solicitação de atualização foi gerada. Verifique o mapeamento de campos.")

            # Tente salvar o documento
            resultado = self.salvar_documento(service, doc_copiado_id, {"requests": requests})

            # Verifique o resultado da operação de salvamento
            if "documentId" in resultado:
                print("Documento salvo com sucesso!")
            else:
                # Adicione informações detalhadas sobre o resultado do salvamento
                if "error" in resultado:
                    error_message = resultado["error"]["message"]
                    logging.error(f"NORTH CROMO - Erro ao salvar o documento. Detalhes: {error_message}")
                    raise RuntimeError(f"NORTH CROMO - Erro ao salvar o documento. Detalhes: {error_message}")
                else:
                    logging.error("NORTH CROMO - Erro ao salvar o documento. Detalhes indisponíveis.")
                    raise RuntimeError("MOTHCROMO - Erro ao salvar o documento. Operações subsequentes não serão realizadas.")

        except Exception as e:
            logging.error(f"NORTH CROMO - Erro ao abrir o documento para edição: {str(e)}")
            raise RuntimeError(f"NORTH CROMO - Erro ao abrir o documento para edição: {str(e)}")
    
    def obter_dados_google_sheets(self):
        print("obter_dados_google_sheets")
        try:
            # Autorize o acesso usando o arquivo de serviço
            credenciais = pygsheets.authorize(
                service_file=os.getcwd() + "/sistemaNortrCromo_googleConsole.json"
            )

            # Abra a planilha pelo URL
            arquivo_url = " https://docs.google.com/spreadsheets/d/15Jyo4qMmVK0JTSB95__JaVJveAOflbS1qR0qNOucEgI/"
            arquivo = credenciais.open_by_url(arquivo_url)

            # Selecione a aba correta
            aba_Impressao_ChecklistRecebimento = arquivo.worksheet_by_title(
                "Impressao_ChecklistRecebimento"
            )

            # Verifique se a guia foi encontrada
            if aba_Impressao_ChecklistRecebimento is None:
                raise RuntimeError(
                    "A guia 'Impressao_ChecklistRecebimento' não foi encontrada na planilha."
                )

            # Obtenha todos os valores da planilha
            dados_da_planilha = aba_Impressao_ChecklistRecebimento.get_all_values()
            print('dados_da_planilha', dados_da_planilha)

            # A primeira linha contém os nomes das colunas, que serão usados para
            # mapeamento
            colunas = dados_da_planilha[0]

            # Os dados começam da segunda linha em diante
            dados = dados_da_planilha[1:]

            resultados = []

            for row in dados:
                # Crie um dicionário para armazenar os dados
                dados_funcionario = dict(zip(colunas, row))

                print("DEBUG: ID_Checklist", dados_funcionario.get("ID_Checklist"))
                print("DEBUG: ID_Ordem", dados_funcionario.get("ID_Ordem"))

                if dados_funcionario.get("ID_Ordem") and dados_funcionario.get("ID_Checklist") and int(dados_funcionario["ID_Checklist"]) > 0:
                    resultados.append(dados_funcionario)
                    
                    
                    
            # Armazene os nomes das colunas e os resultados como variáveis de instância
            self.nomes_colunas_resumoFuncionario = colunas
            self.resultados_numeroLinha_resumoFuncionario = resultados

            return resultados

        except Exception as e:
            # Manipule outras exceções
            logging.error(
                f"Erro desconhecido ao obter dados do Google Sheets: {str(e)}"
            )
            raise RuntimeError(
                f"Erro desconhecido ao obter dados do Google Sheets: {str(e)}"
            )

    # Novo método para obter o número da linha pelo ID do documento
    def obter_numero_linha_pelo_ID_Ordem(self, ID_Ordem):
        cells = self.aba_Impressao_ChecklistRecebimento.find(ID_Ordem)
        try:
            if cells:
                # Se encontrou mais de uma célula, escolha a primeira
                cell = cells[0] if isinstance(cells, list) else cells
                print("obter_numero_linha_pelo_ID_Ordem numero_linha", cell.row)
                return cell.row

            # Obtenha os valores da coluna ID_Ordem
            coluna_ID_Ordem = "ID_Ordem"
            colunas = self.aba_Impressao_ChecklistRecebimento.get_all_values()[0]

            if coluna_ID_Ordem not in colunas:
                raise RuntimeError(f"Coluna '{coluna_ID_Ordem}' não encontrada na planilha.")

            indice_coluna = colunas.index(coluna_ID_Ordem)

            coluna_valores = self.aba_Impressao_ChecklistRecebimento.get_col(indice_coluna + 1)

            # Verifique se o ID_Ordem está na coluna
            if ID_Ordem not in coluna_valores:
                print("obter_numero_linha_pelo_ID_Ordem ID_Ordem NÃO ENCONTRADO")
                return None

            # Encontre o número da linha correspondente
            numero_linha = coluna_valores.index(ID_Ordem) + 1
            print("obter_numero_linha_pelo_ID_Ordem numero_linha", numero_linha)
            return numero_linha if numero_linha > 0 else None

        except Exception as e:
            print(f"Erro ao obter número da linha pelo ID_Ordem: {str(e)}")
            raise  # Removendo a captura da exceção para ver o traceback completo

    def adicionar_link_para_linha(self, doc_copiado_id, link_documento_copiado, ID_Ordem):
        print("TONY - adicionar_link_para_linha")
        try:
            # Autorize o acesso usando o arquivo de serviço
            credenciais = pygsheets.authorize(
                service_file=os.getcwd() + "/sistemaNortrCromo_googleConsole.json"
            )

            # Abra a planilha pelo URL
            arquivo_url = "https://docs.google.com/spreadsheets/d/15Jyo4qMmVK0JTSB95__JaVJveAOflbS1qR0qNOucEgI/"
            arquivo = credenciais.open_by_url(arquivo_url)

            # Selecione a aba correta
            self.aba_Impressao_ChecklistRecebimento = arquivo.worksheet_by_title(
                "Impressao_ChecklistRecebimento"
            )

            # Verifique se a guia foi encontrada
            if self.aba_Impressao_ChecklistRecebimento is None:
                raise RuntimeError("A guia 'Impressao_ChecklistRecebimento' não foi encontrada na planilha.")

            ID_Ordem = ID_Ordem
            print("TONY - ID_Ordem", ID_Ordem)

            # Obtenha o número da linha pelo ID_Ordem
            numero_linha = self.obter_numero_linha_pelo_ID_Ordem(ID_Ordem)
            print("TONY - numero_linha", numero_linha)

            print("Antes do bloco condicional")
            # Se o número da linha for encontrado, adicione o link à coluna N
            if numero_linha is not None:
                print("Depois do bloco condicional")
                # Adiciona o link à coluna LINK_PDF_CHECKLIST da linha especificada
                coluna_link = "LINK_PDF_CHECKLIST"
                try:
                    indice_coluna = self.nomes_colunas_resumoFuncionario.index(coluna_link)
                    print("Depois do bloco condicional", indice_coluna)
                    self.aba_Impressao_ChecklistRecebimento.update_value(
                        (numero_linha, indice_coluna + 1),
                        link_documento_copiado,
                    )
                    print(f"Link adicionado à linha {numero_linha} para o funcionário {ID_Ordem}")

                except ValueError:
                    logging.error(f"Erro: Coluna '{coluna_link}' não encontrada na lista de colunas.")

        except pygsheets.exceptions.RequestError as e:
            if "Unable to find sheet" in str(e):
                logging.error("Erro: Guia não encontrada na planilha.")
                raise RuntimeError("Erro: Guia não encontrada na planilha.")
            else:
                # Manipule outras exceções
                logging.error(f"Erro ao adicionar link à planilha: {str(e)}")
                raise RuntimeError(f"Erro ao adicionar link à planilha: {str(e)}")

# Substitua pelo caminho correto para o seu arquivo de serviço
service_file_path = os.getcwd() + "/sistemaNortrCromo_googleConsole.json"

# Crie uma instância de GoogleDocsHandler
google_docs_handler = GoogleDocsHandler()

# Configure as credenciais
(
    credenciais_sheets,
    credenciais_drive,
    _,
) = google_docs_handler.configure_credentials(service_file_path)

# Autorize o acesso ao Google Sheets
google_docs_handler.authorize_sheets(service_file_path)