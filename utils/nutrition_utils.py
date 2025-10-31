import pandas as pd

def get_nutrition_info(plato: str, csv_path="data/nutrition_data.csv"):
    """Busca la información nutricional del plato en el CSV."""
    df = pd.read_csv(csv_path)
    row = df[df["plato"].str.lower() == plato.lower()]
    if row.empty:
        return None
    return row.iloc[0].to_dict()
