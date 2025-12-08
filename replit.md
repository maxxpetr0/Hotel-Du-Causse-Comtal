# OTA Helper

Application Streamlit pour transformer les emails de réservation d'hôtel en résumés standardisés pour le PMS.

## Fonctionnalités

- Zone de texte pour coller le contenu brut de l'email de réservation
- Champ de saisie pour le nom du réceptionniste
- Date du jour insérée automatiquement
- Extraction automatique des données : tarif, VAD, dates de séjour, type de chambre
- Calcul automatique de la commission (Tarif - VAD) avec 2 décimales
- Formatage du résumé selon le template Weekendesk
- Affichage du résumé avec possibilité de copier
- Gestion des variations de format d'email avec regex flexibles

## Structure du Projet

```
/
├── app.py                    # Application principale Streamlit
├── .streamlit/
│   └── config.toml          # Configuration Streamlit
├── pyproject.toml           # Dépendances Python
└── replit.md                # Documentation
```

## Lancement

L'application se lance avec :
```bash
streamlit run app.py --server.port 5000
```

## Format d'Entrée Supporté (Weekendesk)

L'application reconnaît les formats suivants :
- `Prix établissement payé par le client : XXX.XX EUR`
- `Montant payé par Weekendesk à l'établissement (TTC) : XXX.XX EUR`
- `Séjour : X nuit(s) en [type de chambre]`
- Dates d'arrivée/départ
- Informations de carte bancaire virtuelle

## Format de Sortie

```
Weekendesk
Tarif : XXX,XX €
VAD : XXX,XX €
Commission : XX,XX €
[Nom Réceptionniste] + [Date du Jour]
--
[Dates du séjour]
[Détails du séjour]
--
[Lignes originales tarif/VAD]
[Infos Carte Bancaire si présentes]
```
