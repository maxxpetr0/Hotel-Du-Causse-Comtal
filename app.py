import streamlit as st
from datetime import datetime
from parsers import (
    parse_email, 
    generate_summary, 
    detect_platform, 
    get_platform_list,
    OTA_PLATFORMS
)
from database import init_db, save_summary, get_summaries, get_summary_by_id, delete_summary, get_stats

st.set_page_config(
    page_title="OTA Helper",
    page_icon="🏨",
    layout="wide"
)

init_db()

st.title("🏨 OTA Helper")

tab1, tab2 = st.tabs(["📝 Nouveau résumé", "📚 Historique"])

with tab1:
    st.markdown("Transformez vos emails de réservation en résumés standardisés pour le PMS")
    
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
                st.toast("💾 Résumé sauvegardé dans l'historique")
            
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
                    st.write(f"**Tarif :** {data.get('tarif')}")
                    st.write(f"**VAD :** {data.get('vad')}")
                    st.write(f"**Commission :** {data.get('commission')}")
                    st.write(f"**Réf. réservation :** {data.get('reservation_id')}")
                with col_b:
                    st.write(f"**Client :** {data.get('guest_name')}")
                    st.write(f"**Date d'arrivée :** {data.get('dates_arrivee')}")
                    st.write(f"**Date de départ :** {data.get('dates_depart')}")
                    st.write(f"**Détails séjour :** {data.get('sejour_details')}")
        else:
            st.info("Le résumé apparaîtra ici après avoir cliqué sur 'Générer le résumé'")

with tab2:
    st.subheader("📚 Historique des résumés")
    
    col_search, col_filter = st.columns([3, 1])
    
    with col_search:
        search_query = st.text_input(
            "🔍 Rechercher",
            placeholder="Nom du client, référence, réceptionniste...",
            key="search_history"
        )
    
    with col_filter:
        platform_filter_options = ["all"] + list(OTA_PLATFORMS.keys())
        platform_filter_labels = ["Toutes les plateformes"] + [OTA_PLATFORMS[p]['name'] for p in OTA_PLATFORMS.keys()]
        platform_filter = st.selectbox(
            "Filtrer par plateforme",
            platform_filter_options,
            format_func=lambda x: platform_filter_labels[platform_filter_options.index(x)]
        )
    
    try:
        stats = get_stats()
        if stats:
            col_s1, col_s2, col_s3 = st.columns(3)
            with col_s1:
                st.metric("Total résumés", stats.get('total_summaries', 0))
            with col_s2:
                total_tarif = float(stats.get('total_tarif', 0) or 0)
                st.metric("Volume total", f"{total_tarif:,.2f} €".replace(',', ' '))
            with col_s3:
                total_commission = float(stats.get('total_commission', 0) or 0)
                st.metric("Total commissions", f"{total_commission:,.2f} €".replace(',', ' '))
    except Exception:
        pass
    
    try:
        summaries = get_summaries(
            limit=50,
            search_query=search_query if search_query else None,
            platform_filter=platform_filter if platform_filter != 'all' else None
        )
        
        if summaries:
            for summary in summaries:
                with st.expander(
                    f"📌 {summary['platform'] or 'N/A'} - {summary['guest_name'] or 'Client inconnu'} - {summary['created_at'].strftime('%d/%m/%Y %H:%M') if summary['created_at'] else 'N/A'}"
                ):
                    col_info, col_actions = st.columns([4, 1])
                    
                    with col_info:
                        st.write(f"**Réf :** {summary['reservation_id'] or 'N/A'}")
                        st.write(f"**Réceptionniste :** {summary['receptionist_name'] or 'N/A'}")
                        st.write(f"**Dates :** {summary['date_arrivee'] or '?'} → {summary['date_depart'] or '?'}")
                        
                        tarif = float(summary['tarif']) if summary['tarif'] else 0
                        vad = float(summary['vad']) if summary['vad'] else 0
                        commission = float(summary['commission']) if summary['commission'] else 0
                        st.write(f"**Tarif :** {tarif:.2f} € | **VAD :** {vad:.2f} € | **Commission :** {commission:.2f} €")
                    
                    with col_actions:
                        st.download_button(
                            label="📥",
                            data=summary['summary_text'] or '',
                            file_name=f"resume_{summary['id']}.txt",
                            mime="text/plain",
                            key=f"dl_{summary['id']}"
                        )
                        if st.button("🗑️", key=f"del_{summary['id']}"):
                            delete_summary(summary['id'])
                            st.rerun()
                    
                    st.code(summary['summary_text'] or '', language=None)
        else:
            st.info("Aucun résumé dans l'historique. Générez votre premier résumé !")
    except Exception as e:
        st.warning("Historique non disponible pour le moment.")

st.markdown("---")
platforms_supported = ", ".join([cfg['name'] for cfg in OTA_PLATFORMS.values()])
st.markdown(f"*OTA Helper - Plateformes supportées : {platforms_supported}*")
