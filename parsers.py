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
    'booking': {
        'name': 'Booking.com',
        'keywords': ['booking.com', 'booking', 'réservation booking'],
        'priority': 3
    },
    'originals': {
        'name': 'The Originals',
        'keywords': ['the originals', 'originals relais', 'club (en €)', 'demi-pension'],
        'priority': 4
    },
    'airbnb': {
        'name': 'Airbnb',
        'keywords': ['airbnb', 'air bnb'],
        'priority': 5
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
    
    return 'weekendesk'

def parse_weekendesk(email_text):
    """Parse Weekendesk reservation emails."""
    result = {
        'platform': 'Weekendesk',
        'tarif': None,
        'vad': None,
        'commission': None,
        'sejour_details': None,
        'dates_arrivee': None,
        'dates_depart': None,
        'carte_bancaire': None,
        'guest_name': None,
        'reservation_id': None,
        'raw_tarif_line': None,
        'raw_vad_line': None
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
    
    sejour_patterns = [
        r'S[eé]jour\s*[:\-]?\s*(.+?)(?:\n|$)',
        r'(\d+\s*nuits?\s+en\s+.+?)(?:\n|$)',
        r'(\d+\s*nuits?\s+.+?chambre.+?)(?:\n|$)',
    ]
    result['sejour_details'] = extract_text(email_text, sejour_patterns)
    
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
    
    cb_patterns = [
        r'((?:Carte\s+(?:bancaire\s+)?virtuelle|VCC|Virtual\s+Card)[:\s]*[\s\S]*?(?:CVV|CVC|Code)[:\s]*\d{3,4})',
        r'(N(?:um[eé]ro|°)\s*(?:de\s+)?carte\s*[:\-]?\s*[\d\s\*]+[\s\S]*?(?:CVV|CVC|Code)[:\s]*\d{3,4})',
        r'(Carte\s*[:\-]?\s*\d{4}[\s\*\-]+\d{4}[\s\*\-]+\d{4}[\s\*\-]+\d{4}[\s\S]*?(?:Expiration|Exp|Valid)[:\s]*[\d\/]+)',
    ]
    result['carte_bancaire'] = extract_text(email_text, cb_patterns)
    
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
    
    tarif_line_patterns = [
        r'(Prix\s+[eé]tablissement\s+pay[eé]\s+par\s+le\s+client\s*[:\-]?\s*[\d\s,\.]+\s*(?:EUR|€))',
    ]
    result['raw_tarif_line'] = extract_text(email_text, tarif_line_patterns)
    
    vad_line_patterns = [
        r'(Montant\s+pay[eé]\s+par\s+Weekendesk\s+[àa]\s+l[\'\u2019][eé]tablissement\s*(?:\(TTC\))?\s*[:\-]?\s*[\d\s,\.]+\s*(?:EUR|€))',
    ]
    result['raw_vad_line'] = extract_text(email_text, vad_line_patterns)
    
    return result

def parse_booking(email_text):
    """Parse Booking.com reservation emails."""
    result = {
        'platform': 'Booking.com',
        'tarif': None,
        'vad': None,
        'commission': None,
        'sejour_details': None,
        'dates_arrivee': None,
        'dates_depart': None,
        'carte_bancaire': None,
        'guest_name': None,
        'reservation_id': None,
        'raw_tarif_line': None,
        'raw_vad_line': None
    }
    
    tarif_patterns = [
        r'(?:Total|Prix\s+total|Montant\s+total)\s*[:\-]?\s*([\d\s,\.]+)\s*(?:EUR|€)',
        r'(?:Price|Amount)\s*[:\-]?\s*([\d\s,\.]+)\s*(?:EUR|€)',
        r'(\d+[\d\s,\.]*)\s*(?:EUR|€)\s*(?:au\s+total|total)',
    ]
    
    commission_patterns = [
        r'(?:Commission|Frais)\s*[:\-]?\s*([\d\s,\.]+)\s*(?:EUR|€|%)',
        r'(\d+[\d\s,\.]*)\s*%\s*(?:de\s+)?commission',
    ]
    
    result['tarif'] = extract_price(email_text, tarif_patterns)
    
    commission_match = extract_price(email_text, commission_patterns)
    if commission_match:
        if '%' in email_text and result['tarif']:
            result['commission'] = round(result['tarif'] * commission_match / 100, 2)
        else:
            result['commission'] = commission_match
        
        if result['tarif'] and result['commission']:
            result['vad'] = round(result['tarif'] - result['commission'], 2)
    
    sejour_patterns = [
        r'(\d+)\s*(?:nuit|night)s?',
        r'(\d+\s*x\s*[^,\n]+)',
        r'(?:Chambre|Room)\s*[:\-]?\s*([^\n]+)',
    ]
    nights_match = extract_text(email_text, [r'(\d+)\s*(?:nuit|night)s?'])
    room_match = extract_text(email_text, [r'(?:Chambre|Room|Type)\s*[:\-]?\s*([^\n]+)'])
    if nights_match and room_match:
        result['sejour_details'] = f"{nights_match} nuit(s) - {room_match}"
    elif nights_match:
        result['sejour_details'] = f"{nights_match} nuit(s)"
    elif room_match:
        result['sejour_details'] = room_match
    
    date_arrivee_patterns = [
        r'(?:Arriv[eé]e|Check[\-\s]?in|From)\s*[:\-]?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
        r'(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})\s*[\-–]\s*\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}',
        r'(\d{1,2}\s+(?:jan|f[eé]v|mar|avr|mai|juin|juil|ao[uû]|sep|oct|nov|d[eé]c)[a-z]*\s+\d{2,4})',
    ]
    result['dates_arrivee'] = extract_text(email_text, date_arrivee_patterns)
    
    date_depart_patterns = [
        r'(?:D[eé]part|Check[\-\s]?out|To)\s*[:\-]?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
        r'\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}\s*[\-–]\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
    ]
    result['dates_depart'] = extract_text(email_text, date_depart_patterns)
    
    cb_patterns = [
        r'((?:Carte|Card)[:\s]*[\d\*\s]+[\s\S]*?(?:CVV|CVC|Exp)[:\s]*[\d\/]+)',
        r'((?:Virtual\s+)?(?:Credit\s+)?Card[:\s]*[\s\S]*?(?:Security|CVV)[:\s]*\d{3,4})',
    ]
    result['carte_bancaire'] = extract_text(email_text, cb_patterns)
    
    guest_patterns = [
        r'(?:Guest|Client|Voyageur|Booker)\s*(?:name)?\s*[:\-]?\s*([A-ZÀ-Ü][a-zà-ü]+(?:\s+[A-ZÀ-Ü][a-zà-ü]+)+)',
        r'(?:Réservation\s+(?:de|pour|by))\s+([A-ZÀ-Ü][a-zà-ü]+(?:\s+[A-ZÀ-Ü][a-zà-ü]+)+)',
    ]
    result['guest_name'] = extract_text(email_text, guest_patterns)
    
    reservation_patterns = [
        r'(?:Confirmation|Booking|Reservation)\s*(?:number|ID|N°)?\s*[:\-]?\s*(\d+)',
        r'#\s*(\d+)',
    ]
    result['reservation_id'] = extract_text(email_text, reservation_patterns)
    
    return result

def parse_expedia(email_text):
    """Parse Expedia reservation emails."""
    result = {
        'platform': 'Expedia',
        'tarif': None,
        'vad': None,
        'commission': None,
        'sejour_details': None,
        'dates_arrivee': None,
        'dates_depart': None,
        'carte_bancaire': None,
        'guest_name': None,
        'reservation_id': None,
        'raw_tarif_line': None,
        'raw_vad_line': None
    }
    
    tarif_patterns = [
        r'Prix\s+total\s*([\d\s,\.]+)\s*(?:EUR|€)',
        r'(\d+[\d\s,\.]*)\s*EUR\s*$',
    ]
    result['tarif'] = extract_price(email_text, tarif_patterns)
    result['vad'] = result['tarif']
    
    nights_pattern = r'Nombre\s+de\s+nuits\s*[:\-]?\s*(\d+)\s*nuit'
    room_pattern = r'Type\s+de\s+chambre\s*[:\-]?\s*([^\n]+)'
    nights = extract_text(email_text, [nights_pattern])
    room = extract_text(email_text, [room_pattern])
    if nights and room:
        result['sejour_details'] = f"{nights} nuit(s) en {room.strip()}"
    elif nights:
        result['sejour_details'] = f"{nights} nuit(s)"
    elif room:
        result['sejour_details'] = room.strip()
    
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
    
    cb_patterns = [
        r'Type\s+de\s+carte\s*[:\-]?\s*(\w+)\s*Numéro\s+de\s+carte\s*[:\-]?\s*([\d\*]+)\s*Expiration\s*[:\-]?\s*([^\n]+)\s*Nom\s+du\s+détenteur\s*[:\-]?\s*([^\n]+)',
    ]
    cb_match = re.search(cb_patterns[0], email_text, re.IGNORECASE | re.DOTALL)
    if cb_match:
        result['carte_bancaire'] = f"{cb_match.group(1)} {cb_match.group(2)} - {cb_match.group(4).strip()}"
    
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
    
    return result

def parse_originals(email_text):
    """Parse The Originals direct booking emails."""
    result = {
        'platform': 'The Originals',
        'tarif': None,
        'vad': None,
        'commission': None,
        'sejour_details': None,
        'dates_arrivee': None,
        'dates_depart': None,
        'carte_bancaire': None,
        'guest_name': None,
        'reservation_id': None,
        'raw_tarif_line': None,
        'raw_vad_line': None
    }
    
    tarif_patterns = [
        r'Prix\s+total\s*([\d\s,\.]+)\s*(?:EUR|€)',
        r'(\d+[\d\s,\.]*)\s*EUR\s*$',
    ]
    result['tarif'] = extract_price(email_text, tarif_patterns)
    result['vad'] = result['tarif']
    result['commission'] = 0.0
    
    nights_pattern = r'Nombre\s+de\s+nuits\s*[:\-]?\s*(\d+)\s*nuit'
    room_pattern = r'Type\s+de\s+chambre\s*[:\-]?\s*([^\n]+)'
    tarif_jour_pattern = r'Tarif\s+du\s+jour\s*[:\-]?\s*([^\n]+)'
    nights = extract_text(email_text, [nights_pattern])
    room = extract_text(email_text, [room_pattern])
    tarif_jour = extract_text(email_text, [tarif_jour_pattern])
    
    details_parts = []
    if nights:
        details_parts.append(f"{nights} nuit(s)")
    if room:
        details_parts.append(f"en {room.strip()}")
    if tarif_jour:
        details_parts.append(f"- {tarif_jour.strip()}")
    result['sejour_details'] = " ".join(details_parts) if details_parts else None
    
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
    
    cb_patterns = [
        r'Type\s+de\s+carte\s*[:\-]?\s*(\w+)\s*Numéro\s+de\s+carte\s*[:\-]?\s*([\d\*]+)',
    ]
    cb_match = re.search(cb_patterns[0], email_text, re.IGNORECASE | re.DOTALL)
    if cb_match:
        result['carte_bancaire'] = f"{cb_match.group(1)} {cb_match.group(2)}"
    
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

def parse_airbnb(email_text):
    """Parse Airbnb reservation emails."""
    result = {
        'platform': 'Airbnb',
        'tarif': None,
        'vad': None,
        'commission': None,
        'sejour_details': None,
        'dates_arrivee': None,
        'dates_depart': None,
        'carte_bancaire': None,
        'guest_name': None,
        'reservation_id': None,
        'raw_tarif_line': None,
        'raw_vad_line': None
    }
    
    tarif_patterns = [
        r'(?:Total|Montant\s+total)\s*[:\-]?\s*([\d\s,\.]+)\s*(?:EUR|€)',
        r'(?:Prix\s+par\s+nuit|Nightly\s+rate)\s*[:\-]?\s*([\d\s,\.]+)',
    ]
    
    payout_patterns = [
        r'(?:Versement|Payout|Vous\s+recevrez)\s*[:\-]?\s*([\d\s,\.]+)\s*(?:EUR|€)',
        r'(?:Host\s+)?(?:Payout|Earnings)\s*[:\-]?\s*([\d\s,\.]+)',
    ]
    
    service_fee_patterns = [
        r'(?:Frais\s+de\s+service|Service\s+fee|Airbnb\s+fee)\s*[:\-]?\s*([\d\s,\.]+)\s*(?:EUR|€)',
    ]
    
    result['tarif'] = extract_price(email_text, tarif_patterns)
    result['vad'] = extract_price(email_text, payout_patterns)
    
    service_fee = extract_price(email_text, service_fee_patterns)
    if result['tarif'] and result['vad']:
        result['commission'] = round(result['tarif'] - result['vad'], 2)
    elif result['tarif'] and service_fee:
        result['commission'] = service_fee
        result['vad'] = round(result['tarif'] - service_fee, 2)
    
    sejour_patterns = [
        r'(\d+)\s*(?:nuit|night)s?',
        r'(?:Logement|Listing|Property)\s*[:\-]?\s*([^\n]+)',
    ]
    nights = extract_text(email_text, [r'(\d+)\s*(?:nuit|night)s?'])
    if nights:
        result['sejour_details'] = f"{nights} nuit(s)"
    
    date_arrivee_patterns = [
        r'(?:Arriv[eé]e|Check[\-\s]?in)\s*[:\-]?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
        r'(\d{1,2}\s+(?:jan|f[eé]v|mar|avr|mai|juin|juil|ao[uû]|sep|oct|nov|d[eé]c)[a-z]*(?:\s+\d{2,4})?)\s*[\-–]',
    ]
    result['dates_arrivee'] = extract_text(email_text, date_arrivee_patterns)
    
    date_depart_patterns = [
        r'(?:D[eé]part|Check[\-\s]?out)\s*[:\-]?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
        r'[\-–]\s*(\d{1,2}\s+(?:jan|f[eé]v|mar|avr|mai|juin|juil|ao[uû]|sep|oct|nov|d[eé]c)[a-z]*(?:\s+\d{2,4})?)',
    ]
    result['dates_depart'] = extract_text(email_text, date_depart_patterns)
    
    guest_patterns = [
        r'(?:Voyageur|Guest|Hôte)\s*[:\-]?\s*([A-ZÀ-Ü][a-zà-ü]+(?:\s+[A-ZÀ-Ü]\.?)?)',
    ]
    result['guest_name'] = extract_text(email_text, guest_patterns)
    
    reservation_patterns = [
        r'(?:Code\s+de\s+confirmation|Confirmation\s+code)\s*[:\-]?\s*([A-Z0-9]+)',
        r'(?:R[eé]servation)\s*[:\-]?\s*([A-Z0-9]+)',
    ]
    result['reservation_id'] = extract_text(email_text, reservation_patterns)
    
    return result

PARSERS = {
    'weekendesk': parse_weekendesk,
    'booking': parse_booking,
    'expedia': parse_expedia,
    'originals': parse_originals,
    'airbnb': parse_airbnb,
}

def parse_email(email_text, platform=None):
    """Parse email based on detected or specified platform."""
    if platform is None:
        platform = detect_platform(email_text)
    
    parser = PARSERS.get(platform, parse_weekendesk)
    return parser(email_text)

def generate_summary(data, receptionist_name):
    """Generate the formatted summary for PMS."""
    today = datetime.now().strftime("%d/%m/%Y")
    platform = data.get('platform', 'OTA')
    
    lines = [platform]
    
    if data.get('tarif') is not None:
        lines.append(f"Tarif : {format_price(data['tarif'])}")
    else:
        lines.append("Tarif : Non trouvé")
    
    if data.get('vad') is not None:
        lines.append(f"VAD : {format_price(data['vad'])}")
    else:
        lines.append("VAD : Non trouvé")
    
    if data.get('commission') is not None:
        lines.append(f"Commission : {format_price(data['commission'])}")
    else:
        lines.append("Commission : Non calculable")
    
    lines.append(f"{receptionist_name} + {today}")
    lines.append("--")
    
    if data.get('guest_name'):
        lines.append(f"Client : {data['guest_name']}")
    
    if data.get('reservation_id'):
        lines.append(f"Réf : {data['reservation_id']}")
    
    if data.get('dates_arrivee') or data.get('dates_depart'):
        if data.get('dates_arrivee') and data.get('dates_depart'):
            lines.append(f"Du {data['dates_arrivee']} au {data['dates_depart']}")
        elif data.get('dates_arrivee'):
            lines.append(f"Arrivée : {data['dates_arrivee']}")
        elif data.get('dates_depart'):
            lines.append(f"Départ : {data['dates_depart']}")
    
    if data.get('sejour_details'):
        lines.append(data['sejour_details'])
    
    lines.append("--")
    
    if data.get('raw_tarif_line'):
        lines.append(data['raw_tarif_line'])
    elif data.get('tarif') is not None:
        lines.append(f"Prix client : {data['tarif']:.2f} EUR")
    
    if data.get('raw_vad_line'):
        lines.append(data['raw_vad_line'])
    elif data.get('vad') is not None:
        lines.append(f"Versement établissement : {data['vad']:.2f} EUR")
    
    if data.get('carte_bancaire'):
        lines.append("")
        lines.append("Carte Bancaire Virtuelle :")
        lines.append(data['carte_bancaire'])
    
    return "\n".join(lines)

def get_platform_list():
    """Return list of supported platforms for UI."""
    return [(pid, cfg['name']) for pid, cfg in OTA_PLATFORMS.items()]
