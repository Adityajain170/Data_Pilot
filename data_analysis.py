"""Dataset profiling, statistics, column detection, and automatic insights."""

import re

import pandas as pd


class DataAnalyzer:
    """Calculate useful analysis values from a Pandas DataFrame."""

    SALES_NAMES = {"sales", "weeklysales", "revenue", "totalsales", "amount", "income"}
    DATE_NAMES = {"date", "orderdate", "salesdate", "transactiondate", "weeklydate"}
    HOLIDAY_NAMES = {"holidayflag", "holiday", "isholiday"}
    GROUP_NAMES = {"store", "product", "category", "region", "city", "branch"}

    def __init__(self, dataframe):
        self.dataframe = dataframe

    @staticmethod
    def normalize_column_name(column):
        """Make a column name easier to compare regardless of spaces or punctuation."""
        return re.sub(r"[^a-z0-9]", "", str(column).lower())

    def overview(self):
        """Return the main dataset quality values."""
        return {
            "rows": len(self.dataframe),
            "columns": len(self.dataframe.columns),
            "missing_values": int(self.dataframe.isna().sum().sum()),
            "duplicate_rows": int(self.dataframe.duplicated().sum()),
        }

    def column_information(self):
        """Return one profiling record for every column."""
        information = []
        for column in self.dataframe.columns:
            information.append(
                {
                    "name": str(column),
                    "data_type": str(self.dataframe[column].dtype),
                    "missing_values": int(self.dataframe[column].isna().sum()),
                    "unique_values": int(self.dataframe[column].nunique(dropna=True)),
                }
            )
        return information

    def numeric_columns(self):
        """Return the names of numeric columns."""
        return list(self.dataframe.select_dtypes(include="number").columns)

    def categorical_columns(self):
        """Return the names of non-numeric columns."""
        numeric_names = set(self.numeric_columns())
        return [column for column in self.dataframe.columns if column not in numeric_names]

    def numeric_statistics(self):
        """Return basic statistics for every numeric column."""
        statistics = []
        for column in self.numeric_columns():
            values = self.dataframe[column].dropna()
            if values.empty:
                continue
            statistics.append(
                {
                    "name": str(column),
                    "count": int(values.count()),
                    "mean": float(values.mean()),
                    "median": float(values.median()),
                    "minimum": float(values.min()),
                    "maximum": float(values.max()),
                    "standard_deviation": float(values.std()) if len(values) > 1 else 0.0,
                }
            )
        return statistics

    def find_column(self, names, include_contains=False):
        """Find the first column whose normalized name matches a known name."""
        normalized = {self.normalize_column_name(name) for name in names}
        for column in self.dataframe.columns:
            column_name = self.normalize_column_name(column)
            if column_name in normalized or (include_contains and any(name in column_name for name in normalized)):
                return column
        return None

    def detect_sales_column(self):
        """Detect a likely sales or revenue column."""
        return self.find_column(self.SALES_NAMES, include_contains=True)

    def detect_date_column(self):
        """Detect a likely date column."""
        return self.find_column(self.DATE_NAMES, include_contains=True)

    def detect_holiday_column(self):
        """Detect a likely holiday indicator column."""
        return self.find_column(self.HOLIDAY_NAMES, include_contains=True)

    def detect_group_column(self):
        """Detect a useful categorical or discrete grouping column."""
        for name in self.GROUP_NAMES:
            column = self.find_column({name})
            if column is not None and self.dataframe[column].nunique(dropna=True) > 1:
                return column
        candidates = self.categorical_columns()
        for column in candidates:
            unique_count = self.dataframe[column].nunique(dropna=True)
            if 1 < unique_count <= 100:
                return column
        for column in self.numeric_columns():
            unique_count = self.dataframe[column].nunique(dropna=True)
            if 1 < unique_count <= 100:
                return column
        return None

    @staticmethod
    def _format_number(value):
        """Format a numeric insight value without hiding its meaning."""
        return f"{value:,.2f}"

    @staticmethod
    def _relationship_label(correlation):
        strength = abs(correlation)
        if strength < 0.30:
            word = "very weak"
        elif strength < 0.50:
            word = "weak"
        elif strength < 0.70:
            word = "moderate"
        elif strength < 0.90:
            word = "strong"
        else:
            word = "very strong"
        direction = "positive" if correlation >= 0 else "negative"
        return f"{word} {direction}"

    def generate_insights(self):
        """Generate factual, rule-based observations from the loaded DataFrame."""
        frame = self.dataframe
        overview = self.overview()
        result = {
            "general": [],
            "sales": [],
            "group": [],
            "date": [],
            "holiday": [],
            "correlation": [],
        }
        result["general"].append(f"The dataset contains {overview['rows']:,} records and {overview['columns']:,} columns.")
        if overview["missing_values"]:
            result["general"].append(f"The dataset contains {overview['missing_values']:,} missing values.")
        else:
            result["general"].append("No missing values were detected.")
        if overview["duplicate_rows"]:
            result["general"].append(f"The dataset contains {overview['duplicate_rows']:,} duplicate records.")
        else:
            result["general"].append("No duplicate records were detected.")
        result["general"].append(
            f"The dataset has {len(self.numeric_columns())} numeric and {len(self.categorical_columns())} categorical/text columns."
        )

        sales_column = self.detect_sales_column()
        if sales_column is not None:
            sales = pd.to_numeric(frame[sales_column], errors="coerce").dropna()
            if not sales.empty:
                result["sales"].extend(
                    [
                        f"Sales column detected: {sales_column}.",
                        f"Total sales: {self._format_number(sales.sum())}.",
                        f"Average sales: {self._format_number(sales.mean())}.",
                        f"Highest sale: {self._format_number(sales.max())}.",
                        f"Lowest sale: {self._format_number(sales.min())}.",
                    ]
                )

                group_column = self.detect_group_column()
                if group_column is not None:
                    grouped = pd.DataFrame({"group": frame[group_column], "sales": pd.to_numeric(frame[sales_column], errors="coerce")}).dropna()
                    if not grouped.empty:
                        totals = grouped.groupby("group")["sales"].sum()
                        if not totals.empty:
                            result["group"].extend(
                                [
                                    f"{group_column} '{totals.idxmax()}' generated the highest total sales ({self._format_number(totals.max())}).",
                                    f"{group_column} '{totals.idxmin()}' generated the lowest total sales ({self._format_number(totals.min())}).",
                                ]
                            )

                date_column = self.detect_date_column()
                if date_column is not None:
                    dates = pd.to_datetime(frame[date_column], errors="coerce")
                    valid_dates = dates.notna()
                    if valid_dates.any():
                        dated = pd.DataFrame({"date": dates, "sales": pd.to_numeric(frame[sales_column], errors="coerce")}).dropna()
                        if not dated.empty:
                            highest_date = dated.loc[dated["sales"].idxmax(), "date"]
                            lowest_date = dated.loc[dated["sales"].idxmin(), "date"]
                            result["date"].extend(
                                [
                                    f"Dates range from {dated['date'].min().date()} to {dated['date'].max().date()}.",
                                    f"The highest sales value occurred on {highest_date.date()}.",
                                    f"The lowest sales value occurred on {lowest_date.date()}.",
                                ]
                            )
                            monthly = dated.assign(month=dated["date"].dt.to_period("M")).groupby("month")["sales"].sum()
                            if len(monthly) > 1:
                                result["date"].append(f"The highest total-sales month was {monthly.idxmax()}.")

                holiday_column = self.detect_holiday_column()
                if holiday_column is not None:
                    holiday_values = frame[holiday_column]
                    holiday_mask = holiday_values.astype(str).str.lower().isin({"1", "true", "yes", "holiday"})
                    non_holiday_mask = ~holiday_mask
                    holiday_sales = pd.to_numeric(frame.loc[holiday_mask, sales_column], errors="coerce").dropna()
                    non_holiday_sales = pd.to_numeric(frame.loc[non_holiday_mask, sales_column], errors="coerce").dropna()
                    if not holiday_sales.empty and not non_holiday_sales.empty:
                        holiday_average = holiday_sales.mean()
                        non_holiday_average = non_holiday_sales.mean()
                        if non_holiday_average:
                            difference = ((holiday_average - non_holiday_average) / non_holiday_average) * 100
                            direction = "higher" if difference >= 0 else "lower"
                            result["holiday"].extend(
                                [
                                    f"Average holiday sales: {self._format_number(holiday_average)}.",
                                    f"Average non-holiday sales: {self._format_number(non_holiday_average)}.",
                                    f"Holiday sales were {abs(difference):.2f}% {direction} than non-holiday sales (observational comparison).",
                                ]
                            )

                for other_column in self.numeric_columns():
                    if other_column == sales_column:
                        continue
                    paired = frame[[sales_column, other_column]].apply(pd.to_numeric, errors="coerce").dropna()
                    if len(paired) > 1:
                        correlation = paired[sales_column].corr(paired[other_column])
                        if pd.notna(correlation):
                            result["correlation"].append(
                                f"{sales_column} and {other_column} show a {self._relationship_label(correlation)} relationship (correlation: {correlation:.2f})."
                            )
                if result["correlation"]:
                    result["correlation"].append("Correlation describes association; it does not prove causation.")

        return result
