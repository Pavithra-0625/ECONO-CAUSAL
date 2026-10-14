import pandas as pd
from pathlib import Path

data_folder = Path("dataset/archive (1)")

files = {
    "portfolio": data_folder / "portfolio.csv",
    "profile": data_folder / "profile.csv",
    "transcript": data_folder / "transcript.csv",
}

for name, path in files.items():
    print("\n" + "=" * 60)
    print(f"DATASET: {name.upper()}")
    print("=" * 60)

    df = pd.read_csv(path)

    print("Shape:", df.shape)
    print("\nColumns:")
    print(df.columns.tolist())

    print("\nFirst 3 rows:")
    print(df.head(3).to_string())

    print("\nMissing values by column:")
    print(df.isnull().sum().to_string())