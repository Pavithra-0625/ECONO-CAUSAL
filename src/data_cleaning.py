import json
from pathlib import Path

import pandas as pd

DATA_DIR = Path("dataset/archive (1)")
OUTPUT_DIR = Path("outputs")


def load_data():
    portfolio = pd.read_csv(DATA_DIR / "portfolio.csv")
    profile = pd.read_csv(DATA_DIR / "profile.csv")
    transcript = pd.read_csv(DATA_DIR / "transcript.csv")

    for df in [portfolio, profile, transcript]:
        df.drop(columns=["Unnamed: 0"], errors="ignore", inplace=True)

    return portfolio, profile, transcript


def clean_data(portfolio, profile, transcript):
    portfolio = portfolio.copy()
    profile = profile.copy()
    transcript = transcript.copy()

    for df in [portfolio, profile, transcript]:
        df.columns = df.columns.str.strip().str.lower()

    profile["age"] = pd.to_numeric(profile["age"], errors="coerce")
    profile["income"] = pd.to_numeric(profile["income"], errors="coerce")

    # Starbucks uses 118 as an invalid age / missing-value marker
    profile.loc[profile["age"] >= 118, "age"] = float("nan")

    profile["became_member_on"] = pd.to_datetime(
        profile["became_member_on"].astype(str),
        format="%Y%m%d",
        errors="coerce"
    )

    def parse_value(value):
        if not isinstance(value, str):
            return {}
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            try:
                import ast
                result = ast.literal_eval(value)
                return result if isinstance(result, dict) else {}
            except (ValueError, SyntaxError):
                return {}

    details = transcript["value"].apply(parse_value)

    transcript["offer_id"] = details.apply(
        lambda x: x.get("offer id", x.get("offer_id"))
    )
    transcript["amount"] = details.apply(lambda x: x.get("amount"))
    transcript["reward_amount"] = details.apply(lambda x: x.get("reward"))

    transcript["time"] = pd.to_numeric(
        transcript["time"], errors="coerce"
    )
    portfolio = portfolio.drop_duplicates()
    profile = profile.drop_duplicates(subset=["id"])
    # Preserve transcript events; do not remove identical-looking event rows.

    return portfolio, profile, transcript


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    portfolio, profile, transcript = load_data()
    portfolio, profile, transcript = clean_data(
        portfolio, profile, transcript
    )

    portfolio.to_csv(OUTPUT_DIR / "portfolio_clean.csv", index=False)
    profile.to_csv(OUTPUT_DIR / "profile_clean.csv", index=False)
    transcript.to_csv(OUTPUT_DIR / "transcript_clean.csv", index=False)

    print("EconoCausal Data Cleaning Report")
    print("-" * 40)

    for name, df in [
        ("Portfolio", portfolio),
        ("Profile", profile),
        ("Transcript", transcript)
    ]:
        print(f"\n{name} shape: {df.shape}")
        print("Missing values:", df.isnull().sum().sum())

    print("\nEvent counts:")
    print(transcript["event"].value_counts().to_string())
    print("\nCleaning completed. Files saved in outputs/.")


if __name__ == "__main__":
    main()