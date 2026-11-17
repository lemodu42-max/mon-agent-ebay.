# Agent eBay – démarrage

Prototype local en Python : analyse un catalogue fournisseur CSV, calcule une marge estimée et filtre les produits.
Il ne publie rien sur eBay et ne passe aucune commande automatiquement.

## Installation
Python 3.10+
```bash
python -m venv .venv
# Windows : .venv\\Scripts\\activate
# macOS/Linux : source .venv/bin/activate
pip install -r requirements.txt
```

## Utilisation
Copier `products_example.csv` vers `products.csv`, renseigner les prix/coûts réels, puis :
```bash
python agent.py --input products.csv --output candidates.csv --min-margin 5 --min-rate 20
```

`min-margin` = bénéfice estimé minimum en euros ; `min-rate` = taux de marge minimum en % du prix de vente.

Les frais eBay et frais de paiement sont des paramètres estimatifs : vérifie les frais applicables à ta catégorie et ton compte avant toute décision.
Avant toute publication, vérifie le droit de vendre le produit, le stock, les délais, les retours et l'accord écrit du fournisseur.
