import pandas as pd
import re
import io

def parse_name(full_name):
    """
    Sépare NOM Prénom à partir d'une chaîne.
    La partie en MAJUSCULES = Nom, le reste = Prénom.
    """
    if not full_name or pd.isna(full_name):
        return "_", "_"
    
    full_name = str(full_name).strip()
    
    words = full_name.split()
    nom_parts = []
    prenom_parts = []
    
    for word in words:
        if word.isupper():
            nom_parts.append(word)
        else:
            prenom_parts.append(word)
    
    nom = " ".join(nom_parts) if nom_parts else "_"
    prenom = " ".join(prenom_parts) if prenom_parts else "_"
    
    return nom, prenom

def transform_email(email):
    """
    Transforme l'email : si contient 'm.expediapartnercentral.com', retourne 'EXPEDIA'.
    """
    if not email or pd.isna(email):
        return "_"
    
    email = str(email).strip()
    
    if "m.expediapartnercentral.com" in email.lower():
        return "EXPEDIA"
    
    return email if email else "_"

def fill_empty(value):
    """Remplace les valeurs vides par '_'."""
    if pd.isna(value) or str(value).strip() == "":
        return "_"
    return str(value).strip()

def parse_csv_data(file_content, separator=';'):
    """
    Parse le contenu CSV et retourne un DataFrame transformé.
    """
    try:
        df = pd.read_csv(io.StringIO(file_content), sep=separator, encoding='utf-8-sig')
    except Exception as e:
        try:
            df = pd.read_csv(io.StringIO(file_content), sep=separator, encoding='latin-1')
        except Exception as e2:
            raise ValueError(f"Impossible de lire le fichier CSV: {str(e2)}")
    
    result_data = []
    
    for _, row in df.iterrows():
        date_checkin = fill_empty(row.get('Date arrivée', row.get('Date arrivee', '')))
        
        full_name = row.get('Nom', '')
        nom, prenom = parse_name(full_name)
        
        email = row.get('Email', '')
        mail = transform_email(email)
        
        result_data.append({
            'Date de checkin': date_checkin,
            'Nom': nom,
            'Prénom': prenom,
            'Mail': mail,
            'Plan Tarifaire': '_',
            'Provenance': '_',
            'Groupe': '_',
            'Catégorie': '_'
        })
    
    return pd.DataFrame(result_data)

def generate_markdown_table(df):
    """
    Génère un tableau Markdown avec double en-tête.
    """
    lines = []
    
    lines.append("Date de checkin;Nom;Prénom;Mail;Plan Tarifaire;Champs Marketing;;")
    
    lines.append(";;;;;Provenance;Groupe;Catégorie")
    
    for _, row in df.iterrows():
        line = f"{row['Date de checkin']};{row['Nom']};{row['Prénom']};{row['Mail']};{row['Plan Tarifaire']};{row['Provenance']};{row['Groupe']};{row['Catégorie']}"
        lines.append(line)
    
    return "\n".join(lines)

def process_pms_file(file_content, separator=';'):
    """
    Traite le fichier PMS complet et retourne le tableau Markdown.
    """
    df = parse_csv_data(file_content, separator)
    markdown_output = generate_markdown_table(df)
    return df, markdown_output
