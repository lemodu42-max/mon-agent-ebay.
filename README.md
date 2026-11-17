# Mon agent eBay — version de départ

Application web Streamlit utilisable depuis un navigateur Android.

## Lancer localement
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Déployer sur Render
1. Envoyer tous les fichiers de ce dossier dans le dépôt GitHub `mon-agent-ebay`.
2. Sur Render, créer un nouveau service Web et connecter le dépôt.
3. Render détecte `render.yaml` ; vérifier les commandes puis lancer le déploiement.
4. Ouvrir l'URL fournie par Render depuis Android.

Le forfait gratuit peut s'endormir ou avoir des limites : il ne garantit pas une exécution continue 24 h/24.

## État réel des fonctions
- Disponible : import CSV, calcul estimatif des frais/marges, filtrage de candidats, export CSV et brouillon d'annonce.
- À développer/configurer : recherche automatique via sources autorisées, API eBay OAuth, fournisseurs, inventaire, commandes, alertes et publication.

Aucune annonce n'est publiée et aucune commande n'est passée par cette version.

## Sécurité et conformité
- Ne jamais déposer de mot de passe, jeton OAuth ou clé API dans GitHub.
- Utiliser les variables d'environnement/secrets du serveur.
- Obtenir l'accord du grossiste pour le dropshipping et vérifier délais, retours et stock.
- Ne pas acheter chez un détaillant après une vente eBay pour faire livrer le client.
- Tester en mode brouillon/sandbox avant d'activer une action réelle.
