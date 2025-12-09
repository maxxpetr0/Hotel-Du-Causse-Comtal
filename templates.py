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
    'direct': {
        'name': 'Réservation Directe',
        'description': 'Format pour réservations directes avec garantie CB'
    },
    'booking': {
        'name': 'Booking.com',
        'description': 'Format pour réservations Booking.com'
    },
    'originals': {
        'name': 'The Originals',
        'description': 'Format pour réservations The Originals'
    },
    'airbnb': {
        'name': 'Airbnb',
        'description': 'Format pour réservations Airbnb'
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

def generate_booking(data, receptionist_name):
    """Format Booking.com."""
    today = datetime.now().strftime("%d/%m/%Y")
    
    lines = ["Booking.com"]
    
    if data.get('type_chambre'):
        lines.append(data['type_chambre'])
    
    tarif = data.get('tarif')
    commission = data.get('commission')
    vad = data.get('vad')
    
    lines.append(f"Total : {format_price_eur(tarif)}")
    if vad:
        lines.append(f"Net : {format_price_eur(vad)}")
    if commission:
        lines.append(f"Commission : {format_price_eur(commission)}")
    
    if data.get('guest_name'):
        lines.append(f"Client : {data['guest_name']}")
    
    if data.get('dates_arrivee') and data.get('dates_depart'):
        lines.append(f"Du {data['dates_arrivee']} au {data['dates_depart']}")
    
    lines.append("Encaisser TDS + Extras")
    lines.append(f"{receptionist_name}, le {today}")
    
    return "\n".join(lines)

def generate_originals(data, receptionist_name):
    """Format The Originals."""
    today = datetime.now().strftime("%d/%m/%Y")
    
    lines = ["The Originals"]
    
    if data.get('type_chambre'):
        lines.append(data['type_chambre'])
    
    tarif = data.get('tarif')
    lines.append(f"Total : {format_price_eur(tarif)}")
    
    if data.get('sejour_details'):
        lines.append(data['sejour_details'])
    
    if data.get('dates_arrivee') and data.get('dates_depart'):
        lines.append(f"Du {data['dates_arrivee']} au {data['dates_depart']}")
    
    lines.append("Encaisser la totalité + TDS + Extras")
    lines.append(f"{receptionist_name}, le {today}")
    
    return "\n".join(lines)

def generate_airbnb(data, receptionist_name):
    """Format Airbnb."""
    today = datetime.now().strftime("%d/%m/%Y")
    
    lines = ["Airbnb"]
    
    tarif = data.get('tarif')
    vad = data.get('vad')
    commission = data.get('commission')
    
    lines.append(f"Total voyageur : {format_price_eur(tarif)}")
    lines.append(f"Versement hôte : {format_price_eur(vad)}")
    if commission:
        lines.append(f"Frais Airbnb : {format_price_eur(commission)}")
    
    if data.get('guest_name'):
        lines.append(f"Voyageur : {data['guest_name']}")
    
    if data.get('dates_arrivee') and data.get('dates_depart'):
        lines.append(f"Du {data['dates_arrivee']} au {data['dates_depart']}")
    
    lines.append("Paiement via Airbnb")
    lines.append(f"{receptionist_name}, le {today}")
    
    return "\n".join(lines)

TEMPLATE_GENERATORS = {
    'weekendesk': generate_weekendesk,
    'expedia': generate_expedia,
    'direct': generate_direct,
    'booking': generate_booking,
    'originals': generate_originals,
    'airbnb': generate_airbnb
}

def generate_summary_with_template(data, receptionist_name, template_id=None):
    """Generate summary using the appropriate template based on platform."""
    if template_id is None:
        platform = data.get('platform', '').lower()
        if 'weekendesk' in platform:
            template_id = 'weekendesk'
        elif 'expedia' in platform:
            template_id = 'expedia'
        elif 'booking' in platform:
            template_id = 'booking'
        elif 'originals' in platform:
            template_id = 'originals'
        elif 'airbnb' in platform:
            template_id = 'airbnb'
        else:
            template_id = 'direct'
    
    generator = TEMPLATE_GENERATORS.get(template_id, generate_direct)
    return generator(data, receptionist_name)

def get_template_list():
    """Return list of available templates for UI."""
    return [(tid, cfg['name'], cfg['description']) for tid, cfg in TEMPLATES.items()]
