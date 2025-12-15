from datetime import datetime

TEMPLATES = {
    'weekendesk': {
        'name': 'Weekendesk',
        'description': 'Format pour réservations Weekendesk avec récapitulatif des activités'
    },
    'expedia': {
        'name': 'Expedia / Egencia',
        'description': 'Format pour réservations Expedia avec logique carte virtuelle'
    },
    'keytel': {
        'name': 'Keytel',
        'description': 'Format pour réservations Keytel avec PDJ inclus'
    },
    'smartbox': {
        'name': 'Smartbox',
        'description': 'Format pour réservations Smartbox avec commission'
    },
    'direct': {
        'name': 'Réservation Directe',
        'description': 'Format pour réservations directes avec garantie CB'
    }
}

def format_price_eur(price):
    """Format price as X.XX EUR."""
    if price is None:
        return "[Non trouvé]"
    return f"{price:.2f} EUR"

def generate_weekendesk(data, receptionist_name):
    """
    Format Weekendesk exact :
    Weekendesk
    [TYPE_HEBERGEMENT]
    Total : [PRIX_CLIENT] EUR
    Payline : [MONTANT_WEEKENDESK] EUR
    Commission : [COMMISSION] EUR
    [RECAPITULATIF avec dates et bullets]
    Encaisser TDS + Extras
    [Réceptionniste], le [DATE_DU_JOUR]
    """
    today = datetime.now().strftime("%d/%m/%Y")
    
    lines = ["Weekendesk"]
    
    type_heb = data.get('type_hebergement')
    if type_heb:
        lines.append(type_heb)
    else:
        lines.append("[Type d'hébergement non détecté]")
    
    tarif = data.get('tarif')
    vad = data.get('vad')
    commission = data.get('commission')
    
    lines.append(f"Total : {format_price_eur(tarif)}")
    lines.append(f"Payline : {format_price_eur(vad)}")
    lines.append(f"Commission : {format_price_eur(commission)}")
    
    recapitulatif = data.get('recapitulatif')
    if recapitulatif:
        lines.append(recapitulatif)
    else:
        if data.get('dates_arrivee') and data.get('dates_depart'):
            lines.append(f"Du {data['dates_arrivee']} au {data['dates_depart']}")
        if data.get('sejour_details'):
            lines.append(data['sejour_details'])
    
    lines.append("Encaisser TDS + Extras")
    lines.append(f"{receptionist_name}, le {today}")
    
    return "\n".join(lines)

def generate_expedia(data, receptionist_name):
    """
    Format Expedia :
    EXPEDIA
    [TYPE_CHAMBRE]
    [Logique paiement conditionnelle]
    [Réceptionniste], le [DATE_DU_JOUR]
    
    Logique paiement :
    - Si carte virtuelle Expedia : "Faire Payline [PRIX] + Encaisser TDS et Extras"
    - Sinon : "Encaisser la totalité"
    """
    today = datetime.now().strftime("%d/%m/%Y")
    
    lines = ["EXPEDIA"]
    
    type_ch = data.get('type_chambre')
    if type_ch:
        lines.append(type_ch)
    else:
        lines.append("[Type de chambre non détecté]")
    
    is_virtual_card = data.get('is_virtual_card', False)
    tarif = data.get('tarif')
    
    if is_virtual_card and tarif is not None:
        lines.append(f"Faire Payline {format_price_eur(tarif)} + Encaisser TDS et Extras")
    elif is_virtual_card:
        lines.append("Faire Payline [Montant non trouvé] + Encaisser TDS et Extras")
    else:
        lines.append("Encaisser la totalité")
    
    lines.append(f"{receptionist_name}, le {today}")
    
    return "\n".join(lines)

