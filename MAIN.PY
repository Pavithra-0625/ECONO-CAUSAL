import pandas as pd

files = {
    "portfolio": "dataset/archive (1)/portfolio.csv",
    "profile": "dataset/archive (1)/profile.csv",
    "transcript": "dataset/archive (1)/transcript.csv"
}

for name, path in files.items():
    print("\n", "=" * 40)
    print("Dataset:", name)

    df = pd.read_csv(path)

    print("Shape:", df.shape)
    print("Columns:", df.columns.tolist())
    print("\nFirst 5 rows:")
    print(df.head())
    print("\nMissing values:")
    print(df.isnull().sum())