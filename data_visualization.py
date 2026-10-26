"""Matplotlib chart creation for the DataPilot Tkinter interface."""

import pandas as pd


def create_chart(dataframe, chart_type, x_column, y_column, figure):
    """Draw a selected chart using the supplied DataFrame and Matplotlib figure."""
    figure.clear()
    axis = figure.add_subplot(111)
    chart_type = chart_type.lower()

    if chart_type == "bar chart":
        values = dataframe[[x_column, y_column]].copy()
        values[y_column] = pd.to_numeric(values[y_column], errors="coerce")
        values = values.dropna().groupby(x_column, as_index=False)[y_column].sum()
        values = values.sort_values(y_column, ascending=False).head(30)
        if values.empty:
            raise ValueError("The selected columns do not contain plottable values.")
        axis.bar(values[x_column].astype(str), values[y_column])
        axis.set_xlabel(x_column)
        axis.set_ylabel(y_column)
        axis.tick_params(axis="x", rotation=45)
        axis.set_title(f"{y_column} by {x_column}")

    elif chart_type == "line chart":
        values = dataframe[[x_column, y_column]].copy()
        values["_date"] = pd.to_datetime(values[x_column], errors="coerce")
        values[y_column] = pd.to_numeric(values[y_column], errors="coerce")
        if values["_date"].notna().sum() > 0:
            values = values.dropna(subset=["_date", y_column]).sort_values("_date")
            axis.plot(values["_date"], values[y_column], marker=".", linewidth=1)
            axis.set_xlabel(x_column)
        else:
            values[y_column] = pd.to_numeric(values[y_column], errors="coerce")
            values = values.dropna(subset=[x_column, y_column])
            axis.plot(values[x_column], values[y_column], marker=".", linewidth=1)
            axis.set_xlabel(x_column)
        if values.empty:
            raise ValueError("The selected columns do not contain plottable values.")
        axis.set_ylabel(y_column)
        axis.set_title(f"{y_column} over {x_column}")
        figure.autofmt_xdate()

    elif chart_type == "scatter plot":
        values = dataframe[[x_column, y_column]].apply(pd.to_numeric, errors="coerce").dropna()
        if values.empty:
            raise ValueError("Scatter plots require two numeric columns with values.")
        axis.scatter(values[x_column], values[y_column], alpha=0.65)
        axis.set_xlabel(x_column)
        axis.set_ylabel(y_column)
        axis.set_title(f"{y_column} vs {x_column}")

    elif chart_type == "histogram":
        values = pd.to_numeric(dataframe[x_column], errors="coerce").dropna()
        if values.empty:
            raise ValueError("Histograms require a numeric column with values.")
        axis.hist(values, bins=min(20, max(5, len(values) // 10)), edgecolor="white")
        axis.set_xlabel(x_column)
        axis.set_ylabel("Frequency")
        axis.set_title(f"Distribution of {x_column}")

    else:
        raise ValueError("Unknown chart type.")

    figure.tight_layout()
