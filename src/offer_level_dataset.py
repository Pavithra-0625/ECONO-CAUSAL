
from pathlib import Path
import pandas as pd

DATA_DIR = Path("outputs")


def main():
    transcript = pd.read_csv(DATA_DIR / "transcript_clean.csv")
    portfolio = pd.read_csv(DATA_DIR / "portfolio_clean.csv")

    # Standardize IDs for matching
    transcript["offer_id"] = transcript["offer_id"].astype("string")
    portfolio["id"] = portfolio["id"].astype("string")

    print("ECONOCAUSAL: OFFER ANALYSIS")
    print("=" * 55)

    print("\nOverall event counts:")
    print(transcript["event"].value_counts().to_string())

    # Select offer-related events with a valid offer ID
    events = transcript[
        transcript["event"].isin([
            "offer received",
            "offer viewed",
            "offer completed"
        ])
        & transcript["offer_id"].notna()
    ].copy()

    # Count events for each offer
    summary = (
        events.groupby(["offer_id", "event"])
        .size()
        .unstack(fill_value=0)
    )

    # Count distinct customers for each offer and event
    customers = (
        events.groupby(["offer_id", "event"])["person"]
        .nunique()
        .unstack(fill_value=0)
    )

    summary = summary.rename(columns={
        "offer received": "received_events",
        "offer viewed": "viewed_events",
        "offer completed": "completed_events"
    })

    customers = customers.rename(columns={
        "offer received": "received_customers",
        "offer viewed": "viewed_customers",
        "offer completed": "completed_customers"
    })

    summary = summary.join(customers, how="outer").fillna(0)

    # Ensure consistent columns even if an event type is absent
    for column in [
        "received_events", "viewed_events", "completed_events",
        "received_customers", "viewed_customers",
        "completed_customers"
    ]:
        if column not in summary.columns:
            summary[column] = 0

    summary = summary.reset_index()
    summary = summary.rename(columns={"index": "offer_id"})

    # Add offer characteristics
    metadata = portfolio[
        ["id", "offer_type", "duration", "difficulty", "reward"]
    ].drop_duplicates("id")

    summary = summary.merge(
        metadata,
        left_on="offer_id",
        right_on="id",
        how="left"
    )

    summary = summary.drop(columns=["id"], errors="ignore")

    # Save results locally
    output_path = DATA_DIR / "offer_event_summary.csv"
    summary.to_csv(output_path, index=False)

    print("\nOffer summary:")
    print(summary.to_string(index=False))
    print(f"\nSaved results to: {output_path}")

    print(
        "\nNote: Event counts describe customer activity; "
        "they do not prove that offers caused purchases."
    )


if __name__ == "__main__":
    main()
