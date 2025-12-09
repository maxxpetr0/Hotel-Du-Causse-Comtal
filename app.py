import streamlit as st
from datetime import datetime
from parsers import (
    parse_email, 
    generate_summary, 
    detect_platform, 
    get_platform_list,
    OTA_PLATFORMS
)
from database import (
    init_db, save_summary, register_user, 
    authenticate_user, get_user_count
)

st.set_page_config(
    page_title="OTA Helper",
    page_icon="🏨",
    layout="wide"
)

init_db()

if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'user' not in st.session_state:
    st.session_state['user'] = None

def show_login_page():
    """Display the login/registration page."""
    st.title("🏨 OTA Helper")
    st.markdown("### Connexion")
    
    user_count = get_user_count()
    
    tab_login, tab_register = st.tabs(["🔐 Connexion", "📝 Inscription"])
    
    with tab_login:
        with st.form("login_form"):
            username = st.text_input("Nom d'utilisateur")
            password = st.text_input("Mot de passe", type="password")
            submit = st.form_submit_button("Se connecter", use_container_width=True)
            
            if submit:
                if username and password:
                    user = authenticate_user(username, password)
                    if user:
                        st.session_state['authenticated'] = True
                        st.session_state['user'] = user
                        st.rerun()
                    else:
                        st.error("Identifiants incorrects")
                else:
                    st.warning("Veuillez remplir tous les champs")
    
    with tab_register:
        if user_count == 0:
            st.info("Aucun utilisateur. Inscrivez le premier compte administrateur.")
        
        with st.form("register_form"):
            new_username = st.text_input("Nom d'utilisateur", key="reg_user")
            new_password = st.text_input("Mot de passe", type="password", key="reg_pass")
            confirm_password = st.text_input("Confirmer le mot de passe", type="password", key="reg_confirm")
            register_btn = st.form_submit_button("S'inscrire", use_container_width=True)
            
            if register_btn:
                if not new_username or not new_password:
                    st.warning("Veuillez remplir tous les champs")
                elif len(new_password) < 4:
                    st.warning("Le mot de passe doit contenir au moins 4 caractères")
                elif new_password != confirm_password:
                    st.error("Les mots de passe ne correspondent pas")
                else:
                    if register_user(new_username, new_password):
                        st.success("Compte créé ! Vous pouvez maintenant vous connecter.")
                    else:
                        st.error("Ce nom d'utilisateur existe déjà")

def show_main_app():
    """Display the main application."""
    col_header, col_logout = st.columns([6, 1])
    with col_header:
        st.title("🏨 OTA Helper")
    with col_logout:
        st.write("")
        if st.button("🚪 Déconnexion"):
            st.session_state['authenticated'] = False
            st.session_state['user'] = None
            st.rerun()
    
    st.markdown("Transformez vos emails de réservation en résumés standardisés pour le PMS")
    st.caption(f"Connecté en tant que : **{st.session_state['user']['username']}**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📧 Email de réservation")
        email_input = st.text_area(
            "Collez le contenu brut du mail ici",
            height=300,
            placeholder="Collez ici le contenu de l'email de réservation...",
            key="email_input"
        )
        
        platform_options = [("auto", "🔍 Détection automatique")] + [(pid, f"📌 {cfg['name']}") for pid, cfg in OTA_PLATFORMS.items()]
        platform_labels = [label for _, label in platform_options]
        platform_ids = [pid for pid, _ in platform_options]
        
        selected_platform_label = st.selectbox(
            "🏢 Plateforme OTA",
            platform_labels,
            index=0
        )
        selected_platform = platform_ids[platform_labels.index(selected_platform_label)]
        
        receptionist_name = st.text_input(
            "👤 Nom du Réceptionniste",
            placeholder="Entrez votre nom",
            value=st.session_state['user']['username'],
            key="receptionist_name"
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
                except Exception as e:
                    st.session_state['saved'] = False
                
                st.session_state['summary'] = summary
                st.session_state['data'] = data
        
        if 'summary' in st.session_state:
            if 'detected_platform' in st.session_state:
                st.success(f"✅ Plateforme détectée : **{st.session_state['detected_platform']}**")
            
            if st.session_state.get('saved'):
                st.toast("💾 Résumé sauvegardé")
            
            st.text_area(
                "Résultat",
                value=st.session_state['summary'],
                height=300,
                key="summary_output"
            )
            
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                st.download_button(
                    label="📥 Télécharger (.txt)",
                    data=st.session_state['summary'],
                    file_name=f"resume_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            
            with col_btn2:
                if st.button("📋 Copier", use_container_width=True):
                    st.toast("Sélectionnez le texte et utilisez Ctrl+C")
            
            with st.expander("🔍 Données extraites"):
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
    st.markdown(f"*OTA Helper - Plateformes supportées : {platforms_supported}*")

if st.session_state['authenticated']:
    show_main_app()
else:
    show_login_page()
