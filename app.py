import os
import requests
from pymongo import MongoClient
from Extraction import (download_files_from_directory, parse_yaml_and_organize, 
                        store_yaml_files_in_mongodb, extract_tables_data, 
                        extract_sub_table_data, load_data_to_mongodb)


def main():
    # URL pour extraire les données des tables
    url = 'https://learn.microsoft.com/en-us/microsoft-365/security/defender/advanced-hunting-schema-tables?view=o365-worldwide'
    tables_data = extract_tables_data(url)
    print(tables_data)
    load_data_to_mongodb(tables_data)

    # URL du dépôt GitHub
    repository_url = 'https://api.github.com/repos/Azure/Azure-Sentinel/contents/Hunting%20Queries/Microsoft%20365%20Defender'
    headers = {'Authorization': 'Bearer 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'}

    try:
        response = requests.get(repository_url, headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Failed to access repository. Error: {e}")
        return

    contents = response.json()

    # Créer un répertoire pour sauvegarder les fichiers
    save_directory = 'downloaded_files'
    os.makedirs(save_directory, exist_ok=True)

    # Télécharger les fichiers du dépôt GitHub
    for item in contents:
        if item['type'] == 'file':
            file_url = item['download_url']
            file_name = item['name']
            print(f"Downloading: {file_name}")
            try:
                file_response = requests.get(file_url, headers=headers)
                file_response.raise_for_status()
                with open(os.path.join(save_directory, file_name), 'wb') as file:
                    file.write(file_response.content)
                print(f"File saved to: {file_name}")
            except requests.RequestException as e:
                print(f"Failed to download: {file_name}. Error: {e}")
        elif item['type'] == 'dir':
            subdir_url = item['url']
            subdir_name = item['name']
            subdir_save_directory = os.path.join(save_directory, subdir_name)
            print(f"Entering directory: {subdir_name}")
            os.makedirs(subdir_save_directory, exist_ok=True)
            download_files_from_directory(subdir_url, subdir_save_directory, headers=headers)
            print(f"Exiting directory: {subdir_name}")

    # Analyser les fichiers YAML et les organiser par type de données
    output_directory = 'files_parsed1'
    os.makedirs(output_directory, exist_ok=True)
    os.chmod(output_directory, 0o777)
    parse_yaml_and_organize(save_directory, output_directory)

    # Stocker les fichiers YAML dans MongoDB
    try:
        client = MongoClient('mongodb://localhost:27017/')
        db = client['githubbase3']
        store_yaml_files_in_mongodb(output_directory)
    except pymongo.errors.PyMongoError as e:
        print(f"Failed to store YAML files in MongoDB. Error: {e}")
    finally:
        client.close()


if __name__ == "__main__":
    main()
