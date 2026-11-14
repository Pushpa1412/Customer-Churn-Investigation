"""Generate a reproducible, fully synthetic subscription customer dataset."""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

def main():
    rng = np.random.default_rng(42)
    n = 1200

    tenure = rng.integers(1, 73, size=n)
    contract = rng.choice(
        ["Month-to-month", "One year", "Two year"],
        size=n,
        p=[0.55, 0.27, 0.18],
    )
    payment = rng.choice(
        ["Card", "Bank transfer", "Digital wallet"],
        size=n,
        p=[0.45, 0.30, 0.25],
    )
    monthly_charges = np.round(rng.normal(75, 22, size=n).clip(20, 150), 2)
    support_tickets = rng.poisson(lam=1.4, size=n)

    # These coefficients are simulation assumptions, not estimated real-world effects.
    logit = (
        0.45
        - 0.035 * tenure
        + 0.95 * (contract == "Month-to-month")
        - 0.55 * (contract == "Two year")
        + 0.28 * support_tickets
        + 0.004 * (monthly_charges - 75)
    )
    probability = 1 / (1 + np.exp(-logit))
    churn = rng.binomial(1, probability)

    df = pd.DataFrame({
        "customer_id": [f"CUST{i:05d}" for i in range(1, n + 1)],
        "tenure_months": tenure,
        "monthly_charges": monthly_charges,
        "contract_type": contract,
        "support_tickets": support_tickets,
        "payment_method": payment,
        "churn": churn,
    })

    path = DATA_DIR / "subscription_customers.csv"
    df.to_csv(path, index=False)
    print(f"Created {len(df):,} synthetic records: {path}")
    print(f"Simulated churn rate: {df['churn'].mean():.1%}")

if __name__ == "__main__":
    main()
