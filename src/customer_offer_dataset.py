import argparse
from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"

RECEIVED = "offer received"
VIEWED = "offer viewed"
COMPLETED = "offer completed"
TRANSACTION = "transaction"


def build_customer_offer_dataset(transcript, portfolio, profile=None):
    t = transcript.copy().reset_index(drop=True)
    p = portfolio.copy()

    required_t = {"person", "event", "time", "offer_id"}
    required_p = {"id", "duration"}

    if required_t - set(t.columns):
        raise ValueError(f"Missing transcript columns: {required_t - set(t.columns)}")
    if required_p - set(p.columns):
        raise ValueError(f"Missing portfolio columns: {required_p - set(p.columns)}")

    t["_row"] = range(len(t))
    for col in ["person", "offer_id"]:
        t[col] = t[col].astype("string").str.strip().replace("", pd.NA)

    t["event"] = t["event"].astype("string").str.strip().str.lower()
    t["time"] = pd.to_numeric(t["time"], errors="coerce")

    if "amount" not in t.columns:
        t["amount"] = pd.NA
    t["amount"] = pd.to_numeric(t["amount"], errors="coerce")

    p["id"] = p["id"].astype("string").str.strip()
    p["duration"] = pd.to_numeric(p["duration"], errors="coerce")

    if "offer_type" in p.columns:
        p["offer_type"] = p["offer_type"].astype("string").str.lower().str.strip()

    if profile is not None:
        profile = profile.copy()
        if "id" not in profile.columns:
            raise ValueError("Profile data is missing the id column")
        profile["id"] = profile["id"].astype("string").str.strip()
        profile = profile.drop_duplicates("id", keep="first")

    usable = t.loc[t["person"].notna() & t["time"].notna()].copy()

    receipts = usable.loc[
        usable["event"].eq(RECEIVED) & usable["offer_id"].notna(),
        ["person", "offer_id", "time", "_row"]
    ].copy()

    if receipts.empty:
        raise ValueError("No valid offer-received rows found")

    receipts = receipts.sort_values(
        ["person", "time", "_row"], kind="stable"
    ).reset_index(drop=True)

    receipts["receipt_instance_id"] = range(1, len(receipts) + 1)
    receipts = receipts.rename(columns={"time": "received_time_hours"})

    receipts["next_offer_received_time_hours"] = (
        receipts.groupby("person")["received_time_hours"].shift(-1)
    )

    meta_cols = [
        c for c in ["id", "offer_type", "duration", "difficulty", "reward"]
        if c in p.columns
    ]
    metadata = p[meta_cols].drop_duplicates("id").rename(
        columns={"id": "offer_id", "duration": "offer_duration_days"}
    )

    receipts = receipts.merge(
        metadata, on="offer_id", how="left", validate="many_to_one"
    )
    receipts["offer_duration_days"] = pd.to_numeric(
        receipts["offer_duration_days"], errors="coerce"
    )

    receipts["nominal_expiry_time_hours"] = (
        receipts["received_time_hours"] + 24 * receipts["offer_duration_days"]
    )

    last_time = float(usable["time"].max())
    window_ends = []
    reasons = []
    complete = []

    for row in receipts.itertuples(index=False):
        start = row.received_time_hours
        expiry = row.nominal_expiry_time_hours
        duration = row.offer_duration_days
        next_receipt = row.next_offer_received_time_hours

        if pd.isna(expiry) or pd.isna(duration) or duration <= 0:
            window_ends.append(start)
            reasons.append("invalid_offer_duration")
            complete.append(False)
        elif pd.notna(next_receipt) and next_receipt < expiry:
            window_ends.append(float(next_receipt))
            reasons.append("next_offer_received")
            complete.append(False)
        elif expiry > last_time:
            window_ends.append(last_time)
            reasons.append("dataset_end")
            complete.append(False)
        else:
            window_ends.append(float(expiry))
            reasons.append("none")
            complete.append(True)

    receipts["observed_window_end_hours"] = window_ends
    receipts["window_truncation_reason"] = reasons
    receipts["full_validity_window_observed"] = complete
    receipts["observed_window_days"] = (
        receipts["observed_window_end_hours"]
        - receipts["received_time_hours"]
    ) / 24

    # Build indexes once to avoid repeatedly scanning the full transcript.
    event_indexes = {}

    for person, group in usable.groupby("person", sort=False):
        group = group.sort_values(["time", "_row"], kind="stable")
        view_index = {}
        completion_index = {}

        relevant = group.loc[
            group["event"].isin([VIEWED, COMPLETED])
            & group["offer_id"].notna()
        ]

        for offer_id, offer_group in relevant.groupby("offer_id", sort=False):
            view_index[offer_id] = offer_group.loc[
                offer_group["event"].eq(VIEWED), "time"
            ].to_numpy(dtype=float)
            completion_index[offer_id] = offer_group.loc[
                offer_group["event"].eq(COMPLETED), "time"
            ].to_numpy(dtype=float)

        tx = group.loc[group["event"].eq(TRANSACTION)]
        tx_times = tx["time"].to_numpy(dtype=float)
        tx_amounts = tx["amount"].to_numpy(dtype=float, na_value=np.nan)
        tx_missing = np.isnan(tx_amounts)
        amount_prefix = np.concatenate(
            ([0.0], np.cumsum(np.nan_to_num(tx_amounts, nan=0.0)))
        )
        missing_prefix = np.concatenate(
            ([0], np.cumsum(tx_missing.astype(int)))
        )

        event_indexes[person] = {
            "views": view_index,
            "completions": completion_index,
            "tx_times": tx_times,
            "amount_prefix": amount_prefix,
            "missing_prefix": missing_prefix,
        }

    def count_between(times, start, end):
        if times is None or len(times) == 0:
            return 0
        left = np.searchsorted(times, start, side="right")
        right = np.searchsorted(times, end, side="left")
        return int(right - left)

    view_counts = []
    completion_counts = []
    transaction_counts = []
    spend_amounts = []
    missing_amount_counts = []

    for row in receipts.itertuples(index=False):
        start = row.received_time_hours
        end = row.observed_window_end_hours
        person = row.person
        offer = row.offer_id

        if row.window_truncation_reason == "invalid_offer_duration":
            view_counts.append(pd.NA)
            completion_counts.append(pd.NA)
            transaction_counts.append(pd.NA)
            spend_amounts.append(pd.NA)
            missing_amount_counts.append(pd.NA)
            continue

        index = event_indexes.get(person)
        if index is None:
            view_counts.append(0)
            completion_counts.append(0)
            transaction_counts.append(0)
            spend_amounts.append(0.0)
            missing_amount_counts.append(0)
            continue

        view_counts.append(count_between(index["views"].get(offer), start, end))
        completion_counts.append(
            count_between(index["completions"].get(offer), start, end)
        )

        tx_times = index["tx_times"]
        left = int(np.searchsorted(tx_times, start, side="right"))
        right = int(np.searchsorted(tx_times, end, side="left"))
        tx_count = right - left
        transaction_counts.append(tx_count)

        missing_prefix = index["missing_prefix"]
        missing_count = int(missing_prefix[right] - missing_prefix[left])
        missing_amount_counts.append(missing_count)

        if tx_count == 0:
            spend_amounts.append(0.0)
        else:
            prefix = index["amount_prefix"]
            total = float(prefix[right] - prefix[left])
            spend_amounts.append(pd.NA if missing_count == tx_count else total)

    receipts["view_event_count_in_observed_window"] = pd.array(
        view_counts, dtype="Int64"
    )
    receipts["completion_event_count_in_observed_window"] = pd.array(
        completion_counts, dtype="Int64"
    )
    receipts["transaction_count_in_observed_window"] = pd.array(
        transaction_counts, dtype="Int64"
    )
    receipts["spend_amount_in_observed_window"] = pd.to_numeric(
        pd.Series(spend_amounts, index=receipts.index), errors="coerce"
    )
    receipts["transaction_rows_with_missing_amount"] = pd.array(
        missing_amount_counts, dtype="Int64"
    )

    receipts["viewed_within_observed_window"] = (
        receipts["view_event_count_in_observed_window"].gt(0).astype("Int64")
    )
    receipts["completed_within_observed_window"] = (
        receipts["completion_event_count_in_observed_window"].gt(0).astype("Int64")
    )
    receipts["any_transaction_within_observed_window"] = (
        receipts["transaction_count_in_observed_window"].gt(0).astype("Int64")
    )
    receipts["treatment_received_offer"] = 1

    if profile is not None:
        profile_cols = [
            c for c in ["id", "age", "gender", "income", "became_member_on"]
            if c in profile.columns
        ]
        receipts = receipts.merge(
            profile[profile_cols].rename(columns={"id": "person"}),
            on="person", how="left", validate="many_to_one"
        )

    output_cols = [
        "receipt_instance_id", "person", "offer_id", "offer_type",
        "treatment_received_offer", "received_time_hours",
        "offer_duration_days", "nominal_expiry_time_hours",
        "next_offer_received_time_hours", "observed_window_end_hours",
        "observed_window_days", "window_truncation_reason",
        "full_validity_window_observed", "view_event_count_in_observed_window",
        "viewed_within_observed_window",
        "completion_event_count_in_observed_window",
        "completed_within_observed_window",
        "transaction_count_in_observed_window",
        "any_transaction_within_observed_window",
        "spend_amount_in_observed_window",
        "transaction_rows_with_missing_amount", "difficulty", "reward",
        "age", "gender", "income", "became_member_on"
    ]

    return receipts[
        [c for c in output_cols if c in receipts.columns]
    ].sort_values(
        ["offer_id", "person", "received_time_hours", "receipt_instance_id"],
        kind="stable"
    ).reset_index(drop=True)


