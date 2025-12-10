import streamlit as st
from views import ota_helper, cms_helper, backoffice
from auth import init_users_table, verify_user, create_user, user_exists
from activity_log import init_activity_log_table, log_activity

st.set_page_config(page_title="Hôtel du Causse Comtal - Outils",
                   page_icon="🏰",
                   layout="wide")

init_users_table()
init_activity_log_table()

if 'current_app' not in st.session_state:
    st.session_state.current_app = None
if 'user' not in st.session_state:
    st.session_state.user = None


def show_login():
    st.title("🏰 Hôtel du Causse Comtal")
    st.subheader("Connexion")
    
    if not user_exists():
        st.info("Premier accès : créez le compte administrateur.")
        with st.form("first_admin_form"):
            username = st.text_input("Nom d'utilisateur")
            password = st.text_input("Mot de passe", type="password")
            password_confirm = st.text_input("Confirmer le mot de passe", type="password")
            
            submitted = st.form_submit_button("Créer le compte administrateur", type="primary")
            
            if submitted:
                if not username or not password:
                    st.error("Veuillez remplir tous les champs.")
                elif password != password_confirm:
                    st.error("Les mots de passe ne correspondent pas.")
                elif len(password) < 4:
                    st.error("Le mot de passe doit contenir au moins 4 caractères.")
                else:
                    result = create_user(username, password, is_admin=True)
                    if result:
                        st.success("Compte administrateur créé ! Vous pouvez maintenant vous connecter.")
                        st.rerun()
                    else:
                        st.error("Erreur lors de la création du compte.")
    else:
        with st.form("login_form"):
            username = st.text_input("Nom d'utilisateur")
            password = st.text_input("Mot de passe", type="password")
            
            submitted = st.form_submit_button("Se connecter", type="primary", use_container_width=True)
            
            if submitted:
                if not username or not password:
                    st.error("Veuillez remplir tous les champs.")
                else:
                    user = verify_user(username, password)
                    if user:
                        st.session_state.user = user
                        log_activity(user['id'], user['username'], 'login')
                        st.rerun()
                    else:
                        st.error("Identifiants incorrects.")
    
    st.markdown("---")
    st.caption("Hôtel du Causse Comtal - Socito Industries - Tous droits réservés © 2025")


def show_home():
    col_header, col_user = st.columns([4, 1])
    with col_header:
        st.title("🏰 Hôtel du Causse Comtal")
        st.subheader("Outils de gestion")
    with col_user:
        st.markdown(f"**{st.session_state.user['username']}**")
        if st.button("Déconnexion", key="logout_btn"):
            log_activity(st.session_state.user['id'], st.session_state.user['username'], 'logout')
            st.session_state.user = None
            st.session_state.current_app = None
            st.rerun()
    
    st.markdown("Choisissez l'outil que vous souhaitez utiliser :")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 30px;
            border-radius: 15px;
            text-align: center;
            color: white;
            margin: 10px 0;
        ">
            <h2 style="margin: 0; color: white;">📧 OTA Helper</h2>
            <p style="margin: 15px 0; opacity: 0.9;">
                Transformez vos emails de réservation OTA en résumés standardisés pour le PMS
            </p>
        </div>
        """,
                    unsafe_allow_html=True)

        if st.button("Ouvrir OTA Helper",
                     key="btn_ota",
                     use_container_width=True,
                     type="primary"):
            st.session_state.current_app = 'ota'
            log_activity(st.session_state.user['id'], st.session_state.user['username'], 'ota_helper_open')
            st.rerun()

        st.markdown("""
        **Fonctionnalités :**
        - Détection automatique de la plateforme
        - Extraction des tarifs, VAD, commissions
        - Templates adaptés par OTA
        - Weekendesk, Expedia, Booking, Airbnb...
        """)

    with col2:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            padding: 30px;
            border-radius: 15px;
            text-align: center;
            color: white;
            margin: 10px 0;
        ">
            <h2 style="margin: 0; color: white;">📊 CMS Helper</h2>
            <p style="margin: 15px 0; opacity: 0.9;">
                Transformez les exports PMS en tableau formaté pour le CMS marketing
            </p>
        </div>
        """,
                    unsafe_allow_html=True)

        if st.button("Ouvrir CMS Helper",
                     key="btn_cms",
                     use_container_width=True,
                     type="primary"):
            st.session_state.current_app = 'cms'
            log_activity(st.session_state.user['id'], st.session_state.user['username'], 'cms_helper_open')
            st.rerun()

        st.markdown("""
        **Fonctionnalités :**
        - Import de fichiers CSV du PMS
        - Séparation Nom/Prénom automatique
        - Détection emails Expedia
        - Export tableau double en-tête
        """)

    if st.session_state.user.get('is_admin', False):
        st.markdown("---")
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
            padding: 30px;
            border-radius: 15px;
            text-align: center;
            color: white;
            margin: 10px 0;
        ">
            <h2 style="margin: 0; color: white;">⚙️ Back Office</h2>
            <p style="margin: 15px 0; opacity: 0.9;">
                Gérez les utilisateurs et les accès à l'application
            </p>
        </div>
        """,
                    unsafe_allow_html=True)

        if st.button("Ouvrir Back Office",
                     key="btn_backoffice",
                     use_container_width=True,
                     type="secondary"):
            st.session_state.current_app = 'backoffice'
            log_activity(st.session_state.user['id'], st.session_state.user['username'], 'backoffice_open')
            st.rerun()

    st.markdown("---")
    st.caption("Hôtel du Causse Comtal - Socito Industries - Tous droits réservés © 2025")


def show_app_with_nav(app_name, app_func):
    col_nav, col_spacer, col_user = st.columns([1, 4, 1])
    with col_nav:
        if st.button("← Accueil", key="back_home"):
            st.session_state.current_app = None
            for key in list(st.session_state.keys()):
                if key not in ['current_app', 'user']:
                    del st.session_state[key]
            st.rerun()
    with col_user:
        st.markdown(f"**{st.session_state.user['username']}**")
        if st.button("Déconnexion", key="logout_nav"):
            log_activity(st.session_state.user['id'], st.session_state.user['username'], 'logout')
            st.session_state.user = None
            st.session_state.current_app = None
            st.rerun()

    st.markdown("---")
    app_func()


if st.session_state.user is None:
    show_login()
elif st.session_state.current_app == 'ota':
    show_app_with_nav('ota', ota_helper.run)
elif st.session_state.current_app == 'cms':
    show_app_with_nav('cms', cms_helper.run)
elif st.session_state.current_app == 'backoffice':
    show_app_with_nav('backoffice', backoffice.run)
else:
    show_home()
