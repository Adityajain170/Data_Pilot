"""DataPilot desktop application: analysis, insights, and visualization."""

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from data_analysis import DataAnalyzer
from data_loader import DataLoader
from data_visualization import create_chart


class DataPilotApp:
    """Simple Tkinter GUI for the DataPilot milestones."""

    def __init__(self, root):
        self.root = root
        self.root.title("DataPilot — Turn Raw Data into Decisions")
        self.root.geometry("1150x760")
        self.root.minsize(850, 550)

        self.dataframe = None
        self.data_loader = DataLoader()
        self.dataset_name = tk.StringVar(value="No dataset loaded")
        self.dataset_summary = tk.StringVar(value="Rows: —    Columns: —")
        self.status_text = tk.StringVar(value="Load a CSV or Excel file to begin.")

        self._build_interface()

    def _build_interface(self):
        """Create the window layout and controls."""
        header = ttk.Frame(self.root, padding=(20, 18, 20, 10))
        header.pack(fill="x")

        ttk.Label(header, text="DATAPILOT", font=("TkDefaultFont", 22, "bold")).pack(anchor="w")
        ttk.Label(header, text="Turn Raw Data into Decisions", font=("TkDefaultFont", 11)).pack(anchor="w", pady=(2, 12))

        controls = ttk.Frame(header)
        controls.pack(anchor="w")
        ttk.Button(controls, text="Load Dataset", command=self.load_dataset).pack(side="left", padx=(0, 8))
        ttk.Button(controls, text="Dataset Analysis", command=self.show_analysis).pack(side="left", padx=(0, 8))
        ttk.Button(controls, text="Visualize", command=self.show_visualization).pack(side="left", padx=(0, 8))
        ttk.Button(controls, text="Insights", command=self.show_insights).pack(side="left")

        summary = ttk.LabelFrame(self.root, text="Current Dataset", padding=10)
        summary.pack(fill="x", padx=20, pady=(0, 10))
        ttk.Label(summary, textvariable=self.dataset_name, font=("TkDefaultFont", 10, "bold")).pack(anchor="w")
        ttk.Label(summary, textvariable=self.dataset_summary).pack(anchor="w", pady=(4, 0))

        self.content = ttk.Frame(self.root, padding=(20, 0, 20, 10))
        self.content.pack(fill="both", expand=True)
        self._show_welcome()

        ttk.Label(self.root, textvariable=self.status_text, relief="sunken", anchor="w", padding=5).pack(fill="x", side="bottom")

    def _clear_content(self):
        for widget in self.content.winfo_children():
            widget.destroy()

    def _show_welcome(self):
        self._clear_content()
        welcome = ttk.Frame(self.content)
        welcome.pack(expand=True)
        ttk.Label(welcome, text="Welcome to DataPilot", font=("TkDefaultFont", 18, "bold")).pack()
        ttk.Label(welcome, text="Load a dataset to view its contents, calculate metrics, find insights, and create charts.").pack(pady=(8, 0))

    def load_dataset(self):
        """Ask for a file, load it, and display its first 20 rows."""
        file_path = filedialog.askopenfilename(
            title="Select a dataset",
            filetypes=[
                ("Supported datasets", "*.csv *.xlsx *.xls"),
                ("CSV files", "*.csv"),
                ("Excel files", "*.xlsx *.xls"),
                ("All files", "*.*"),
            ],
        )
        if not file_path:
            self.status_text.set("No file selected.")
            return

        try:
            dataframe = self.data_loader.load_file(file_path)
            if dataframe.empty:
                raise ValueError("The selected file does not contain any data rows.")
        except Exception as error:
            messagebox.showerror("Could not load dataset", str(error))
            self.status_text.set("The dataset could not be loaded.")
            return

        self.dataframe = dataframe
        self.dataset_name.set(Path(file_path).name)
        self.dataset_summary.set(f"Rows: {len(dataframe):,}    Columns: {len(dataframe.columns):,}")
        self.status_text.set(f"Dataset loaded successfully: {Path(file_path).name}")
        self.show_preview()
        messagebox.showinfo(
            "Dataset loaded",
            f"Dataset loaded successfully!\n\nFile: {Path(file_path).name}\nRows: {len(dataframe):,}\nColumns: {len(dataframe.columns):,}",
        )

    def show_preview(self):
        """Display the first 20 rows in a scrollable Treeview."""
        if self.dataframe is None:
            messagebox.showwarning("No dataset", "Load a CSV or Excel file first.")
            return

        self._clear_content()
        ttk.Label(self.content, text="DATASET PREVIEW", font=("TkDefaultFont", 14, "bold")).pack(anchor="w", pady=(0, 8))

        table_frame = ttk.Frame(self.content)
        table_frame.pack(fill="both", expand=True)
        column_names = [str(column) for column in self.dataframe.columns]
        tree = ttk.Treeview(table_frame, columns=column_names, show="headings")
        vertical_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        horizontal_scroll = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vertical_scroll.set, xscrollcommand=horizontal_scroll.set)

        for column in column_names:
            tree.heading(column, text=column)
            tree.column(column, width=130, minwidth=80, anchor="w")

        for row in self.dataframe.head(20).itertuples(index=False, name=None):
            values = ["" if value != value else str(value) for value in row]
            tree.insert("", "end", values=values)

        tree.grid(row=0, column=0, sticky="nsew")
        vertical_scroll.grid(row=0, column=1, sticky="ns")
        horizontal_scroll.grid(row=1, column=0, sticky="ew")
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)
        ttk.Label(self.content, text="Showing the first 20 rows.", foreground="#555555").pack(anchor="w", pady=(6, 0))

    def show_analysis(self):
        """Calculate and display profiling and numeric statistics."""
        if self.dataframe is None:
            messagebox.showwarning("No dataset", "Load a CSV or Excel file before opening Dataset Analysis.")
            return

        analyzer = DataAnalyzer(self.dataframe)
        overview = analyzer.overview()
        information = analyzer.column_information()
        numeric_columns = analyzer.numeric_columns()
        categorical_columns = analyzer.categorical_columns()
        statistics = analyzer.numeric_statistics()

        self._clear_content()
        ttk.Label(self.content, text="DATASET ANALYSIS", font=("TkDefaultFont", 14, "bold")).pack(anchor="w", pady=(0, 8))

        canvas = tk.Canvas(self.content, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.content, orient="vertical", command=canvas.yview)
        report = ttk.Frame(canvas)
        report.bind("<Configure>", lambda event: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=report, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        overview_frame = ttk.LabelFrame(report, text="Dataset Overview", padding=10)
        overview_frame.pack(fill="x", pady=(0, 10))
        overview_text = (
            f"Rows: {overview['rows']:,}    Columns: {overview['columns']:,}    "
            f"Missing Values: {overview['missing_values']:,}    Duplicate Rows: {overview['duplicate_rows']:,}\n"
            f"Numeric Columns: {len(numeric_columns)}    Categorical/Text Columns: {len(categorical_columns)}"
        )
        ttk.Label(overview_frame, text=overview_text, justify="left").pack(anchor="w")

        self._add_table(
            report,
            "Column Information",
            ("Column Name", "Data Type", "Missing Values", "Unique Values"),
            [(item["name"], item["data_type"], item["missing_values"], item["unique_values"]) for item in information],
        )

        stat_rows = [
            (item["name"], item["count"], f"{item['mean']:.2f}", f"{item['median']:.2f}", f"{item['minimum']:.2f}", f"{item['maximum']:.2f}", f"{item['standard_deviation']:.2f}")
            for item in statistics
        ]
        if stat_rows:
            self._add_table(report, "Numeric Statistics", ("Column", "Count", "Mean", "Median", "Minimum", "Maximum", "Std. Deviation"), stat_rows)
        else:
            empty_frame = ttk.LabelFrame(report, text="Numeric Statistics", padding=10)
            empty_frame.pack(fill="x", pady=(0, 10))
            ttk.Label(empty_frame, text="No numeric columns were found in this dataset.").pack(anchor="w")

        self.status_text.set("Dataset analysis calculated from the loaded DataFrame.")

    def _add_table(self, parent, title, headings, rows):
        """Add a compact table to an analysis report."""
        frame = ttk.LabelFrame(parent, text=title, padding=8)
        frame.pack(fill="x", pady=(0, 10))
        tree = ttk.Treeview(frame, columns=headings, show="headings", height=min(max(len(rows), 1), 8))
        for heading in headings:
            tree.heading(heading, text=heading)
            tree.column(heading, width=125, minwidth=85, anchor="w")
        for row in rows:
            tree.insert("", "end", values=row)
        tree.pack(fill="x", expand=True)

    def show_insights(self):
        """Display rule-based observations generated from the current DataFrame."""
        if self.dataframe is None:
            messagebox.showwarning("No dataset", "Load a dataset before opening Insights.")
            return

        analyzer = DataAnalyzer(self.dataframe)
        insights = analyzer.generate_insights()
        self._clear_content()
        ttk.Label(self.content, text="AUTOMATIC INSIGHTS", font=("TkDefaultFont", 14, "bold")).pack(anchor="w", pady=(0, 8))

        text_frame = ttk.Frame(self.content)
        text_frame.pack(fill="both", expand=True)
        text = tk.Text(text_frame, wrap="word", padx=12, pady=12, font=("TkDefaultFont", 11))
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text.yview)
        text.configure(yscrollcommand=scrollbar.set)
        text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        section_titles = {
            "general": "GENERAL OBSERVATIONS",
            "sales": "SALES PERFORMANCE",
            "group": "GROUP PERFORMANCE",
            "date": "DATE INSIGHTS",
            "holiday": "HOLIDAY IMPACT",
            "correlation": "CORRELATION INSIGHTS",
        }
        for section, title in section_titles.items():
            if insights[section]:
                text.insert("end", f"{title}\n", "heading")
                for item in insights[section]:
                    text.insert("end", f"• {item}\n")
                text.insert("end", "\n")
        text.tag_configure("heading", font=("TkDefaultFont", 11, "bold"))
        text.configure(state="disabled")
        self.status_text.set("Automatic insights calculated from the loaded DataFrame.")

    def show_visualization(self):
        """Build the embedded chart-selection interface."""
        if self.dataframe is None:
            messagebox.showwarning("No dataset", "Load a dataset before opening Visualization.")
            return

        self._clear_content()
        ttk.Label(self.content, text="VISUALIZATION", font=("TkDefaultFont", 14, "bold")).pack(anchor="w", pady=(0, 8))
        analyzer = DataAnalyzer(self.dataframe)
        all_columns = [str(column) for column in self.dataframe.columns]
        numeric_columns = [str(column) for column in analyzer.numeric_columns()]
        date_column = analyzer.detect_date_column()
        sales_column = analyzer.detect_sales_column()
        group_column = analyzer.detect_group_column()

        recommendation = self._get_recommendation(analyzer)
        recommendation_frame = ttk.LabelFrame(self.content, text="Recommended Visualization", padding=8)
        recommendation_frame.pack(fill="x", pady=(0, 8))
        ttk.Label(recommendation_frame, text=recommendation, wraplength=900).pack(anchor="w")

        options = ttk.Frame(self.content)
        options.pack(fill="x", pady=(0, 8))
        ttk.Label(options, text="Chart Type:").grid(row=0, column=0, padx=(0, 6), pady=4, sticky="w")
        chart_type = ttk.Combobox(options, state="readonly", values=["Bar Chart", "Line Chart", "Scatter Plot", "Histogram"], width=18)
        chart_type.set("Bar Chart")
        chart_type.grid(row=0, column=1, padx=(0, 18), pady=4, sticky="w")
        ttk.Label(options, text="X-Axis / Column:").grid(row=0, column=2, padx=(0, 6), pady=4, sticky="w")
        x_choice = ttk.Combobox(options, state="readonly", values=all_columns, width=24)
        x_choice.grid(row=0, column=3, padx=(0, 18), pady=4, sticky="w")
        ttk.Label(options, text="Y-Axis:").grid(row=0, column=4, padx=(0, 6), pady=4, sticky="w")
        y_choice = ttk.Combobox(options, state="readonly", values=numeric_columns, width=24)
        y_choice.grid(row=0, column=5, pady=4, sticky="w")

        if group_column is not None:
            x_choice.set(str(group_column))
        elif date_column is not None:
            x_choice.set(str(date_column))
        elif all_columns:
            x_choice.set(all_columns[0])
        if sales_column is not None and str(sales_column) in numeric_columns:
            y_choice.set(str(sales_column))
        elif numeric_columns:
            y_choice.set(numeric_columns[0])

        figure = Figure(figsize=(8.5, 4.8), dpi=100)
        chart_canvas = FigureCanvasTkAgg(figure, master=self.content)
        chart_canvas.get_tk_widget().pack(fill="both", expand=True)

        def update_controls(*_):
            if chart_type.get() == "Histogram":
                y_choice.configure(state="disabled")
                x_choice.configure(values=numeric_columns)
                if x_choice.get() not in numeric_columns and numeric_columns:
                    x_choice.set(numeric_columns[0])
            elif chart_type.get() == "Scatter Plot":
                y_choice.configure(state="readonly")
                x_choice.configure(values=numeric_columns)
                if x_choice.get() not in numeric_columns and numeric_columns:
                    x_choice.set(numeric_columns[0])
            else:
                y_choice.configure(state="readonly")
                x_choice.configure(values=all_columns)

        def generate():
            selected_type = chart_type.get()
            x_column = x_choice.get()
            y_column = y_choice.get()
            if not x_column:
                messagebox.showerror("Invalid chart selection", "Select a column for the chart.")
                return
            if selected_type != "Histogram" and not y_column:
                messagebox.showerror("Invalid chart selection", "Select a numeric Y-axis column.")
                return
            if selected_type in {"Scatter Plot", "Histogram"} and selected_type == "Scatter Plot" and x_column not in numeric_columns:
                messagebox.showerror("Invalid chart selection", "Scatter plots require a numeric X-axis column.")
                return
            if selected_type != "Histogram" and y_column not in numeric_columns:
                messagebox.showerror("Invalid chart selection", "The Y-axis must be numeric for this chart type.")
                return
            try:
                create_chart(self.dataframe, selected_type, x_column, y_column, figure)
                chart_canvas.draw()
                self.status_text.set(f"{selected_type} generated from the loaded DataFrame.")
            except Exception as error:
                messagebox.showerror("Could not generate chart", str(error))

        def clear_chart():
            figure.clear()
            chart_canvas.draw()
            self.status_text.set("Chart cleared.")

        chart_type.bind("<<ComboboxSelected>>", update_controls)
        ttk.Button(options, text="Generate Chart", command=generate).grid(row=1, column=0, columnspan=2, pady=(8, 0), sticky="w")
        ttk.Button(options, text="Clear Chart", command=clear_chart).grid(row=1, column=2, columnspan=2, pady=(8, 0), sticky="w")
        update_controls()

    @staticmethod
    def _get_recommendation(analyzer):
        """Return a simple rule-based visualization recommendation."""
        sales = analyzer.detect_sales_column()
        date = analyzer.detect_date_column()
        group = analyzer.detect_group_column()
        numeric = analyzer.numeric_columns()
        if sales is not None and group is not None:
            return f"Bar chart — Compare {sales} by {group}"
        if sales is not None and date is not None:
            return f"Line chart — View {sales} trend over time"
        if sales is not None and len(numeric) > 1:
            other = next((column for column in numeric if column != sales), numeric[0])
            return f"Scatter plot — Examine the relationship between {sales} and {other}"
        if numeric:
            return f"Histogram — View the distribution of {numeric[0]}"
        return "Load numeric or categorical columns to receive a chart recommendation."


def main():
    root = tk.Tk()
    DataPilotApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
