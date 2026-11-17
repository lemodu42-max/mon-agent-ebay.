import argparse
import pandas as pd

REQUIRED = {
    "sku", "title", "supplier", "source_type", "supplier_cost",
    "shipping_cost", "suggested_price", "ebay_fee_rate",
    "payment_fee_rate", "other_cost", "stock", "delivery_days",
    "wholesale_agreement"
}

def truthy(value):
    return str(value).strip().lower() in {"1", "true", "yes", "oui", "vrai"}

def score_products(df, min_margin, min_rate):
    missing = REQUIRED - set(df.columns)
    if missing:
        raise ValueError("Colonnes manquantes : " + ", ".join(sorted(missing)))

    numeric = [
        "supplier_cost", "shipping_cost", "suggested_price",
        "ebay_fee_rate", "payment_fee_rate", "other_cost",
        "stock", "delivery_days"
    ]
    for col in numeric:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["wholesale_agreement"] = df["wholesale_agreement"].map(truthy)

    df["estimated_fees"] = df["suggested_price"] * (
        df["ebay_fee_rate"] + df["payment_fee_rate"]
    )
    df["estimated_profit"] = (
        df["suggested_price"] - df["supplier_cost"] -
        df["shipping_cost"] - df["estimated_fees"] - df["other_cost"]
    )
    df["margin_rate_pct"] = (
        df["estimated_profit"] / df["suggested_price"] * 100
    ).where(df["suggested_price"] > 0, 0)

    # Garde-fou : le prototype n'autorise comme candidats que les fournisseurs
    # grossistes avec accord préalable, stock positif et marge suffisante.
    df["policy_check"] = (
        (df["source_type"].str.lower() == "wholesaler") &
        df["wholesale_agreement"] &
        (df["stock"] > 0) &
        (df["delivery_days"] > 0)
    )
    df["candidate"] = (
        df["policy_check"] &
        (df["estimated_profit"] >= min_margin) &
        (df["margin_rate_pct"] >= min_rate)
    )
    df["review_note"] = df.apply(
        lambda r: "À vérifier manuellement" if r["candidate"]
        else "Écarté : fournisseur/accord/stock/délai/marge à vérifier", axis=1
    )
    return df.sort_values(
        ["candidate", "estimated_profit"], ascending=[False, False]
    )

def main():
    parser = argparse.ArgumentParser(description="Analyseur de produits eBay")
    parser.add_argument("--input", default="products.csv")
    parser.add_argument("--output", default="candidates.csv")
    parser.add_argument("--min-margin", type=float, default=5.0)
    parser.add_argument("--min-rate", type=float, default=20.0)
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    result = score_products(df, args.min_margin, args.min_rate)
    result.to_csv(args.output, index=False)
    print(f"{len(result)} produits analysés.")
    print(f"{int(result['candidate'].sum())} candidats à contrôler.")
    print(f"Résultat : {args.output}")
    print("Aucune annonce publiée et aucune commande passée.")

if __name__ == "__main__":
    main()
