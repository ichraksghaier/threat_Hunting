import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import json

base_url = "https://attack.mitre.org"

def extract_tables_data(url):
    # Obtenir le contenu HTML de la page principale des tactiques
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Trouver la table contenant les tactiques
    main_table = soup.find('table', class_='table table-bordered table-alternate mt-2')

    # Initialiser une liste pour stocker les données de toutes les tactiques et techniques
    tables_data = []

    # Parcourir chaque ligne de la table des tactiques
    for row in main_table.find('tbody').find_all('tr'):
        # Extraire les données de chaque colonne de la ligne
        columns = row.find_all('td')
        if len(columns) == 3:
            tactic_id = columns[0].text.strip()
            tactic_name = columns[1].text.strip()
            tactic_description = columns[2].text.strip()
            tactic_link = base_url + columns[1].find('a')['href']  # Lien complet vers la tactique

            # Obtenir les données des techniques pour cette tactique
            sub_table_data = extract_sub_table_data(tactic_link)

            # Ajouter les données de la tactique et de ses techniques à la liste des tables
            tables_data.append({
                'Tactic ID': tactic_id,
                'Tactic Name': tactic_name,
                'Tactic Description': tactic_description,
                'Techniques': sub_table_data
            })

    return tables_data

def extract_sub_table_data(table_link):
    # Obtenir le contenu HTML de la page de la tactique
    sub_table_response = requests.get(table_link)
    sub_table_soup = BeautifulSoup(sub_table_response.text, 'html.parser')

    # Trouver la table des techniques dans la page de la tactique
    sub_table = sub_table_soup.find('table', class_='table-techniques')

    # Initialiser une liste pour stocker les données des techniques
    sub_table_data = []

    # Extraire les données des techniques
    if sub_table:
        sub_rows = sub_table.find_all('tr')[1:]  # Ignorer l'en-tête de la table
        for sub_row in sub_rows:
            sub_columns = sub_row.find_all('td')
            if len(sub_columns) == 4:
                technique_id = sub_columns[0].get_text(strip=True)
                technique_name = sub_columns[2].get_text(strip=True)
                technique_description = sub_columns[3].get_text(strip=True)
                technique_link = base_url + sub_columns[2].find('a')['href']  # Lien complet vers la technique
                # Obtenir les procédures, les mitigations et les détections pour cette technique
                procedures, mitigations, detections = extract_additional_info(technique_link)
                sub_table_data.append({
                    'Technique ID': technique_id,
                    'Technique Name': technique_name,
                    'Technique Description': technique_description,
                    'Procedures': procedures,
                    'Mitigations': mitigations,
                    'Detections': detections
                })

    return sub_table_data

def extract_additional_info(technique_link):
    response = requests.get(technique_link)
    soup = BeautifulSoup(response.text, 'html.parser')

    procedures = extract_procedures(soup)
    mitigations = extract_mitigations(soup)
    detections = extract_detections(soup)

    return procedures, mitigations, detections

def extract_procedures(soup):
    procedure_section = soup.find('h2', id='examples')
    procedures = []
    if procedure_section:
        table = procedure_section.find_next('table')
        if table:
            rows = table.find_all('tr')[1:]  # Ignorer l'en-tête de la table
            for row in rows:
                columns = row.find_all('td')
                if len(columns) == 3:
                    procedure_id = columns[0].get_text(strip=True)
                    procedure_name = columns[1].get_text(strip=True)
                    procedure_description = columns[2].get_text(strip=True)
                    procedures.append({
                        'Procedure ID': procedure_id,
                        'Procedure Name': procedure_name,
                        'Procedure Description': procedure_description
                    })
    return procedures

def extract_mitigations(soup):
    mitigation_section = soup.find('h2', id='mitigations')
    mitigations = []
    if mitigation_section:
        table = mitigation_section.find_next('table')
        if table:
            rows = table.find_all('tr')[1:]  # Ignorer l'en-tête de la table
            for row in rows:
                columns = row.find_all('td')
                if len(columns) == 3:
                    mitigation_id = columns[0].get_text(strip=True)
                    mitigation_name = columns[1].get_text(strip=True)
                    mitigation_description = columns[2].get_text(strip=True)
                    mitigations.append({
                        'Mitigation ID': mitigation_id,
                        'Mitigation Name': mitigation_name,
                        'Mitigation Description': mitigation_description
                    })
    return mitigations

def extract_detections(soup):
    detection_section = soup.find('h2', id='detection')
    detections = []
    if detection_section:
        table = detection_section.find_next('table')
        if table:
            rows = table.find_all('tr')[1:]  # Ignorer l'en-tête de la table
            for row in rows:
                columns = row.find_all('td')
                if len(columns) == 4:
                    detection_id = columns[0].get_text(strip=True)
                    data_source = columns[1].get_text(strip=True)
                    data_component = columns[2].get_text(strip=True)
                    detects_description = columns[3].get_text(strip=True)
                    detections.append({
                        'Detection ID': detection_id,
                        'Data Source': data_source,
                        'Data Component': data_component,
                        'Detects Description': detects_description
                    })
    return detections

def save_data_to_json(data, file_path):
    with open(file_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)
    print(f"Données enregistrées dans {file_path}.")

def main():
    url = f"{base_url}/tactics/enterprise/"
    tables_data = extract_tables_data(url)
    save_data_to_json(tables_data, 'mitre_tactics_techniques4.json')

if __name__ == '__main__':
    main()