def build_offer_summary(df):
    keys = [c for c in ["offer_id", "offer_type"] if c in df.columns]

    summary = df.groupby(keys, dropna=False).agg(
        receipt_instances=("receipt_instance_id", "size"),
        unique_customers=("person", "nunique"),
        complete_windows=("full_validity_window_observed", "sum")
    ).reset_index()

    summary["censored_or_invalid_windows"] = (
        summary["receipt_instances"] - summary["complete_windows"]
    )

    complete_df = df.loc[df["full_validity_window_observed"]]

    if complete_df.empty:
        for col in [
            "view_rate_pct", "completion_event_rate_pct",
            "transaction_rate_pct", "mean_spend_in_window",
            "mean_transactions_in_window"
        ]:
            summary[col] = pd.NA
        return summary

    rates = complete_df.groupby(keys, dropna=False).agg(
        view_rate_pct=("viewed_within_observed_window", "mean"),
        completion_event_rate_pct=("completed_within_observed_window", "mean"),
        transaction_rate_pct=("any_transaction_within_observed_window", "mean"),
        mean_spend_in_window=("spend_amount_in_observed_window", "mean"),
        mean_transactions_in_window=("transaction_count_in_observed_window", "mean")
    ).reset_index()

    for col in [
        "view_rate_pct", "completion_event_rate_pct", "transaction_rate_pct"
    ]:
        rates[col] *= 100

    return summary.merge(rates, on=keys, how="left", validate="one_to_one")