def generate_direct(data, receptionist_name):
    """
    Format Réservation Directe :
    Réservation Directe (Garantie CB)
    [TYPE_CHAMBRE]
    Encaisser la totalité ([PRIX_TOTAL_TTC]) + TDS + Extras
    [Réceptionniste], le [DATE_DU_JOUR]
    """
    today = datetime.now().strftime("%d/%m/%Y")
    
    lines = ["Réservation Directe (Garantie CB)"]
    
    type_ch = data.get('type_chambre')
    if type_ch:
        lines.append(type_ch)
    else:
        lines.append("[Type de chambre non détecté]")
    
    tarif = data.get('tarif')
    if tarif is not None:
        lines.append(f"Encaisser la totalité ({format_price_eur(tarif)}) + TDS + Extras")
    else:
        lines.append("Encaisser la totalité + TDS + Extras")
    
    lines.append(f"{receptionist_name}, le {today}")
    
    return "\n".join(lines)

def generate_keytel(data, receptionist_name):
    """
    Format Keytel :
    KEYTEL
    [TYPE_CHAMBRE]
    Total [PRIX_TOTAL] € PDJ Inclus
    Paiement Keytel
    Encaisser TDS + Extras
    [Réceptionniste], le [DATE_DU_JOUR]
    """
    today = datetime.now().strftime("%d/%m/%Y")
    
    lines = ["KEYTEL"]
    
    type_ch = data.get('type_chambre')
    if type_ch:
        lines.append(type_ch)
    else:
        lines.append("[Type de chambre non détecté]")
    
    tarif = data.get('tarif')
    if tarif is not None:
        lines.append(f"Total {tarif:.2f} € PDJ Inclus")
    else:
        lines.append("Total [Non trouvé] € PDJ Inclus")
    
    lines.append("Paiement Keytel")
    lines.append("Encaisser TDS + Extras")
    lines.append(f"{receptionist_name}, le {today}")
    
    return "\n".join(lines)

def generate_smartbox(data, receptionist_name):
    """
    Format Smartbox :
    Smartbox
    [TYPE_HEBERGEMENT]
    Prix total : [VALEUR DE PRIX_CLIENT]
    Prix hors commission : [PRIX_HORS_COMMISSION]
    Commission : [VALEUR DE COMMISSION]
    [VALEUR DE RECAPITULATIF]
    Encaisser TDS + Extras
    [Réceptionniste], le [DATE_DU_JOUR]
    """
    today = datetime.now().strftime("%d/%m/%Y")
    
    lines = ["Smartbox"]
    
    type_heb = data.get('type_hebergement')
    if type_heb:
        lines.append(type_heb)
    else:
        lines.append("[Type d'hébergement non détecté]")
    
    tarif = data.get('tarif')
    vad = data.get('vad')
    commission = data.get('commission')
    
    lines.append(f"Prix total : {format_price_eur(tarif)}")
    lines.append(f"Prix hors commission : {format_price_eur(vad)}")
    lines.append(f"Commission : {format_price_eur(commission)}")
    
    recapitulatif = data.get('recapitulatif')
    if recapitulatif:
        lines.append(recapitulatif)
    else:
        if data.get('dates_arrivee') and data.get('dates_depart'):
            lines.append(f"Du {data['dates_arrivee']} au {data['dates_depart']}")
        if data.get('sejour_details'):
            lines.append(data['sejour_details'])
    
    lines.append("Encaisser TDS + Extras")
    lines.append(f"{receptionist_name}, le {today}")
    
    return "\n".join(lines)

TEMPLATE_GENERATORS = {
    'weekendesk': generate_weekendesk,
    'expedia': generate_expedia,
    'keytel': generate_keytel,
    'smartbox': generate_smartbox,
    'direct': generate_direct,
}

def generate_summary_with_template(data, receptionist_name, template_id=None):
    """Generate summary using the appropriate template based on platform."""
    if template_id is None:
        platform = data.get('platform', '').lower()
        if 'weekendesk' in platform:
            template_id = 'weekendesk'
        elif 'expedia' in platform:
            template_id = 'expedia'
        elif 'keytel' in platform:
            template_id = 'keytel'
        elif 'smartbox' in platform:
            template_id = 'smartbox'
        else:
            template_id = 'direct'
    
    generator = TEMPLATE_GENERATORS.get(template_id, generate_direct)
    return generator(data, receptionist_name)

def get_template_list():
    """Return list of available templates for UI."""
    return [(tid, cfg['name'], cfg['description']) for tid, cfg in TEMPLATES.items()]
