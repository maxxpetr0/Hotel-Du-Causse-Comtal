from datetime import datetime

TEMPLATES = {
    'standard': {
        'name': 'Standard',
        'description': 'Format classique pour PMS'
    },
    'compact': {
        'name': 'Compact',
        'description': 'Format condensé sur moins de lignes'
    },
    'detailed': {
        'name': 'Détaillé',
        'description': 'Format complet avec toutes les informations'
    },
    'pms_simple': {
        'name': 'PMS Simple',
        'description': 'Format simplifié pour saisie rapide'
    }
}

def format_price(price):
    """Format price with French locale (comma as decimal separator)."""
    if price is None:
        return "Non trouvé"
    return f"{price:,.2f}".replace(',', ' ').replace('.', ',').replace(' ', ' ') + " €"

def generate_standard(data, receptionist_name):
    """Generate the standard summary format."""
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

def generate_compact(data, receptionist_name):
    """Generate compact summary format."""
    today = datetime.now().strftime("%d/%m/%Y")
    platform = data.get('platform', 'OTA')
    
    lines = []
    
    tarif_str = format_price(data.get('tarif')) if data.get('tarif') else "?"
    vad_str = format_price(data.get('vad')) if data.get('vad') else "?"
    comm_str = format_price(data.get('commission')) if data.get('commission') is not None else "?"
    
    lines.append(f"{platform} | {tarif_str} | VAD: {vad_str} | Com: {comm_str}")
    
    client = data.get('guest_name', '')
    ref = data.get('reservation_id', '')
    if client or ref:
        lines.append(f"{client} - Réf: {ref}" if client and ref else (client or f"Réf: {ref}"))
    
    dates = ""
    if data.get('dates_arrivee') and data.get('dates_depart'):
        dates = f"{data['dates_arrivee']} → {data['dates_depart']}"
    elif data.get('dates_arrivee'):
        dates = f"Arr: {data['dates_arrivee']}"
    
    sejour = data.get('sejour_details', '')
    if dates or sejour:
        lines.append(f"{dates} | {sejour}" if dates and sejour else (dates or sejour))
    
    lines.append(f"[{receptionist_name} - {today}]")
    
    return "\n".join(lines)

def generate_detailed(data, receptionist_name):
    """Generate detailed summary format with all information."""
    today = datetime.now().strftime("%d/%m/%Y")
    platform = data.get('platform', 'OTA')
    
    lines = [
        "═" * 40,
        f"RÉSERVATION {platform.upper()}",
        "═" * 40,
        ""
    ]
    
    lines.append("📊 TARIFICATION")
    lines.append("-" * 20)
    lines.append(f"  Tarif client    : {format_price(data.get('tarif'))}")
    lines.append(f"  VAD             : {format_price(data.get('vad'))}")
    lines.append(f"  Commission      : {format_price(data.get('commission')) if data.get('commission') is not None else 'Non calculable'}")
    lines.append("")
    
    lines.append("👤 CLIENT")
    lines.append("-" * 20)
    lines.append(f"  Nom             : {data.get('guest_name', 'Non renseigné')}")
    lines.append(f"  Réf. réservation: {data.get('reservation_id', 'Non renseignée')}")
    lines.append("")
    
    lines.append("📅 SÉJOUR")
    lines.append("-" * 20)
    lines.append(f"  Arrivée         : {data.get('dates_arrivee', 'Non renseignée')}")
    lines.append(f"  Départ          : {data.get('dates_depart', 'Non renseignée')}")
    lines.append(f"  Détails         : {data.get('sejour_details', 'Non renseignés')}")
    lines.append("")
    
    if data.get('carte_bancaire'):
        lines.append("💳 CARTE BANCAIRE")
        lines.append("-" * 20)
        lines.append(f"  {data['carte_bancaire']}")
        lines.append("")
    
    if data.get('raw_tarif_line') or data.get('raw_vad_line'):
        lines.append("📝 LIGNES ORIGINALES")
        lines.append("-" * 20)
        if data.get('raw_tarif_line'):
            lines.append(f"  {data['raw_tarif_line']}")
        if data.get('raw_vad_line'):
            lines.append(f"  {data['raw_vad_line']}")
        lines.append("")
    
    lines.append("═" * 40)
    lines.append(f"Traité par: {receptionist_name}")
    lines.append(f"Date: {today}")
    lines.append("═" * 40)
    
    return "\n".join(lines)

def generate_pms_simple(data, receptionist_name):
    """Generate simple PMS format for quick entry."""
    today = datetime.now().strftime("%d/%m/%Y")
    platform = data.get('platform', 'OTA')
    
    lines = []
    
    lines.append(f"[{platform}]")
    
    tarif = f"{data['tarif']:.2f}" if data.get('tarif') else "0.00"
    vad = f"{data['vad']:.2f}" if data.get('vad') else "0.00"
    comm = f"{data['commission']:.2f}" if data.get('commission') is not None else "0.00"
    
    lines.append(f"T:{tarif} V:{vad} C:{comm}")
    
    if data.get('guest_name'):
        lines.append(data['guest_name'])
    
    if data.get('reservation_id'):
        lines.append(f"#{data['reservation_id']}")
    
    if data.get('dates_arrivee') and data.get('dates_depart'):
        lines.append(f"{data['dates_arrivee']}-{data['dates_depart']}")
    
    lines.append(f"{receptionist_name}/{today}")
    
    return "\n".join(lines)

TEMPLATE_GENERATORS = {
    'standard': generate_standard,
    'compact': generate_compact,
    'detailed': generate_detailed,
    'pms_simple': generate_pms_simple
}

def generate_summary_with_template(data, receptionist_name, template_id='standard'):
    """Generate summary using specified template."""
    generator = TEMPLATE_GENERATORS.get(template_id, generate_standard)
    return generator(data, receptionist_name)

def get_template_list():
    """Return list of available templates for UI."""
    return [(tid, cfg['name'], cfg['description']) for tid, cfg in TEMPLATES.items()]
