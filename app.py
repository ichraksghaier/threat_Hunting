import os
import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
import pymongo
from Extraction import download_files_from_directory, parse_yaml_and_organize, store_yaml_files_in_mongodb ,extract_tables_data,extract_sub_table_data,load_data_to_mongodb


#url1
url = 'https://learn.microsoft.com/en-us/microsoft-365/security/defender/advanced-hunting-schema-tables?view=o365-worldwide'
tables_data = extract_tables_data(url)
print(tables_data)
load_data_to_mongodb(tables_data)



#api_github
repository_url = 'https://api.github.com/repos/Azure/Azure-Sentinel/contents/Hunting%20Queries/Microsoft%20365%20Defender'

headers = {'Authorization': 'Bearer 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'}

# Make a request to get the contents of the repository
response = requests.get(repository_url, headers=headers)

if response.status_code == 200:
    # Parse the JSON response
    contents = response.json()

    # Create a directory to save files
    save_directory = 'downloaded_files'
    os.makedirs(save_directory, exist_ok=True)

    # Download files from GitHub repository
    for item in contents:
        if item['type'] == 'file':
            # Download the file
            file_url = item['download_url']
            file_name = item['name']
            print(f"Downloading: {file_name}")
            response = requests.get(file_url, headers=headers)
            if response.status_code == 200:
                # Save the file
                with open(os.path.join(save_directory, file_name), 'wb') as file:
                    file.write(response.content)
                print(f"File saved to: {file_name}")
            else:
                print(f"Failed to download: {file_name}. Status code: {response.status_code}")
        elif item['type'] == 'dir':
            # Recursively download files from subdirectory
            subdir_url = item['url']
            subdir_name = item['name']
            subdir_save_directory = os.path.join(save_directory, subdir_name)
            print(f"Entering directory: {subdir_name}")
            os.makedirs(subdir_save_directory, exist_ok=True)
            download_files_from_directory(subdir_url, subdir_save_directory, headers=headers)
            print(f"Exiting directory: {subdir_name}")

    # Parse YAML files and organize based on data types
    downloaded_directory = 'downloaded_files'
    output_directory = 'files_parsed1'
    os.makedirs(output_directory, exist_ok=True)
    os.chmod(output_directory, 0o777)
    parse_yaml_and_organize(downloaded_directory, output_directory)

    # Store YAML files in MongoDB
    client = MongoClient('mongodb://localhost:27017/')
    db = client['githubbase3']  # Replace with your MongoDB database name
    store_yaml_files_in_mongodb(output_directory)
    client.close()
else:
    print(f"Failed to access repository. Status code: {response.status_code}")
