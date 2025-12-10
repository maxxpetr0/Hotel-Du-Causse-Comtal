import streamlit as st
from datetime import datetime
from parsers import (
    parse_email, 
    generate_summary, 
    detect_platform, 
    get_platform_list,
    OTA_PLATFORMS
)
from database import init_db, save_summary
from activity_log import log_activity

def run():
    init_db()
    
    st.title("OTA Helper")
    st.markdown("Transformez vos emails de réservation en résumés standardisés pour le PMS")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Email de réservation")
        email_input = st.text_area(
            "Collez le contenu brut du mail ici",
            height=300,
            placeholder="Collez ici le contenu de l'email de réservation...",
            key="email_input"
        )
        
        platform_options = [("auto", "Détection automatique")] + [(pid, cfg['name']) for pid, cfg in OTA_PLATFORMS.items()]
        platform_labels = [label for _, label in platform_options]
        platform_ids = [pid for pid, _ in platform_options]
        
        selected_platform_label = st.selectbox(
            "Plateforme OTA",
            platform_labels,
            index=0
        )
        selected_platform = platform_ids[platform_labels.index(selected_platform_label)]
        
        receptionist_name = st.text_input(
            "Nom du Réceptionniste",
            placeholder="Entrez votre nom",
            key="receptionist_name"
        )
        
        today_display = datetime.now().strftime("%d/%m/%Y")
        st.info(f"Date du jour : **{today_display}** (automatique)")
        
        generate_button = st.button("Générer le résumé", type="primary", use_container_width=True)
    
    with col2:
        st.subheader("Résumé formaté")
        
        if generate_button:
            if not email_input.strip():
                st.error("Veuillez coller le contenu de l'email.")
            elif not receptionist_name.strip():
                st.error("Veuillez entrer votre nom.")
            else:
                if selected_platform == "auto":
                    detected = detect_platform(email_input)
                else:
                    detected = selected_platform
                
                st.session_state['detected_platform'] = OTA_PLATFORMS.get(detected, {}).get('name', detected)
                
                data = parse_email(email_input, detected)
                summary = generate_summary(data, receptionist_name.strip())
                
                try:
                    save_summary(data, summary, receptionist_name.strip(), email_input)
                    st.session_state['saved'] = True
                    current_user = st.session_state.get('user', {})
                    platform_name = OTA_PLATFORMS.get(detected, {}).get('name', detected)
                    log_activity(current_user.get('id'), current_user.get('username'), 'ota_helper_generate', f"Plateforme: {platform_name}")
                except Exception as e:
                    st.session_state['saved'] = False
                
                st.session_state['summary'] = summary
                st.session_state['data'] = data
        
        if 'summary' in st.session_state:
            if 'detected_platform' in st.session_state:
                st.success(f"Plateforme détectée : **{st.session_state['detected_platform']}**")
            
            if st.session_state.get('saved'):
                st.toast("Résumé sauvegardé")
            
            st.text_area(
                "Résultat",
                value=st.session_state['summary'],
                height=300,
                key="summary_output"
            )
            
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                st.download_button(
                    label="Télécharger (.txt)",
                    data=st.session_state['summary'],
                    file_name=f"resume_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            
            with col_btn2:
                if st.button("Copier", use_container_width=True):
                    st.toast("Sélectionnez le texte et utilisez Ctrl+C")
            
            with st.expander("Données extraites"):
                data = st.session_state.get('data', {})
                col_a, col_b = st.columns(2)
                with col_a:
                    st.write(f"**Plateforme :** {data.get('platform')}")
                    st.write(f"**Type hébergement :** {data.get('type_hebergement') or 'Non détecté'}")
                    st.write(f"**Tarif :** {data.get('tarif')}")
                    st.write(f"**VAD (Payline) :** {data.get('vad')}")
                    st.write(f"**Commission :** {data.get('commission')}")
                    st.write(f"**Réf. réservation :** {data.get('reservation_id')}")
                with col_b:
                    st.write(f"**Client :** {data.get('guest_name')}")
                    st.write(f"**Date d'arrivée :** {data.get('dates_arrivee')}")
                    st.write(f"**Date de départ :** {data.get('dates_depart')}")
                    st.write(f"**Détails séjour :** {data.get('sejour_details')}")
                    if data.get('is_virtual_card'):
                        st.write("**Carte virtuelle :** Oui (Expedia VirtualCard)")
                
                if data.get('recapitulatif'):
                    st.write("**Récapitulatif des activités :**")
                    st.code(data.get('recapitulatif'), language=None)
        else:
            st.info("Le résumé apparaîtra ici après avoir cliqué sur 'Générer le résumé'")
    
    st.markdown("---")
    platforms_supported = ", ".join([cfg['name'] for cfg in OTA_PLATFORMS.values()])
    st.caption(f"Plateformes supportées : {platforms_supported}")
