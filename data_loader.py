"""Functions for loading CSV and Excel files into Pandas DataFrames."""

from pathlib import Path

import pandas as pd


class DataLoader:
    """Load supported dataset files."""

    def load_csv(self, file_path):
        """Load a CSV file and return its DataFrame."""
        return pd.read_csv(file_path)

    def load_excel(self, file_path):
        """Load an Excel file and return its DataFrame."""
        return pd.read_excel(file_path)

    def load_file(self, file_path):
        """Load a supported CSV or Excel file based on its extension."""
        extension = Path(file_path).suffix.lower()

        if extension == ".csv":
            return self.load_csv(file_path)
        if extension in {".xlsx", ".xls"}:
            return self.load_excel(file_path)

        raise ValueError("Unsupported file type. Please choose a CSV or Excel file.")
