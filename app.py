import streamlit as st
from views import ota_helper, cms_helper

st.set_page_config(
    page_title="Hôtel du Causse Comtal - Outils",
    page_icon="🏰",
    layout="wide"
)

if 'current_app' not in st.session_state:
    st.session_state.current_app = None

def show_home():
    st.title("🏰 Hôtel du Causse Comtal")
    st.subheader("Outils de gestion")
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
        """, unsafe_allow_html=True)
        
        if st.button("Ouvrir OTA Helper", key="btn_ota", use_container_width=True, type="primary"):
            st.session_state.current_app = 'ota'
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
        """, unsafe_allow_html=True)
        
        if st.button("Ouvrir CMS Helper", key="btn_cms", use_container_width=True, type="primary"):
            st.session_state.current_app = 'cms'
            st.rerun()
        
        st.markdown("""
        **Fonctionnalités :**
        - Import de fichiers CSV du PMS
        - Séparation Nom/Prénom automatique
        - Détection emails Expedia
        - Export tableau double en-tête
        """)
    
    st.markdown("---")
    st.caption("Hôtel du Causse Comtal - Outils de gestion hôtelière")

def show_app_with_nav(app_name, app_func):
    col_nav, col_spacer = st.columns([1, 5])
    with col_nav:
        if st.button("← Accueil", key="back_home"):
            st.session_state.current_app = None
            for key in list(st.session_state.keys()):
                if key not in ['current_app']:
                    del st.session_state[key]
            st.rerun()
    
    st.markdown("---")
    app_func()

if st.session_state.current_app == 'ota':
    show_app_with_nav('ota', ota_helper.run)
elif st.session_state.current_app == 'cms':
    show_app_with_nav('cms', cms_helper.run)
else:
    show_home()
