import re
from datetime import datetime

def normalize_price(price_str):
    """Normalize a price string to a float, handling French formats."""
    price_str = price_str.replace('\u00a0', '').replace('\u202f', '')
    price_str = price_str.replace(' ', '').replace('\t', '')
    
    if ',' in price_str and '.' in price_str:
        if price_str.rfind(',') > price_str.rfind('.'):
            price_str = price_str.replace('.', '').replace(',', '.')
        else:
            price_str = price_str.replace(',', '')
    elif ',' in price_str:
        parts = price_str.split(',')
        if len(parts) == 2 and len(parts[1]) <= 2:
            price_str = price_str.replace(',', '.')
        else:
            price_str = price_str.replace(',', '')
    
    price_str = re.sub(r'[^\d.]', '', price_str)
    
    return float(price_str) if price_str else None

def extract_price(text, patterns):
    """Extract a price using multiple regex patterns."""
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            try:
                return normalize_price(match.group(1))
            except (ValueError, IndexError):
                continue
    return None

def extract_text(text, patterns):
    """Extract text using multiple regex patterns."""
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
    return None

def format_price(price):
    """Format price with French locale (comma as decimal separator)."""
    if price is None:
        return "Non trouvé"
    return f"{price:,.2f}".replace(',', ' ').replace('.', ',').replace(' ', ' ') + " €"

OTA_PLATFORMS = {
    'weekendesk': {
        'name': 'Weekendesk',
        'keywords': ['weekendesk', 'week-end', 'noemi.valerio@weekendesk'],
        'priority': 1
    },
    'expedia': {
        'name': 'Expedia',
        'keywords': ['expedia', 'expediapartnercentral', 'egencia', 'expedia virtual card'],
        'priority': 2
    },
    'keytel': {
        'name': 'Keytel',
        'keywords': ['keytel', 'keytel.fr', 'keytel.com'],
        'priority': 3
    },
    'smartbox': {
        'name': 'Smartbox',
        'keywords': ['smartbox', 'smart box', 'smartbox.com'],
        'priority': 4
    },
    'direct': {
        'name': 'Réservation Directe',
        'keywords': [],
        'priority': 99
    }
}

def detect_platform(email_text):
    """Auto-detect the OTA platform from email content."""
    text_lower = email_text.lower()
    
    detected = []
    for platform_id, config in OTA_PLATFORMS.items():
        for keyword in config['keywords']:
            if keyword.lower() in text_lower:
                detected.append((platform_id, config['priority']))
                break
    
    if detected:
        detected.sort(key=lambda x: x[1])
        return detected[0][0]
    
    return 'direct'

