# Hôtel du Causse Comtal - Outils de Gestion

Application Streamlit multi-outils pour l'Hôtel du Causse Comtal.

## Outils Disponibles

### 1. OTA Helper
Transformation des emails de réservation OTA en résumés standardisés pour le PMS.

**Fonctionnalités :**
- Détection automatique de la plateforme OTA (Weekendesk, Expedia, Keytel, Smartbox, Réservation Directe)
- Extraction automatique des données : tarif, VAD/Payline, dates de séjour, type de chambre
- Calcul automatique de la commission
- Templates de sortie adaptés à chaque plateforme
- Détection carte virtuelle Expedia avec logique de paiement conditionnelle
- Export en fichier texte téléchargeable

### 2. CMS Helper
Transformation des exports PMS en tableau formaté pour le CMS marketing.

**Fonctionnalités :**
- Import de fichiers CSV du PMS
- Collage direct des données CSV
- Séparation automatique Nom/Prénom (NOM en majuscules)
- Détection et remplacement des emails Expedia par "EXPEDIA"
- Génération de tableau avec double en-tête pour le CMS
- Export en TXT (format marketing) et CSV (tableur)

### 3. Back Office (Admin)
Gestion des utilisateurs et des accès.

**Fonctionnalités :**
- Création de nouveaux utilisateurs
- Modification des mots de passe
- Gestion des droits administrateur
- Suppression d'utilisateurs
- Journal d'activité (logs de toutes les actions)

## Authentification

L'application est protégée par un système d'authentification :
- Premier accès : création du compte administrateur
- Connexion obligatoire pour accéder aux outils
- Mots de passe hashés (SHA256 + salt)
- Session Streamlit pour la gestion des connexions
- Back Office réservé aux administrateurs

## Structure du Projet

```
/
├── app.py                    # Application principale avec navigation et auth
├── auth.py                   # Module d'authentification
├── views/
│   ├── __init__.py
│   ├── ota_helper.py        # Page OTA Helper
│   ├── cms_helper.py        # Page CMS Helper
│   └── backoffice.py        # Page Back Office (admin)
├── parsers.py                # Module de parsing des emails OTA
├── cms_parser.py             # Module de parsing des données PMS
├── templates.py              # Templates de sortie par plateforme OTA
├── database.py               # Module PostgreSQL pour l'historique
├── activity_log.py           # Module de journal d'activité
├── .streamlit/
│   └── config.toml          # Configuration Streamlit
└── replit.md                # Documentation
```

## Lancement

```bash
streamlit run app.py --server.port 5000
```

## Plateformes OTA Supportées

### Weekendesk
```
Weekendesk
[Type d'hébergement]
Total : XXX.XX EUR
Payline : XXX.XX EUR
Commission : XX.XX EUR
[Récapitulatif des activités par date avec bullets]
Encaisser TDS + Extras
[Réceptionniste], le [Date du jour]
```

### Expedia / Egencia
- Carte virtuelle Expedia : `Faire Payline [PRIX] + Encaisser TDS et Extras`
- Autre carte : `Encaisser la totalité`

### Keytel
```
KEYTEL
[TYPE_CHAMBRE]
Total [PRIX_TOTAL] € PDJ Inclus
Paiement Keytel
Encaisser TDS + Extras
[Réceptionniste], le [Date du jour]
```

### Smartbox
```
Smartbox
[TYPE_HEBERGEMENT]
Prix total : [PRIX_CLIENT]
Prix hors commission : [PRIX_HORS_COMMISSION]
Commission : [COMMISSION]
[RECAPITULATIF]
Encaisser TDS + Extras
[Réceptionniste], le [Date du jour]
```

### Réservation Directe
Format pour les réservations directes avec garantie CB.

## CMS Helper - Règles de Transformation

1. Valeurs vides → remplacées par "_"
2. Colonne "Nom" (NOM Prénom) → séparée en Nom (majuscules) et Prénom
3. Email contenant "m.expediapartnercentral.com" → remplacé par "EXPEDIA"
4. Colonnes vides : Plan Tarifaire, Provenance, Groupe, Catégorie

**Format de sortie :**
```
Date de checkin;Nom;Prénom;Mail;Plan Tarifaire;Champs Marketing;;
;;;;;Provenance;Groupe;Catégorie
[Données ligne par ligne]
```

## Base de Données

PostgreSQL avec tables :
- `summaries` : historique des résumés OTA générés
- `users` : utilisateurs et authentification
- `activity_logs` : journal d'activité

## Journal d'Activité

Le journal d'activité enregistre automatiquement :
- Connexions et déconnexions
- Ouverture des outils (OTA Helper, CMS Helper, Back Office)
- Génération de résumés OTA
- Transformation de données CMS
- Création, modification et suppression d'utilisateurs

Accessible uniquement aux administrateurs dans le Back Office (onglet "Journal d'activité").
