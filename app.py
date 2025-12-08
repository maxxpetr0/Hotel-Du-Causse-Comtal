import streamlit as st
import re
from datetime import datetime

st.set_page_config(
    page_title="OTA Helper",
    page_icon="🏨",
    layout="wide"
)

st.title("🏨 OTA Helper")
st.markdown("Transformez vos emails de réservation en résumés standardisés pour le PMS")

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
    
    return float(price_str)

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

def parse_email(email_text):
    """Parse the hotel reservation email and extract relevant data."""
    result = {
        'tarif': None,
        'vad': None,
        'commission': None,
        'sejour_details': None,
        'dates_arrivee': None,
        'dates_depart': None,
        'carte_bancaire': None,
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
    
    tarif_line_patterns = [
        r'(Prix\s+[eé]tablissement\s+pay[eé]\s+par\s+le\s+client\s*[:\-]?\s*[\d\s,\.]+\s*(?:EUR|€))',
    ]
    result['raw_tarif_line'] = extract_text(email_text, tarif_line_patterns)
    
    vad_line_patterns = [
        r'(Montant\s+pay[eé]\s+par\s+Weekendesk\s+[àa]\s+l[\'\u2019][eé]tablissement\s*(?:\(TTC\))?\s*[:\-]?\s*[\d\s,\.]+\s*(?:EUR|€))',
    ]
    result['raw_vad_line'] = extract_text(email_text, vad_line_patterns)
    
    return result

def format_price(price):
    """Format price with French locale (comma as decimal separator)."""
    if price is None:
        return "Non trouvé"
    return f"{price:,.2f}".replace(',', ' ').replace('.', ',').replace(' ', ' ') + " €"

def generate_summary(data, receptionist_name):
    """Generate the formatted summary for PMS."""
    today = datetime.now().strftime("%d/%m/%Y")
    
    lines = ["Weekendesk"]
    
    if data['tarif'] is not None:
        lines.append(f"Tarif : {format_price(data['tarif'])}")
    else:
        lines.append("Tarif : Non trouvé")
    
    if data['vad'] is not None:
        lines.append(f"VAD : {format_price(data['vad'])}")
    else:
        lines.append("VAD : Non trouvé")
    
    if data['commission'] is not None:
        lines.append(f"Commission : {format_price(data['commission'])}")
    else:
        lines.append("Commission : Non calculable")
    
    lines.append(f"{receptionist_name} + {today}")
    lines.append("--")
    
    dates_str = ""
    if data['dates_arrivee'] or data['dates_depart']:
        if data['dates_arrivee'] and data['dates_depart']:
            dates_str = f"Du {data['dates_arrivee']} au {data['dates_depart']}"
        elif data['dates_arrivee']:
            dates_str = f"Arrivée : {data['dates_arrivee']}"
        elif data['dates_depart']:
            dates_str = f"Départ : {data['dates_depart']}"
        lines.append(dates_str)
    
    if data['sejour_details']:
        lines.append(data['sejour_details'])
    
    lines.append("--")
    
    if data['raw_tarif_line']:
        lines.append(data['raw_tarif_line'])
    elif data['tarif'] is not None:
        lines.append(f"Prix établissement payé par le client : {data['tarif']:.2f} EUR")
    
    if data['raw_vad_line']:
        lines.append(data['raw_vad_line'])
    elif data['vad'] is not None:
        lines.append(f"Montant payé par Weekendesk à l'établissement (TTC) : {data['vad']:.2f} EUR")
    
    if data['carte_bancaire']:
        lines.append("")
        lines.append("Carte Bancaire Virtuelle :")
        lines.append(data['carte_bancaire'])
    
    return "\n".join(lines)

col1, col2 = st.columns(2)

with col1:
    st.subheader("📧 Email de réservation")
    email_input = st.text_area(
        "Collez le contenu brut du mail ici",
        height=400,
        placeholder="Collez ici le contenu de l'email de réservation Weekendesk..."
    )
    
    receptionist_name = st.text_input(
        "👤 Nom du Réceptionniste",
        placeholder="Entrez votre nom"
    )
    
    today_display = datetime.now().strftime("%d/%m/%Y")
    st.info(f"📅 Date du jour : **{today_display}** (automatique)")
    
    generate_button = st.button("🔄 Générer le résumé", type="primary", use_container_width=True)

with col2:
    st.subheader("📋 Résumé formaté")
    
    if generate_button:
        if not email_input.strip():
            st.error("⚠️ Veuillez coller le contenu de l'email.")
        elif not receptionist_name.strip():
            st.error("⚠️ Veuillez entrer votre nom.")
        else:
            data = parse_email(email_input)
            summary = generate_summary(data, receptionist_name.strip())
            
            st.session_state['summary'] = summary
            st.session_state['data'] = data
    
    if 'summary' in st.session_state:
        st.text_area(
            "Résultat",
            value=st.session_state['summary'],
            height=400,
            key="summary_output"
        )
        
        st.code(st.session_state['summary'], language=None)
        
        if st.button("📋 Copier le résumé", use_container_width=True):
            st.toast("Sélectionnez le texte ci-dessus et utilisez Ctrl+C pour copier")
        
        with st.expander("🔍 Données extraites (debug)"):
            data = st.session_state.get('data', {})
            st.write(f"**Tarif trouvé :** {data.get('tarif')}")
            st.write(f"**VAD trouvée :** {data.get('vad')}")
            st.write(f"**Commission calculée :** {data.get('commission')}")
            st.write(f"**Date d'arrivée :** {data.get('dates_arrivee')}")
            st.write(f"**Date de départ :** {data.get('dates_depart')}")
            st.write(f"**Détails séjour :** {data.get('sejour_details')}")
            st.write(f"**Carte bancaire :** {data.get('carte_bancaire')}")
    else:
        st.info("Le résumé apparaîtra ici après avoir cliqué sur 'Générer le résumé'")

st.markdown("---")
st.markdown("*OTA Helper - Outil de formatage des réservations pour PMS*")
