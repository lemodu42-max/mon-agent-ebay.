import os
import base64
import requests
import pandas as pd
import streamlit as st

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

def ebay_application_token(client_id, client_secret, sandbox=False):
    if not client_id or not client_secret:
        raise ValueError("Ajoute EBAY_CLIENT_ID et EBAY_CLIENT_SECRET dans les variables d'environnement Render.")
    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    host = "https://api.sandbox.ebay.com" if sandbox else "https://api.ebay.com"
    response = requests.post(
        f"{host}/identity/v1/oauth2/token",
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={
            "grant_type": "client_credentials",
            "scope": "https://api.ebay.com/oauth/api_scope",
        },
        timeout=25,
    )
    response.raise_for_status()
    return response.json()["access_token"], host

def search_ebay_active_items(keyword, marketplace="EBAY_FR", limit=30, sandbox=False):
    client_id = os.getenv("EBAY_CLIENT_ID", "")
    client_secret = os.getenv("EBAY_CLIENT_SECRET", "")
    token, host = ebay_application_token(client_id, client_secret, sandbox)
    response = requests.get(
        f"{host}/buy/browse/v1/item_summary/search",
        headers={
            "Authorization": f"Bearer {token}",
            "X-EBAY-C-MARKETPLACE-ID": marketplace,
            "Accept-Language": "fr-FR",
        },
        params={"q": keyword, "limit": limit, "sort": "price"},
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    rows = []
    for item in payload.get("itemSummaries", []):
        price = item.get("price", {})
        shipping = (item.get("shippingOptions") or [{}])[0].get("shippingCost", {})
        rows.append({
            "Titre": item.get("title", ""),
            "Prix affiché": float(price.get("value", 0) or 0),
            "Devise": price.get("currency", "EUR"),
            "Livraison affichée": float(shipping.get("value", 0) or 0),
            "Vendeur": (item.get("seller") or {}).get("username", ""),
            "État": item.get("condition", ""),
            "Lien": item.get("itemWebUrl", ""),
        })
    return pd.DataFrame(rows), payload.get("total", 0)

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
    "Mode sécurisé : l'application analyse les catalogues et consulte les annonces actives eBay. "
    "Elle ne publie aucune annonce, ne passe aucune commande et ne modifie aucun stock."
)

with st.sidebar:
    st.header("Paramètres de rentabilité")
    min_profit = st.number_input("Bénéfice minimum estimé (€)", min_value=0.0, value=5.0, step=1.0)
    min_margin = st.number_input("Marge minimum (%)", min_value=0.0, value=20.0, step=1.0)

pages = st.tabs(["Vue d'ensemble", "Recherche eBay", "Analyse produits", "Préparer une annonce", "Suivi commandes", "Configuration"])

with pages[0]:
    st.subheader("État du projet")
    a, b, c = st.columns(3)
    a.metric("Analyse de catalogue", "Disponible")
    b.metric("Recherche annonces actives", "À configurer")
    c.metric("Connexion vendeur eBay", "Non connectée")
    st.markdown("""
    **Modules du projet**
    - Recherche d'annonces actives eBay par mot-clé.
    - Comparaison des prix affichés et des frais de livraison visibles.
    - Import d'un catalogue grossiste et calcul de marges.
    - Préparation de brouillons d'annonces.
    - Connexion vendeur, inventaire, commandes et publication : à développer séparément.
    """)
    st.info("Les prix des annonces actives ne prouvent pas qu'un produit se vend. Il faut des données de ventes réalisées pour mesurer la demande.")

with pages[1]:
    st.subheader("Rechercher des annonces actives sur eBay")
    st.write("Cette recherche consulte les annonces actuellement visibles sur la marketplace française.")
    keyword = st.text_input("Produit ou mot-clé", placeholder="ex. organiseur de tiroir")
    market = st.selectbox("Marketplace", ["EBAY_FR", "EBAY_DE", "EBAY_IT", "EBAY_ES", "EBAY_GB"])
    limit = st.slider("Nombre de résultats", 5, 50, 25, 5)
    sandbox = st.checkbox("Utiliser l'environnement Sandbox (tests)", value=False)
    if st.button("Rechercher sur eBay", type="primary"):
        if not keyword.strip():
            st.error("Saisis un mot-clé.")
        else:
            try:
                with st.spinner("Recherche des annonces eBay…"):
                    results, total = search_ebay_active_items(keyword.strip(), market, limit, sandbox)
                st.success(f"{len(results)} annonces récupérées. eBay indique {total} résultats au total.")
                if results.empty:
                    st.info("Aucune annonce trouvée pour ce mot-clé.")
                else:
                    st.dataframe(
                        results,
                        use_container_width=True,
                        hide_index=True,
                        column_config={"Lien": st.column_config.LinkColumn("Ouvrir sur eBay")}
                    )
                    st.download_button(
                        "Télécharger les résultats CSV",
                        results.to_csv(index=False).encode("utf-8"),
                        "recherche_ebay.csv",
                        "text/csv"
                    )
            except requests.HTTPError as e:
                detail = e.response.text[:1000] if e.response is not None else str(e)
                st.error(f"Erreur API eBay : {detail}")
            except Exception as e:
                st.error(str(e))
    st.caption("Limite importante : Browse API renvoie des annonces actives et leurs prix, pas l'historique des ventes réalisées ni les produits les plus vendus.")

with pages[2]:
    st.subheader("Analyser un catalogue fournisseur CSV")
    sample = template()
    st.download_button("Télécharger le modèle CSV", sample.to_csv(index=False).encode("utf-8"),
                       "modele_produits.csv", "text/csv")
    uploaded = st.file_uploader("Importer ton fichier CSV fournisseur", type=["csv"])
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
        st.write("Importe les prix réels d'un grossiste et vérifie l'accord de dropshipping avant de retenir un produit.")
        st.dataframe(sample, use_container_width=True, hide_index=True)

with pages[3]:
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

with pages[4]:
    st.subheader("Suivi des commandes")
    st.info("Le suivi automatique sera activé après une connexion vendeur eBay OAuth. Pour l'instant, aucune commande n'est lue ni modifiée.")

with pages[5]:
    st.subheader("Connexions et sécurité")
    st.markdown("""
    **Pour activer la recherche eBay :**
    1. Crée une application dans le portail développeur eBay.
    2. Récupère le Client ID (App ID) et le Client Secret (Cert ID) de l'environnement choisi.
    3. Dans Render > ton service > Environment, ajoute `EBAY_CLIENT_ID` et `EBAY_CLIENT_SECRET`.
    4. Redéploie le service. Ne colle jamais ces secrets dans GitHub ou dans une conversation.

    La recherche publique d'annonces utilise un jeton Application OAuth (Client Credentials).
    Elle ne connecte pas ton compte vendeur et ne permet pas de publier.
    """)
    st.error("Ne saisis jamais ici ton mot de passe eBay, un code SMS ou une clé API. Les clés doivent rester dans les variables secrètes de Render.")
