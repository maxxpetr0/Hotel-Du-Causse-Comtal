# OTA Helper

Application Streamlit pour transformer les emails de réservation d'hôtel en résumés standardisés pour le PMS.

## Fonctionnalités

- Zone de texte pour coller le contenu brut de l'email de réservation
- Champ de saisie pour le nom du réceptionniste
- Date du jour insérée automatiquement
- **Détection automatique de la plateforme OTA** (Weekendesk, Expedia, Booking, Airbnb, The Originals, Réservation Directe)
- Extraction automatique des données : tarif, VAD/Payline, dates de séjour, type de chambre
- Calcul automatique de la commission (Tarif - VAD)
- **Templates de sortie adaptés à chaque plateforme OTA**
- **Extraction du récapitulatif des activités** (Weekendesk) avec dates et bullets
- **Détection carte virtuelle Expedia** avec logique de paiement conditionnelle
- Historique des résumés avec recherche (PostgreSQL)
- Export en fichier texte téléchargeable

## Structure du Projet

```
/
├── app.py                    # Application principale Streamlit
├── parsers.py                # Module de parsing des emails OTA
├── templates.py              # Templates de sortie par plateforme
├── database.py               # Module PostgreSQL pour l'historique
├── .streamlit/
│   └── config.toml          # Configuration Streamlit
└── replit.md                # Documentation
```

## Lancement

L'application se lance avec :
```bash
streamlit run app.py --server.port 5000
```

## Plateformes Supportées

### Weekendesk
Format de sortie :
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
Format avec logique conditionnelle :
- **Carte virtuelle Expedia** : `Faire Payline [PRIX] + Encaisser TDS et Extras`
- **Autre carte** : `Encaisser la totalité`

```
EXPEDIA
[Type de chambre]
[Phrase de paiement conditionnelle]
[Réceptionniste], le [Date du jour]
```

### Réservation Directe
```
Réservation Directe (Garantie CB)
[Type de chambre]
Encaisser la totalité ([PRIX]) + TDS + Extras
[Réceptionniste], le [Date du jour]
```

### Booking.com, The Originals, Airbnb
Formats adaptés à chaque plateforme avec les informations pertinentes.

## Format d'Entrée Supporté

L'application reconnaît automatiquement les emails des différentes OTAs :

### Weekendesk
- `Prix établissement payé par le client : XXX.XX EUR`
- `Montant payé par Weekendesk à l'établissement (TTC) : XXX.XX EUR`
- Récapitulatif des activités entre "externe à votre établissement" et "Prix établissement"

### Expedia
- `Prix total XXX.XX EUR`
- `Type de chambre : [Type]`
- `Nom du détenteur : Expedia VirtualCard` (détection carte virtuelle)

## Base de Données

PostgreSQL avec table `summaries` pour l'historique des résumés générés.
