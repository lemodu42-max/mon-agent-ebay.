import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="Mon agent eBay", page_icon="🛍️", layout="wide")

REQUIRED = {
    "sku", "title", "supplier", "source_type", "supplier_cost",
    "shipping_cost", "suggested_price", "ebay_fee_rate",
    "payment_fee_rate", "other_cost", "stock", "delivery_days",
    "wholesale_agreement"
}

def truthy(value):
    return str(value).strip().lower() in {"1", "true", "yes", "oui", "vrai"}

def analyze(df, min_profit, min_margin):
    df = df.copy()
    missing = REQUIRED - set(df.columns)
    if missing:
        raise ValueError("Colonnes manquantes : " + ", ".join(sorted(missing)))
    numeric = [
        "supplier_cost", "shipping_cost", "suggested_price",
        "ebay_fee_rate", "payment_fee_rate", "other_cost", "stock", "delivery_days"
    ]
    for col in numeric:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    if df[numeric].isna().any().any():
        raise ValueError("Certaines colonnes numériques contiennent des valeurs vides ou invalides.")
    df["wholesale_agreement"] = df["wholesale_agreement"].map(truthy)
    df["estimated_fees"] = df["suggested_price"] * (
        df["ebay_fee_rate"] + df["payment_fee_rate"]
    )
    df["estimated_profit"] = (
        df["suggested_price"] - df["supplier_cost"] - df["shipping_cost"]
        - df["estimated_fees"] - df["other_cost"]
    )
    df["margin_rate_pct"] = (
        df["estimated_profit"] / df["suggested_price"] * 100
    ).where(df["suggested_price"] > 0, 0)
    df["policy_check"] = (
        df["source_type"].astype(str).str.lower().eq("wholesaler")
        & df["wholesale_agreement"] & (df["stock"] > 0) & (df["delivery_days"] > 0)
    )
    df["candidate"] = (
        df["policy_check"] & (df["estimated_profit"] >= min_profit)
        & (df["margin_rate_pct"] >= min_margin)
    )
    df["decision"] = df["candidate"].map({
        True: "À contrôler avant toute annonce",
        False: "Écarté : critères non remplis"
    })
    return df.sort_values(["candidate", "estimated_profit"], ascending=[False, False])

def template():
    return pd.DataFrame([{
        "sku": "EX-001", "title": "Exemple accessoire maison",
        "supplier": "Grossiste à confirmer", "source_type": "wholesaler",
        "supplier_cost": 9.0, "shipping_cost": 3.0, "suggested_price": 25.0,
        "ebay_fee_rate": 0.13, "payment_fee_rate": 0.0, "other_cost": 1.0,
        "stock": 20, "delivery_days": 4, "wholesale_agreement": "oui"
    }])

st.title("🛍️ Mon agent eBay")
st.caption("Tableau de bord de préparation et de contrôle de produits — accessible depuis Android.")
st.warning(
    "Mode sécurisé de départ : cette application analyse les données importées. "
    "Elle ne publie aucune annonce, ne passe aucune commande et ne modifie aucun stock."
)

with st.sidebar:
    st.header("Paramètres de rentabilité")
    min_profit = st.number_input("Bénéfice minimum estimé (€)", min_value=0.0, value=5.0, step=1.0)
    min_margin = st.number_input("Marge minimum (%)", min_value=0.0, value=20.0, step=1.0)

pages = st.tabs(["Vue d'ensemble", "Analyse produits", "Préparer une annonce", "Suivi commandes", "Configuration"])

with pages[0]:
    st.subheader("État du projet")
    a, b, c = st.columns(3)
    a.metric("Analyse de catalogue", "Disponible")
    b.metric("Connexion eBay", "À configurer")
    c.metric("Fournisseurs", "À connecter")
    st.markdown("""
    **Modules prévus dans le projet**
    - Recherche de tendances eBay et étude des ventes.
    - Comparaison de fournisseurs grossistes et contrôle des accords.
    - Calcul des coûts, frais et marges.
    - Préparation des brouillons d'annonces.
    - Synchronisation des stocks et suivi des commandes, après connexion autorisée.
    - Alertes en cas de rupture, retard ou marge insuffisante.
    """)
    st.info("Les modules marqués « à configurer » nécessitent des accès officiels et des tests avant toute automatisation.")

with pages[1]:
    st.subheader("Analyser un catalogue CSV")
    sample = template()
    st.download_button("Télécharger le modèle CSV", sample.to_csv(index=False).encode("utf-8"),
                       "modele_produits.csv", "text/csv")
    uploaded = st.file_uploader("Importer ton fichier CSV", type=["csv"])
    if uploaded:
        try:
            result = analyze(pd.read_csv(uploaded), min_profit, min_margin)
            x, y, z = st.columns(3)
            x.metric("Produits analysés", len(result))
            y.metric("Produits à contrôler", int(result["candidate"].sum()))
            z.metric("Bénéfice moyen estimé", f"{result['estimated_profit'].mean():.2f} €")
            st.dataframe(result, use_container_width=True, hide_index=True)
            st.download_button("Télécharger les résultats", result.to_csv(index=False).encode("utf-8"),
                               "resultats_analyse.csv", "text/csv")
        except Exception as e:
            st.error(str(e))
    else:
        st.write("Télécharge le modèle, remplis-le avec les données réelles de tes fournisseurs, puis importe-le.")
        st.dataframe(sample, use_container_width=True, hide_index=True)

with pages[2]:
    st.subheader("Préparer une annonce (brouillon)")
    st.caption("Cette page ne publie rien sur eBay.")
    title = st.text_input("Titre du produit")
    description = st.text_area("Description")
    price = st.number_input("Prix de vente (€)", min_value=0.0, step=0.5)
    quantity = st.number_input("Quantité", min_value=0, step=1)
    if st.button("Générer le brouillon"):
        if not title.strip() or not description.strip() or price <= 0:
            st.error("Renseigne au minimum le titre, la description et un prix supérieur à zéro.")
        else:
            draft = f"TITRE: {title}\nPRIX: {price:.2f} EUR\nQUANTITÉ: {quantity}\n\nDESCRIPTION:\n{description}\n"
            st.code(draft)
            st.download_button("Télécharger le brouillon TXT", draft, "brouillon_annonce.txt", "text/plain")

with pages[3]:
    st.subheader("Suivi des commandes")
    st.info("Le suivi automatique sera activé après connexion à l'API eBay. Pour l'instant, aucune commande n'est lue ni modifiée.")
    st.write("Tu pourras ensuite afficher le numéro de commande, le statut de paiement, l'expédition et le suivi.")

with pages[4]:
    st.subheader("Connexions et sécurité")
    st.markdown("""
    **À fournir/configurer plus tard :**
    1. Compte développeur eBay et application API (OAuth).
    2. Autorisations eBay adaptées aux annonces, inventaires et commandes.
    3. Fournisseurs grossistes ayant accepté par écrit le dropshipping.
    4. Politiques eBay de livraison, paiement et retours.
    5. Secrets stockés dans les variables d'environnement du serveur, jamais dans GitHub.
    """)
    st.error("Ne saisis jamais ici ton mot de passe eBay, un code SMS ou une clé API. Ne les publie pas dans GitHub.")