def extract_weekendesk_recapitulatif(email_text):
    """
    Extract the activity recap block from Weekendesk emails.
    The recap is between "externe à votre établissement" and "Prix établissement payé par le client"
    """
    patterns = [
        r'externe[s]?\s+[àa]\s+votre\s+[eé]tablissement\)?(.+?)Prix\s+[eé]tablissement\s+pay[eé]\s+par\s+le\s+client',
        r'R[eé]capitulatif\s+des\s+activit[eé]s(.+?)Prix\s+[eé]tablissement',
        r'(\d{1,2}/\d{1,2}/\d{4}\s*\n(?:[\s\S]*?(?:\n\d{1,2}/\d{1,2}/\d{4}[\s\S]*?)*)?)(?=\s*Prix\s+[eé]tablissement|\s*$)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, email_text, re.IGNORECASE | re.DOTALL)
        if match:
            recap = match.group(1).strip()
            lines = []
            current_date = None
            
            for line in recap.split('\n'):
                line = line.strip()
                if not line:
                    continue
                
                date_match = re.match(r'^(\d{1,2}/\d{1,2}/\d{4})$', line)
                if date_match:
                    current_date = date_match.group(1)
                    lines.append(current_date)
                elif line and not line.startswith('•'):
                    if re.match(r'^[\d\w]', line) and not re.match(r'^\d{1,2}/\d{1,2}/', line):
                        lines.append(f"• {line}")
                    else:
                        lines.append(line)
                else:
                    lines.append(line)
            
            return '\n'.join(lines)
    
    date_block_pattern = r'(\d{1,2}/\d{1,2}/\d{4}[\s\S]*?)(?=Prix\s+[eé]tablissement|Montant\s+pay[eé]|$)'
    match = re.search(date_block_pattern, email_text, re.IGNORECASE)
    if match:
        return format_recap_block(match.group(1).strip())
    
    return None

def format_recap_block(text):
    """Format the recap block with proper bullets and dates."""
    lines = []
    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue
        
        if re.match(r'^\d{1,2}/\d{1,2}/\d{4}$', line):
            lines.append(line)
        elif line and not line.startswith('•') and not line.startswith('-'):
            if not re.match(r'^(Prix|Montant|Total|EUR|€)', line, re.IGNORECASE):
                lines.append(f"• {line}")
        else:
            lines.append(line.replace('-', '•', 1) if line.startswith('-') else line)
    
    return '\n'.join(lines)

def parse_weekendesk(email_text):
    """Parse Weekendesk reservation emails."""
    result = {
        'platform': 'Weekendesk',
        'tarif': None,
        'vad': None,
        'commission': None,
        'type_hebergement': None,
        'type_chambre': None,
        'recapitulatif': None,
        'sejour_details': None,
        'dates_arrivee': None,
        'dates_depart': None,
        'carte_bancaire': None,
        'guest_name': None,
        'reservation_id': None,
        'is_virtual_card': False
    }
    
    tarif_patterns = [
        r'Prix\s+[eé]tablissement\s+pay[eé]\s+par\s+le\s+client\s*[:\-]?\s*([\d\s,\.]+)\s*(?:EUR|€)',
        r'Prix\s+client\s*[:\-]?\s*([\d\s,\.]+)\s*(?:EUR|€)',
        r'Tarif\s+client\s*[:\-]?\s*([\d\s,\.]+)\s*(?:EUR|€)',
        r'Total\s+client\s*[:\-]?\s*([\d\s,\.]+)\s*(?:EUR|€)',
    ]
    
    vad_patterns = [
        r'Montant\s+pay[eé]\s+par\s+Weekendesk\s+[àa]\s+l[\'\u2019][eé]tablissement\s*(?:\(TTC\))?\s*[:\-]?\s*([\d\s,\.]+)\s*(?:EUR|€)',
        r'Montant\s+[eé]tablissement\s*[:\-]?\s*([\d\s,\.]+)\s*(?:EUR|€)',
        r'VAD\s*[:\-]?\s*([\d\s,\.]+)\s*(?:EUR|€)',
        r'Virement\s*[:\-]?\s*([\d\s,\.]+)\s*(?:EUR|€)',
    ]
    
    result['tarif'] = extract_price(email_text, tarif_patterns)
    result['vad'] = extract_price(email_text, vad_patterns)
    
    if result['tarif'] is not None and result['vad'] is not None:
        result['commission'] = round(result['tarif'] - result['vad'], 2)
    
    hebergement_patterns = [
        r'(?:Type\s+(?:d[\'e]\s*)?(?:h[eé]bergement|chambre|logement))\s*[:\-]?\s*([^\n]+)',
        r'(?:Chambre|Suite|Room)\s*[:\-]?\s*([^\n]+)',
        r'([A-Za-z\s]+(?:Suite|Chambre|Room|Double|Single|Twin)[^\n]*)',
    ]
    type_heb = extract_text(email_text, hebergement_patterns)
    result['type_hebergement'] = type_heb
    result['type_chambre'] = type_heb
    
    result['recapitulatif'] = extract_weekendesk_recapitulatif(email_text)
    
    date_arrivee_patterns = [
        r'(?:Date\s+d[\'\u2019])?[Aa]rriv[eé]e\s*[:\-]?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
        r'[Cc]heck[\-\s]?in\s*[:\-]?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
        r'Du\s+(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
    ]
    result['dates_arrivee'] = extract_text(email_text, date_arrivee_patterns)
    
    date_depart_patterns = [
        r'(?:Date\s+de\s+)?[Dd][eé]part\s*[:\-]?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
        r'[Cc]heck[\-\s]?out\s*[:\-]?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
        r'[Aa]u\s+(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
    ]
    result['dates_depart'] = extract_text(email_text, date_depart_patterns)
    
    guest_patterns = [
        r'(?:Client|Voyageur|Guest|Nom)\s*[:\-]?\s*([A-ZÀ-Ü][a-zà-ü]+\s+[A-ZÀ-Ü][a-zà-ü]+)',
        r'M(?:me|r|lle)?\.?\s+([A-ZÀ-Ü][a-zà-ü]+\s+[A-ZÀ-Ü][a-zà-ü]+)',
    ]
    result['guest_name'] = extract_text(email_text, guest_patterns)
    
    reservation_patterns = [
        r'(?:N°\s*(?:de\s+)?r[eé]servation|R[eé]f[eé]rence|Booking\s*ID|Confirmation)\s*[:\-]?\s*([A-Z0-9\-]+)',
        r'Dossier\s*[:\-]?\s*([A-Z0-9\-]+)',
    ]
    result['reservation_id'] = extract_text(email_text, reservation_patterns)
    
    return result

def parse_expedia(email_text):
    """Parse Expedia reservation emails with virtual card detection."""
    result = {
        'platform': 'Expedia',
        'tarif': None,
        'vad': None,
        'commission': None,
        'type_hebergement': None,
        'type_chambre': None,
        'recapitulatif': None,
        'sejour_details': None,
        'dates_arrivee': None,
        'dates_depart': None,
        'carte_bancaire': None,
        'guest_name': None,
        'reservation_id': None,
        'is_virtual_card': False,
        'card_holder_name': None
    }
    
    tarif_patterns = [
        r'Prix\s+total\s*([\d\s,\.]+)\s*(?:EUR|€)',
        r'Total\s*[:\-]?\s*([\d\s,\.]+)\s*(?:EUR|€)',
        r'(\d+[\d\s,\.]*)\s*EUR\s*$',
    ]
    result['tarif'] = extract_price(email_text, tarif_patterns)
    result['vad'] = result['tarif']
    
    chambre_patterns = [
        r'Type\s+de\s+chambre\s*[:\-]?\s*([^\n]+)',
        r'(?:Chambre|Room)\s*[:\-]?\s*([^\n]+)',
    ]
    type_ch = extract_text(email_text, chambre_patterns)
    result['type_chambre'] = type_ch
    result['type_hebergement'] = type_ch
    
    card_holder_patterns = [
        r'Nom\s+du\s+d[eé]tenteur\s*[:\-]?\s*([^\n]+)',
        r'Cardholder\s*(?:name)?\s*[:\-]?\s*([^\n]+)',
        r'Card\s+holder\s*[:\-]?\s*([^\n]+)',
    ]
    card_holder = extract_text(email_text, card_holder_patterns)
    result['card_holder_name'] = card_holder
    
    if card_holder and 'expedia virtualcard' in card_holder.lower():
        result['is_virtual_card'] = True
    elif 'expedia virtual card' in email_text.lower() or 'virtualcard' in email_text.lower():
        result['is_virtual_card'] = True
    
    date_arrivee_patterns = [
        r"Date\s+d['\u2019]arriv[eé]e\s*[:\-]?\s*([A-Za-z]+\s+\d{1,2},?\s+\d{4})",
        r"Date\s+d['\u2019]arriv[eé]e\s*[:\-]?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})",
        r"Date\s+d['\u2019]arriv[eé]e\s*[:\-]?\s*(\d{1,2}\s+\w+,?\s+\d{4})",
    ]
    result['dates_arrivee'] = extract_text(email_text, date_arrivee_patterns)
    
    date_depart_patterns = [
        r"Date\s+de\s+d[eé]part\s*[:\-]?\s*([A-Za-z]+\s+\d{1,2},?\s+\d{4})",
        r"Date\s+de\s+d[eé]part\s*[:\-]?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})",
        r"Date\s+de\s+d[eé]part\s*[:\-]?\s*(\d{1,2}\s+\w+,?\s+\d{4})",
    ]
    result['dates_depart'] = extract_text(email_text, date_depart_patterns)
    
    guest_patterns = [
        r'Information\s+du\s+client\s*([A-ZÀ-Ü][a-zà-ü]+\s+[A-ZÀ-Ü][a-zà-ü]+)',
        r'^([A-ZÀ-Ü][a-zà-ü]+\s+[A-ZÀ-Ü][a-zà-ü]+)\s*Courriel',
    ]
    result['guest_name'] = extract_text(email_text, guest_patterns)
    
    reservation_patterns = [
        r'Numéro\s+de\s+confirmation\s*[:\-]?\s*(\d+)',
        r'Ref[:\-]?\s*(\d+)',
    ]
    result['reservation_id'] = extract_text(email_text, reservation_patterns)
    
    nights_pattern = r'Nombre\s+de\s+nuits\s*[:\-]?\s*(\d+)\s*nuit'
    nights = extract_text(email_text, [nights_pattern])
    if nights and result['type_chambre']:
        result['sejour_details'] = f"{nights} nuit(s) en {result['type_chambre']}"
    elif nights:
        result['sejour_details'] = f"{nights} nuit(s)"
    
    return result

def parse_direct(email_text):
    """Parse direct reservation emails."""
    result = {
        'platform': 'Réservation Directe',
        'tarif': None,
        'vad': None,
        'commission': 0.0,
        'type_hebergement': None,
        'type_chambre': None,
        'recapitulatif': None,
        'sejour_details': None,
        'dates_arrivee': None,
        'dates_depart': None,
        'carte_bancaire': None,
        'guest_name': None,
        'reservation_id': None,
        'is_virtual_card': False
    }
    
    tarif_patterns = [
        r'Prix\s+total\s*([\d\s,\.]+)\s*(?:EUR|€)',
        r'Total\s*[:\-]?\s*([\d\s,\.]+)\s*(?:EUR|€)',
        r'Montant\s*[:\-]?\s*([\d\s,\.]+)\s*(?:EUR|€)',
    ]
    result['tarif'] = extract_price(email_text, tarif_patterns)
    result['vad'] = result['tarif']
    
    chambre_patterns = [
        r'Type\s+de\s+chambre\s*[:\-]?\s*([^\n]+)',
        r'(?:Chambre|Room)\s*[:\-]?\s*([^\n]+)',
    ]
    type_ch = extract_text(email_text, chambre_patterns)
    result['type_chambre'] = type_ch
    result['type_hebergement'] = type_ch
    
    date_arrivee_patterns = [
        r"Date\s+d['\u2019]arriv[eé]e\s*[:\-]?\s*(\d{1,2}\s+\w+,?\s+\d{4})",
        r"Date\s+d['\u2019]arriv[eé]e\s*[:\-]?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})",
    ]
    result['dates_arrivee'] = extract_text(email_text, date_arrivee_patterns)
    
    date_depart_patterns = [
        r"Date\s+de\s+d[eé]part\s*[:\-]?\s*(\d{1,2}\s+\w+,?\s+\d{4})",
        r"Date\s+de\s+d[eé]part\s*[:\-]?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})",
    ]
    result['dates_depart'] = extract_text(email_text, date_depart_patterns)
    
    guest_patterns = [
        r'Information\s+du\s+client\s*([A-ZÀ-Ü][a-zà-ü]+\s+[A-ZÀ-Ü]+)',
        r'^([A-ZÀ-Ü][a-zà-ü]+\s+[A-ZÀ-Ü]+)\s*Courriel',
    ]
    result['guest_name'] = extract_text(email_text, guest_patterns)
    
    reservation_patterns = [
        r'Numéro\s+de\s+confirmation\s*[:\-]?\s*(\d+)',
        r'Ref[:\-]?\s*(\d+)',
    ]
    result['reservation_id'] = extract_text(email_text, reservation_patterns)
    
    return result

def parse_keytel(email_text):
    """Parse Keytel reservation emails."""
    result = {
        'platform': 'Keytel',
        'tarif': None,
        'vad': None,
        'commission': 0.0,
        'type_hebergement': None,
        'type_chambre': None,
        'recapitulatif': None,
        'sejour_details': None,
        'dates_arrivee': None,
        'dates_depart': None,
        'carte_bancaire': None,
        'guest_name': None,
        'reservation_id': None,
        'is_virtual_card': False
    }
    
    tarif_patterns = [
        r'Prix\s+total\s*([\d\s,\.]+)\s*(?:EUR|€)',
        r'Total\s*[:\-]?\s*([\d\s,\.]+)\s*(?:EUR|€)',
        r'Montant\s*[:\-]?\s*([\d\s,\.]+)\s*(?:EUR|€)',
    ]
    result['tarif'] = extract_price(email_text, tarif_patterns)
    result['vad'] = result['tarif']
    
    chambre_patterns = [
        r'Type\s+de\s+chambre\s*[:\-]?\s*([^\n]+)',
        r'(?:Chambre|Room)\s*[:\-]?\s*([^\n]+)',
    ]
    type_ch = extract_text(email_text, chambre_patterns)
    result['type_chambre'] = type_ch
    result['type_hebergement'] = type_ch
    
    date_arrivee_patterns = [
        r"Date\s+d['\u2019]arriv[eé]e\s*[:\-]?\s*(\d{1,2}\s+\w+,?\s+\d{4})",
        r"Date\s+d['\u2019]arriv[eé]e\s*[:\-]?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})",
        r'(?:Arriv[eé]e|Check[\-\s]?in)\s*[:\-]?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
    ]
    result['dates_arrivee'] = extract_text(email_text, date_arrivee_patterns)
    
    date_depart_patterns = [
        r"Date\s+de\s+d[eé]part\s*[:\-]?\s*(\d{1,2}\s+\w+,?\s+\d{4})",
        r"Date\s+de\s+d[eé]part\s*[:\-]?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})",
        r'(?:D[eé]part|Check[\-\s]?out)\s*[:\-]?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
    ]
    result['dates_depart'] = extract_text(email_text, date_depart_patterns)
    
    guest_patterns = [
        r'(?:Client|Voyageur|Guest|Nom)\s*[:\-]?\s*([A-ZÀ-Ü][a-zà-ü]+\s+[A-ZÀ-Ü][a-zà-ü]+)',
        r'M(?:me|r|lle)?\.?\s+([A-ZÀ-Ü][a-zà-ü]+\s+[A-ZÀ-Ü][a-zà-ü]+)',
    ]
    result['guest_name'] = extract_text(email_text, guest_patterns)
    
    reservation_patterns = [
        r'(?:N°\s*(?:de\s+)?r[eé]servation|R[eé]f[eé]rence|Confirmation)\s*[:\-]?\s*([A-Z0-9\-]+)',
        r'Dossier\s*[:\-]?\s*([A-Z0-9\-]+)',
    ]
    result['reservation_id'] = extract_text(email_text, reservation_patterns)
    
    return result

def extract_smartbox_recapitulatif(email_text):
    """Extract the activity recap block from Smartbox emails."""
    patterns = [
        r'R[eé]capitulatif\s*[:\-]?\s*([^\n]+(?:\n[^\n]+)*?)(?=\s*(?:Prix|Total|Montant|$))',
        r'D[eé]tails?\s+(?:du\s+)?s[eé]jour\s*[:\-]?\s*([^\n]+(?:\n[^\n]+)*?)(?=\s*(?:Prix|Total|Montant|$))',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, email_text, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
    
    return None

def parse_smartbox(email_text):
    """Parse Smartbox reservation emails."""
    result = {
        'platform': 'Smartbox',
        'tarif': None,
        'vad': None,
        'commission': None,
        'type_hebergement': None,
        'type_chambre': None,
        'recapitulatif': None,
        'sejour_details': None,
        'dates_arrivee': None,
        'dates_depart': None,
        'carte_bancaire': None,
        'guest_name': None,
        'reservation_id': None,
        'is_virtual_card': False
    }
    
    tarif_patterns = [
        r'Prix\s+client\s*[:\-]?\s*([\d\s,\.]+)\s*(?:EUR|€)',
        r'Prix\s+total\s*[:\-]?\s*([\d\s,\.]+)\s*(?:EUR|€)',
        r'Total\s+client\s*[:\-]?\s*([\d\s,\.]+)\s*(?:EUR|€)',
    ]
    result['tarif'] = extract_price(email_text, tarif_patterns)
    
    vad_patterns = [
        r'Prix\s+hors\s+commission\s*[:\-]?\s*([\d\s,\.]+)\s*(?:EUR|€)',
        r'Montant\s+[eé]tablissement\s*[:\-]?\s*([\d\s,\.]+)\s*(?:EUR|€)',
        r'Net\s+[eé]tablissement\s*[:\-]?\s*([\d\s,\.]+)\s*(?:EUR|€)',
    ]
    result['vad'] = extract_price(email_text, vad_patterns)
    
    commission_patterns = [
        r'Commission\s*[:\-]?\s*([\d\s,\.]+)\s*(?:EUR|€)',
        r'Frais\s+Smartbox\s*[:\-]?\s*([\d\s,\.]+)\s*(?:EUR|€)',
    ]
    result['commission'] = extract_price(email_text, commission_patterns)
    
    if result['tarif'] is not None and result['vad'] is not None and result['commission'] is None:
        result['commission'] = round(result['tarif'] - result['vad'], 2)
    
    hebergement_patterns = [
        r'(?:Type\s+(?:d[\'e]\s*)?(?:h[eé]bergement|chambre|logement))\s*[:\-]?\s*([^\n]+)',
        r'(?:Chambre|Suite|Room)\s*[:\-]?\s*([^\n]+)',
        r'Coffret\s*[:\-]?\s*([^\n]+)',
    ]
    type_heb = extract_text(email_text, hebergement_patterns)
    result['type_hebergement'] = type_heb
    result['type_chambre'] = type_heb
    
    result['recapitulatif'] = extract_smartbox_recapitulatif(email_text)
    
    date_arrivee_patterns = [
        r"Date\s+d['\u2019]arriv[eé]e\s*[:\-]?\s*(\d{1,2}\s+\w+,?\s+\d{4})",
        r"Date\s+d['\u2019]arriv[eé]e\s*[:\-]?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})",
        r'(?:Arriv[eé]e|Check[\-\s]?in)\s*[:\-]?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
    ]
    result['dates_arrivee'] = extract_text(email_text, date_arrivee_patterns)
    
    date_depart_patterns = [
        r"Date\s+de\s+d[eé]part\s*[:\-]?\s*(\d{1,2}\s+\w+,?\s+\d{4})",
        r"Date\s+de\s+d[eé]part\s*[:\-]?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})",
        r'(?:D[eé]part|Check[\-\s]?out)\s*[:\-]?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
    ]
    result['dates_depart'] = extract_text(email_text, date_depart_patterns)
    
    guest_patterns = [
        r'(?:Client|Voyageur|Guest|Nom)\s*[:\-]?\s*([A-ZÀ-Ü][a-zà-ü]+\s+[A-ZÀ-Ü][a-zà-ü]+)',
        r'M(?:me|r|lle)?\.?\s+([A-ZÀ-Ü][a-zà-ü]+\s+[A-ZÀ-Ü][a-zà-ü]+)',
        r'B[eé]n[eé]ficiaire\s*[:\-]?\s*([A-ZÀ-Ü][a-zà-ü]+\s+[A-ZÀ-Ü][a-zà-ü]+)',
    ]
    result['guest_name'] = extract_text(email_text, guest_patterns)
    
    reservation_patterns = [
        r'(?:N°\s*(?:de\s+)?r[eé]servation|R[eé]f[eé]rence|Confirmation)\s*[:\-]?\s*([A-Z0-9\-]+)',
        r'Code\s+Smartbox\s*[:\-]?\s*([A-Z0-9\-]+)',
        r'Dossier\s*[:\-]?\s*([A-Z0-9\-]+)',
    ]
    result['reservation_id'] = extract_text(email_text, reservation_patterns)
    
    return result

PARSERS = {
    'weekendesk': parse_weekendesk,
    'expedia': parse_expedia,
    'keytel': parse_keytel,
    'smartbox': parse_smartbox,
    'direct': parse_direct,
}

def parse_email(email_text, platform=None):
    """Parse email based on detected or specified platform."""
    if platform is None:
        platform = detect_platform(email_text)
    
    parser = PARSERS.get(platform, parse_direct)
    return parser(email_text)

def generate_summary(data, receptionist_name):
    """Generate the formatted summary using templates."""
    from templates import generate_summary_with_template
    return generate_summary_with_template(data, receptionist_name)

def get_platform_list():
    """Return list of supported platforms for UI."""
    return [(pid, cfg['name']) for pid, cfg in OTA_PLATFORMS.items()]
