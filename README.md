# Mon agent eBay — recherche d'annonces v2

Application Streamlit utilisable depuis un navigateur Android.

## Fonctions incluses
- Tableau de bord.
- Recherche d'annonces actives eBay via la Browse API (mot-clé, marketplace, prix affichés, frais de livraison visibles, lien).
- Import d'un catalogue fournisseur CSV et estimation de marge.
- Brouillon d'annonce exportable.

## Limites importantes
La Browse API retourne des annonces actives. Elle ne donne pas, à elle seule, le nombre de ventes réalisées ni la preuve qu'un article est demandé. L'API Marketplace Insights qui fournit des données d'articles vendus est en accès restreint et n'est pas ouverte aux nouveaux utilisateurs selon la documentation eBay consultée.
Cette version ne trouve pas automatiquement des fournisseurs grossistes, ne publie pas d'annonces et ne passe aucune commande.

## Déploiement Render
Build command:
```bash
pip install -r requirements.txt
```
Start command:
```bash
streamlit run app.py --server.port $PORT --server.address 0.0.0.0
```

Dans Render > service > Environment, ajouter :
- `EBAY_CLIENT_ID` : App ID / Client ID de l'application eBay
- `EBAY_CLIENT_SECRET` : Cert ID / Client Secret de l'application eBay

Ne jamais mettre ces secrets dans GitHub. Utiliser les identifiants Production pour les annonces eBay réelles ; Sandbox sert uniquement aux tests. Le code sélectionne l'environnement Sandbox uniquement si la case correspondante est cochée.

## Créer les identifiants
Créer une application dans le portail développeur eBay : https://developer.ebay.com/
La recherche Browse API utilise un Application access token via Client Credentials et le scope `https://api.ebay.com/oauth/api_scope`.

## Sécurité et conformité
- La recherche Browse API est une recherche d'annonces actives, pas un historique de ventes.
- Les prix affichés et frais de livraison peuvent changer.
- Vérifier la demande réelle, les frais eBay applicables, la TVA, les retours et le stock avant décision.
- N'utiliser que des fournisseurs grossistes qui acceptent explicitement le dropshipping.
- Ne pas acheter chez un détaillant après une vente eBay pour expédier au client.
- Aucune annonce n'est publiée et aucune commande n'est passée par cette version.