def self_test():
    portfolio = pd.DataFrame([
        {"id": "A", "offer_type": "discount", "duration": 2, "difficulty": 5, "reward": 5},
        {"id": "B", "offer_type": "bogo", "duration": 1, "difficulty": 1, "reward": 1},
        {"id": "C", "offer_type": "info", "duration": 3, "difficulty": 0, "reward": 0}
    ])

    transcript = pd.DataFrame([
        {"person": "c1", "event": RECEIVED, "time": 0, "offer_id": "A", "amount": None},
        {"person": "c1", "event": VIEWED, "time": 1, "offer_id": "A", "amount": None},
        {"person": "c1", "event": TRANSACTION, "time": 2, "offer_id": None, "amount": 5.0},
        {"person": "c1", "event": RECEIVED, "time": 24, "offer_id": "B", "amount": None},
        {"person": "c1", "event": VIEWED, "time": 26, "offer_id": "B", "amount": None},
        {"person": "c1", "event": TRANSACTION, "time": 30, "offer_id": None, "amount": 7.0},
        {"person": "c1", "event": COMPLETED, "time": 35, "offer_id": "B", "amount": None},
        {"person": "c2", "event": RECEIVED, "time": 90, "offer_id": "C", "amount": None},
        {"person": "c2", "event": TRANSACTION, "time": 95, "offer_id": None, "amount": 2.0},
        {"person": "c2", "event": TRANSACTION, "time": 100, "offer_id": None, "amount": 3.0}
    ])

    profile = pd.DataFrame([
        {"id": "c1", "age": 30, "gender": "f", "income": 60000}
    ])

    dataset = build_customer_offer_dataset(transcript, portfolio, profile)
    a = dataset.loc[dataset.offer_id.eq("A")].iloc[0]
    b = dataset.loc[dataset.offer_id.eq("B")].iloc[0]
    c = dataset.loc[dataset.offer_id.eq("C")].iloc[0]

    assert len(dataset) == 3
    assert a.window_truncation_reason == "next_offer_received"
    assert int(a.transaction_count_in_observed_window) == 1
    assert float(a.spend_amount_in_observed_window) == 5.0
    assert b.window_truncation_reason == "none"
    assert bool(b.full_validity_window_observed)
    assert int(b.completed_within_observed_window) == 1
    assert b.age == 30
    assert c.window_truncation_reason == "dataset_end"
    assert len(build_offer_summary(dataset)) == 3

    print("Self-test passed: dataset construction and summary checks.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return

    transcript_path = OUT / "transcript_clean.csv"
    portfolio_path = OUT / "portfolio_clean.csv"
    profile_path = OUT / "profile_clean.csv"

    for path in [transcript_path, portfolio_path]:
        if not path.exists():
            raise FileNotFoundError(
                f"Missing {path}. Please run src/data_cleaning.py first."
            )

    transcript = pd.read_csv(transcript_path)
    portfolio = pd.read_csv(portfolio_path)
    profile = pd.read_csv(profile_path) if profile_path.exists() else None

    dataset = build_customer_offer_dataset(transcript, portfolio, profile)
    summary = build_offer_summary(dataset)
    OUT.mkdir(parents=True, exist_ok=True)

    dataset.to_csv(OUT / "customer_offer_dataset.csv", index=False)
    summary.to_csv(OUT / "customer_offer_summary.csv", index=False)

    print(f"Receipt rows: {len(dataset):,}")
    print(f"Unique customers: {dataset.person.nunique():,}")
    print(f"Offers: {dataset.offer_id.nunique():,}")
    print(f"Complete windows: {int(dataset.full_validity_window_observed.sum()):,}")
    print("Offer summary:")
    print(summary.to_string(index=False))
    print("\nSaved customer_offer_dataset.csv and customer_offer_summary.csv in outputs/.")
    print(
        "\nImportant: transaction outcomes describe customer activity during "
        "the observation window; they do not prove that a particular offer "
        "caused a purchase. This dataset is descriptive, not yet a causal estimate."
    )


if __name__ == "__main__":
    main()
