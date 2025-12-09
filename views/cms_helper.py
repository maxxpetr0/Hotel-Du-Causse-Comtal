import streamlit as st
from datetime import datetime
from cms_parser import process_pms_file, parse_csv_data, generate_markdown_table

def run():
    st.title("CMS Helper")
    st.markdown("Transformez les données PMS en tableau formaté pour le CMS")
    
    st.subheader("Import des données")
    
    upload_tab, paste_tab = st.tabs(["Importer un fichier", "Coller les données"])
    
    with upload_tab:
        uploaded_file = st.file_uploader(
            "Choisissez un fichier CSV du PMS",
            type=['csv'],
            help="Format attendu : fichier CSV avec séparateur point-virgule (;)"
        )
        
        if uploaded_file is not None:
            try:
                file_content = uploaded_file.getvalue().decode('utf-8-sig')
            except:
                file_content = uploaded_file.getvalue().decode('latin-1')
            
            st.session_state['cms_file_content'] = file_content
    
    with paste_tab:
        pasted_content = st.text_area(
            "Collez les données CSV ici",
            height=200,
            placeholder="Collez le contenu du fichier CSV (avec en-têtes)...",
            key="cms_paste_input"
        )
        
        if pasted_content.strip():
            st.session_state['cms_file_content'] = pasted_content
    
    separator = st.selectbox(
        "Séparateur CSV",
        [";", ",", "\t"],
        index=0,
        format_func=lambda x: {";" : "Point-virgule (;)", "," : "Virgule (,)", "\t" : "Tabulation"}[x]
    )
    
    process_button = st.button("Transformer les données", type="primary", use_container_width=True)
    
    if process_button:
        if 'cms_file_content' not in st.session_state or not st.session_state['cms_file_content']:
            st.error("Veuillez importer un fichier ou coller des données.")
        else:
            try:
                df, markdown_output = process_pms_file(
                    st.session_state['cms_file_content'], 
                    separator
                )
                
                st.session_state['cms_df'] = df
                st.session_state['cms_markdown'] = markdown_output
                st.session_state['cms_processed'] = True
                
            except Exception as e:
                st.error(f"Erreur lors du traitement : {str(e)}")
                st.session_state['cms_processed'] = False
    
    if st.session_state.get('cms_processed'):
        st.markdown("---")
        st.subheader("Résultat")
        
        df = st.session_state.get('cms_df')
        if df is not None:
            st.write(f"**{len(df)} enregistrements traités**")
            
            with st.expander("Aperçu des données transformées", expanded=True):
                st.dataframe(df, use_container_width=True)
            
            st.subheader("Tableau à copier-coller")
            
            markdown_output = st.session_state.get('cms_markdown', '')
            
            st.text_area(
                "Sortie formatée",
                value=markdown_output,
                height=300,
                key="cms_output"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.download_button(
                    label="Télécharger (.txt)",
                    data=markdown_output,
                    file_name=f"cms_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            
            with col2:
                csv_output = df.to_csv(index=False, sep=';')
                st.download_button(
                    label="Télécharger (.csv)",
                    data=csv_output,
                    file_name=f"cms_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
    
    st.markdown("---")
    
    with st.expander("Format d'entrée attendu"):
        st.markdown("""
        **Colonnes requises :**
        - Statut, Civilité, Nom, Chambre, Téléphone, Email, Pays, Code postal, 
        - Adresse, Ville, Nb personnes, Référence, Faite par, Date arrivée, 
        - Heure d'arrivée, Date départ, Heure de départ, Commentaire, CA TTC, Paiements, Solde
        
        **Règles de transformation :**
        1. Valeurs vides remplacées par "_"
        2. Nom séparé en Nom (MAJUSCULES) et Prénom
        3. Email contenant "m.expediapartnercentral.com" remplacé par "EXPEDIA"
        """)
    
    with st.expander("Format de sortie"):
        st.markdown("""
        **Structure du tableau :**
        ```
        Date de checkin;Nom;Prénom;Mail;Plan Tarifaire;Champs Marketing;;
        ;;;;;Provenance;Groupe;Catégorie
        [Données ligne par ligne]
        ```
        """)
