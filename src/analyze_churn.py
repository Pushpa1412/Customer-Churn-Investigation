"""Validate, summarize and visualize the synthetic churn dataset."""
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "subscription_customers.csv"
OUT = ROOT / "outputs"
CHARTS = OUT / "charts"
OUT.mkdir(exist_ok=True)
CHARTS.mkdir(parents=True, exist_ok=True)

REQUIRED = {
    "customer_id", "tenure_months", "monthly_charges", "contract_type",
    "support_tickets", "payment_method", "churn"
}

def validate_data(df):
    missing_columns = REQUIRED - set(df.columns)
    if missing_columns:
        raise ValueError(f"Missing required columns: {sorted(missing_columns)}")
    if df["customer_id"].duplicated().any():
        raise ValueError("Duplicate customer_id values found.")
    if df[list(REQUIRED)].isna().any().any():
        raise ValueError("Missing values found in required columns.")
    if not set(df["churn"].unique()).issubset({0, 1}):
        raise ValueError("churn must contain only 0 and 1.")
    if (df[["tenure_months", "monthly_charges", "support_tickets"]] < 0).any().any():
        raise ValueError("Numeric tenure, charges and ticket values must be non-negative.")
    allowed_contracts = {"Month-to-month", "One year", "Two year"}
    if not set(df["contract_type"].unique()).issubset(allowed_contracts):
        raise ValueError("Unexpected contract_type category.")
    print("PASS: required columns, uniqueness, missingness, labels, numeric ranges and contract categories.")

def main():
    if not DATA_PATH.exists():
        raise FileNotFoundError("Dataset not found. Run: python src/generate_data.py")

    df = pd.read_csv(DATA_PATH)
    validate_data(df)

    # Explicit type conversion and defensive cleaning.
    df["tenure_months"] = pd.to_numeric(df["tenure_months"], errors="raise").astype(int)
    df["monthly_charges"] = pd.to_numeric(df["monthly_charges"], errors="raise")
    df["support_tickets"] = pd.to_numeric(df["support_tickets"], errors="raise").astype(int)
    df["churn"] = pd.to_numeric(df["churn"], errors="raise").astype(int)

    total = len(df)
    churn_rate = df["churn"].mean()
    print(f"Rows: {total:,}")
    print(f"Overall churn rate: {churn_rate:.1%}")
    print(f"Duplicate customer IDs: {df['customer_id'].duplicated().sum()}")
    print(f"Missing cells: {int(df.isna().sum().sum())}")

    segment = (
        df.groupby("contract_type", observed=True)
          .agg(customers=("customer_id", "count"), churn_rate=("churn", "mean"))
          .reset_index()
          .sort_values("churn_rate", ascending=False)
    )
    segment.to_csv(OUT / "contract_churn_summary.csv", index=False)
    print("\nChurn by contract:")
    print(segment.to_string(index=False))

    # Visual 1: overall churn distribution.
    counts = df["churn"].map({0: "Retained", 1: "Churned"}).value_counts()
    plt.figure(figsize=(6, 4))
    sns.barplot(x=counts.index, y=counts.values)
    plt.title("Customer Churn Distribution")
    plt.xlabel("Customer status")
    plt.ylabel("Number of customers")
    plt.tight_layout()
    plt.savefig(CHARTS / "churn_distribution.png", dpi=150)
    plt.close()

    # Visual 2: churn rate by contract.
    plt.figure(figsize=(7, 4))
    sns.barplot(data=segment, x="contract_type", y="churn_rate")
    plt.title("Churn Rate by Contract Type")
    plt.xlabel("Contract type")
    plt.ylabel("Churn rate")
    plt.ylim(0, 1)
    plt.tight_layout()
    plt.savefig(CHARTS / "churn_by_contract.png", dpi=150)
    plt.close()

    # Visual 3: churn rate by tenure band.
    df["tenure_band"] = pd.cut(
        df["tenure_months"],
        bins=[0, 6, 12, 24, 48, 72],
        labels=["1-6", "7-12", "13-24", "25-48", "49-72"],
        include_lowest=True,
    )
    tenure_summary = df.groupby("tenure_band", observed=True)["churn"].mean().reset_index()
    plt.figure(figsize=(7, 4))
    sns.barplot(data=tenure_summary, x="tenure_band", y="churn")
    plt.title("Churn Rate by Customer Tenure")
    plt.xlabel("Tenure (months)")
    plt.ylabel("Churn rate")
    plt.ylim(0, 1)
    plt.tight_layout()
    plt.savefig(CHARTS / "churn_by_tenure.png", dpi=150)
    plt.close()

    # Evidence-based recommendations are computed from the segment summaries.
    highest = segment.iloc[0]
    lowest = segment.iloc[-1]
    report = [
        "# Initial Findings",
        "",
        "> These findings describe a synthetic dataset generated from stated assumptions; they are not real-company evidence.",
        "",
        f"- Total simulated customers: **{total:,}**.",
        f"- Overall simulated churn rate: **{churn_rate:.1%}**.",
        f"- Highest-churn contract segment: **{highest['contract_type']}** ({highest['churn_rate']:.1%}, n={int(highest['customers'])}).",
        f"- Lowest-churn contract segment: **{lowest['contract_type']}** ({lowest['churn_rate']:.1%}, n={int(lowest['customers'])}).",
        "",
        "## Suggested retention actions",
        "- Review the customer journey and onboarding experience for short-tenure subscribers.",
        "- Test whether longer-term contract options and transparent plan benefits improve retention; do not assume the observed association proves causation.",
        "- Review support-ticket themes and resolution times before designing service improvements.",
        "",
        "## Limitations",
        "- Data is simulated and its patterns are partly determined by the generator's assumptions.",
        "- Segment rates are descriptive and do not establish causal effects.",
        "- Validate all hypotheses using representative, authorized real data before making business decisions.",
    ]
    (OUT / "initial_findings.md").write_text("\n".join(report), encoding="utf-8")
    print(f"\nSaved tables, charts and findings under: {OUT}")

if __name__ == "__main__":
    main()
