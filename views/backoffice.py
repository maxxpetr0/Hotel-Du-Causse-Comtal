import streamlit as st
from auth import get_all_users, create_user, delete_user, update_user_password, toggle_admin, count_admins
from activity_log import log_activity, get_activity_logs, get_action_label

def run():
    st.title("Back Office - Gestion des Utilisateurs")
    
    if not st.session_state.get('user', {}).get('is_admin', False):
        st.error("Accès refusé. Vous devez être administrateur.")
        return
    
    tab_users, tab_logs = st.tabs(["Utilisateurs", "Journal d'activité"])
    
    with tab_users:
        show_users_management()
    
    with tab_logs:
        show_activity_logs()

def show_users_management():
    st.markdown("---")
    
    with st.expander("Créer un nouvel utilisateur", expanded=False):
        with st.form("create_user_form"):
            new_username = st.text_input("Nom d'utilisateur")
            new_password = st.text_input("Mot de passe", type="password")
            new_password_confirm = st.text_input("Confirmer le mot de passe", type="password")
            is_admin = st.checkbox("Administrateur")
            
            submitted = st.form_submit_button("Créer l'utilisateur", type="primary")
            
            if submitted:
                if not new_username or not new_password:
                    st.error("Veuillez remplir tous les champs.")
                elif new_password != new_password_confirm:
                    st.error("Les mots de passe ne correspondent pas.")
                elif len(new_password) < 4:
                    st.error("Le mot de passe doit contenir au moins 4 caractères.")
                else:
                    result = create_user(new_username, new_password, is_admin)
                    if result:
                        current_user = st.session_state.get('user', {})
                        log_activity(current_user.get('id'), current_user.get('username'), 'user_created', f"Utilisateur: {new_username}, Admin: {is_admin}")
                        st.success(f"Utilisateur '{new_username}' créé avec succès !")
                        st.rerun()
                    else:
                        st.error("Ce nom d'utilisateur existe déjà.")
    
    st.subheader("Utilisateurs existants")
    
    users = get_all_users()
    
    if not users:
        st.info("Aucun utilisateur enregistré.")
        return
    
    for user in users:
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
            
            with col1:
                admin_badge = " 👑" if user['is_admin'] else ""
                st.markdown(f"**{user['username']}**{admin_badge}")
                if user['last_login']:
                    st.caption(f"Dernière connexion : {user['last_login'].strftime('%d/%m/%Y %H:%M')}")
                else:
                    st.caption("Jamais connecté")
            
            with col2:
                if user['id'] != st.session_state.user['id']:
                    if st.button("Changer MDP", key=f"pwd_{user['id']}"):
                        st.session_state[f"edit_pwd_{user['id']}"] = True
            
            with col3:
                if user['id'] != st.session_state.user['id']:
                    admin_count = count_admins()
                    can_toggle = not (user['is_admin'] and admin_count <= 1)
                    
                    if can_toggle:
                        btn_text = "Retirer admin" if user['is_admin'] else "Rendre admin"
                        if st.button(btn_text, key=f"admin_{user['id']}"):
                            toggle_admin(user['id'])
                            current_user = st.session_state.get('user', {})
                            action = "retiré admin" if user['is_admin'] else "rendu admin"
                            log_activity(current_user.get('id'), current_user.get('username'), 'user_admin_toggled', f"Utilisateur: {user['username']} {action}")
                            st.rerun()
            
            with col4:
                if user['id'] != st.session_state.user['id']:
                    admin_count = count_admins()
                    can_delete = not (user['is_admin'] and admin_count <= 1)
                    
                    if can_delete:
                        if st.button("Supprimer", key=f"del_{user['id']}", type="secondary"):
                            st.session_state[f"confirm_del_{user['id']}"] = True
            
            if st.session_state.get(f"edit_pwd_{user['id']}", False):
                with st.form(f"pwd_form_{user['id']}"):
                    new_pwd = st.text_input("Nouveau mot de passe", type="password", key=f"newpwd_{user['id']}")
                    col_save, col_cancel = st.columns(2)
                    with col_save:
                        if st.form_submit_button("Enregistrer"):
                            if new_pwd and len(new_pwd) >= 4:
                                update_user_password(user['id'], new_pwd)
                                current_user = st.session_state.get('user', {})
                                log_activity(current_user.get('id'), current_user.get('username'), 'user_password_changed', f"Utilisateur: {user['username']}")
                                st.session_state[f"edit_pwd_{user['id']}"] = False
                                st.success("Mot de passe modifié !")
                                st.rerun()
                            else:
                                st.error("Mot de passe trop court (min 4 caractères)")
                    with col_cancel:
                        if st.form_submit_button("Annuler"):
                            st.session_state[f"edit_pwd_{user['id']}"] = False
                            st.rerun()
            
            if st.session_state.get(f"confirm_del_{user['id']}", False):
                st.warning(f"Êtes-vous sûr de vouloir supprimer '{user['username']}' ?")
                col_yes, col_no = st.columns(2)
                with col_yes:
                    if st.button("Oui, supprimer", key=f"yes_del_{user['id']}", type="primary"):
                        deleted_username = user['username']
                        delete_user(user['id'])
                        current_user = st.session_state.get('user', {})
                        log_activity(current_user.get('id'), current_user.get('username'), 'user_deleted', f"Utilisateur: {deleted_username}")
                        st.session_state[f"confirm_del_{user['id']}"] = False
                        st.rerun()
                with col_no:
                    if st.button("Non, annuler", key=f"no_del_{user['id']}"):
                        st.session_state[f"confirm_del_{user['id']}"] = False
                        st.rerun()
            
            st.markdown("---")

def show_activity_logs():
    st.subheader("Journal d'activité")
    
    logs = get_activity_logs(limit=200)
    
    if not logs:
        st.info("Aucune activité enregistrée.")
        return
    
    st.write(f"**{len(logs)} dernières activités**")
    
    for log in logs:
        col_time, col_user, col_action, col_details = st.columns([2, 2, 2, 3])
        
        with col_time:
            st.caption(log['created_at'].strftime('%d/%m/%Y %H:%M:%S'))
        
        with col_user:
            st.write(f"**{log['username'] or 'Système'}**")
        
        with col_action:
            action_label = get_action_label(log['action_type'])
            st.write(action_label)
        
        with col_details:
            if log['action_details']:
                st.caption(log['action_details'])
    
    st.markdown("---")
