import os
import requests
import shutil
import time
import yaml
import pymongo
from pymongo import MongoClient
from bs4 import BeautifulSoup

def extract_tables_data(url):

    # Obtenir le contenu HTML de la page principale
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Trouver la grande table contenant les liens vers d'autres tables
    main_table = soup.find('table')

    # Initialiser une liste pour stocker les données de toutes les tables
    tables_data = []

    # Parcourir chaque ligne de la grande table
    for row in main_table.find_all('tr'):
        # Extraire les données de chaque colonne de la ligne
        columns = row.find_all('td')
        if len(columns) == 2:  # Vérifier si la ligne contient des liens
            table_name = columns[0].text.strip()  # Nom de la table
            table_link = 'https://learn.microsoft.com/en-us/microsoft-365/security/defender/' + columns[0].find('a')['href']  # Lien complet vers la table
            description = columns[1].text.strip()  # Description de la table

            # Obtenir les données de la sous-table
            sub_table_data = extract_sub_table_data(table_link)

            # Ajouter les données de la table à la liste des tables
            tables_data.append({
                'Table Name': table_name,
                'Description': description,
                'Table Data': sub_table_data
            })

    return tables_data


def extract_sub_table_data(table_link):

    # Obtenir le contenu HTML de la page de la sous-table
    sub_table_response = requests.get(table_link)
    sub_table_soup = BeautifulSoup(sub_table_response.text, 'html.parser')

    # Trouver la sous-table dans la page de la sous-table
    sub_table = sub_table_soup.find('table')

    # Initialiser une liste pour stocker les données de la sous-table
    sub_table_data = []

    # Extraire les données de la sous-table
    for sub_row in sub_table.find_all('tr'):
        sub_columns = sub_row.find_all('td')
        if len(sub_columns) == 3:
            column_name = sub_columns[0].text.strip()
            data_type = sub_columns[1].text.strip()
            column_description = sub_columns[2].text.strip()
            sub_table_data.append({
                'Column Name': column_name,
                'Data Type': data_type,
                'Description': column_description
            })

    return sub_table_data


def load_data_to_mongodb(data, database_name='Microsoft_tables', collection_name='tables'):
    # Connexion à la base de données MongoDB
    client = pymongo.MongoClient("mongodb://localhost:27017/")  # Remplacez localhost et le port si nécessaire
    db = client[database_name]  # Remplacez mydatabase par le nom de votre base de données

    collection = db[collection_name]
    # Supprimer les données existantes dans la collection
    collection.drop()
    # Insérer les nouvelles données dans la collection
    collection.insert_many(data)
    # Fermer la connexion à la base de données
    client.close()





def download_files_from_directory(directory_url, save_directory, headers=None):
    """
    Télécharge les fichiers depuis un répertoire GitHub.

    Args:
        directory_url (str): L'URL du répertoire GitHub.
        save_directory (str): Le répertoire où sauvegarder les fichiers téléchargés.
        headers (dict, optionnel): Les en-têtes HTTP pour l'authentification. Par défaut, None.
    """
    directory_contents = requests.get(directory_url, headers=headers).json()
    for file_item in directory_contents:
        if file_item['type'] == 'file':
            file_url = file_item['download_url']
            file_name = file_item['name']
            print(f"Downloading: {file_name}")
            response = requests.get(file_url, headers=headers)
            if response.status_code == 200:
                with open(os.path.join(save_directory, file_name), 'wb') as file:
                    file.write(response.content)
                print(f"File saved to: {file_name}")
            else:
                print(f"Failed to download: {file_name}. Status code: {response.status_code}")
        elif file_item['type'] == 'dir':
            subdir_url = file_item['url']
            subdir_name = file_item['name']
            subdir_save_directory = os.path.join(save_directory, subdir_name)
            print(f"Entering directory: {subdir_name}")
            os.makedirs(subdir_save_directory, exist_ok=True)
            download_files_from_directory(subdir_url, subdir_save_directory, headers=headers)
            print(f"Exiting directory: {subdir_name}")

def parse_yaml_and_organize(directory_path, output_directory):
    """
    Analyse les fichiers YAML et les organise en fonction des types de données.

    Args:
        directory_path (str): Le chemin du répertoire contenant les fichiers YAML.
        output_directory (str): Le répertoire où organiser les fichiers en fonction des types de données.
    """
    for root, dirs, files in os.walk(directory_path):
        for file_name in files:
            if file_name.endswith(".yaml"):
                file_path = os.path.join(root, file_name)
                print(f"Parsing YAML file: {file_path}")
                with open(file_path, 'r', encoding='utf-8') as file:
                    try:
                        yaml_data = yaml.safe_load(file)
                        required_data_connectors = yaml_data.get('requiredDataConnectors', [])
                        if not isinstance(required_data_connectors, list):
                            required_data_connectors = [required_data_connectors]
                        for connector in required_data_connectors:
                            data_types = connector.get('dataTypes', [])
                            for data_type in data_types:
                                data_type_folder = os.path.join(output_directory, data_type)
                                os.makedirs(data_type_folder, exist_ok=True)
                                new_file_path = os.path.join(data_type_folder, file_name)
                                time.sleep(0.1)
                                shutil.copy(file_path, new_file_path)
                                print(f"Copied {file_name} to {data_type_folder}")
                    except yaml.YAMLError as e:
                        print(f"Error parsing YAML file {file_path}: {e}")

def store_yaml_files_in_mongodb(directory_path):
    """
    Stocke les fichiers YAML dans MongoDB.

    Args:
        directory_path (str): Le chemin du répertoire contenant les fichiers YAML.
    """
    client = MongoClient('mongodb://localhost:27017/')
    db = client['githubbase2']
    for root, dirs, files in os.walk(directory_path):
        for file_name in files:
            if file_name.endswith(".yaml"):
                file_path = os.path.join(root, file_name)
                print(f"Storing YAML file in MongoDB: {file_path}")
                with open(file_path, 'r', encoding='utf-8') as file:
                    try:
                        yaml_data = yaml.safe_load(file)
                        data_type = os.path.relpath(root, directory_path)
                        collection_name = f'{data_type}_collection'
                        collection = db[collection_name]
                        collection.insert_one(yaml_data)
                        print(f"YAML data stored in MongoDB collection {collection_name}: {file_path}")
                    except yaml.YAMLError as e:
                        print(f"Error parsing YAML file {file_path}: {e}")
    client.close()

     
