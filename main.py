"""M10 PMLS Assignment 1: skin clinic campaign analysis served with FastAPI."""
from pathlib import Path

import pandas as pd
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse

DATA_PATH = Path(__file__).parent / "skin_clinic_campaign.csv"

app = FastAPI(title="Skin Clinic Campaign Analysis")


def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    df["Responded"] = (df["Response_to_Campaign"] == "Yes").astype(int)
    df["Product_Usage"] = pd.cut(
        df["Unique_Products_Purchased"],
        bins=[0, 4, 8, float("inf")],
        labels=["1-4", "5-8", ">8"],
    ).astype(str)
    return df


def response_table(df: pd.DataFrame, column: str, label: str, order: list[str]) -> pd.DataFrame:
    """Return customers, responders and response rate (%) for each segment."""
    table = (
        df.groupby(column)["Responded"]
        .agg(Customers="count", Responders="sum")
        .reindex(order)
        .reset_index()
        .rename(columns={column: label})
    )
    table["Response Rate (%)"] = (table["Responders"] / table["Customers"] * 100).round(2)
    return table


def build_tables() -> dict[str, pd.DataFrame]:
    df = load_data()
    return {
        "1. Gender vs Campaign Response": response_table(
            df, "Gender", "Gender", ["Male", "Female"]
        ),
        "2. Age Group vs Campaign Response": response_table(
            df, "AgeGroup", "Age Group", ["<30", "30-50", ">50"]
        ),
        "3. Purchase in Last Quarter vs Campaign Response": response_table(
            df, "Purchase_Last_Quarter", "Purchase in Last Quarter", ["Yes", "No"]
        ),
        "4. Product Usage vs Campaign Response": response_table(
            df, "Product_Usage", "Unique Products Purchased", ["1-4", "5-8", ">8"]
        ),
    }


PAGE_STYLE = """
body { font-family: Arial, sans-serif; margin: 32px auto; max-width: 720px; padding: 0 16px; color: #222; }
h1 { font-size: 24px; }
h2 { font-size: 17px; margin-top: 32px; }
table { border-collapse: collapse; width: 100%; }
th, td { border: 1px solid #ccc; padding: 8px 12px; text-align: left; }
th { background: #f0f0f0; }
"""


@app.get("/", include_in_schema=False)
def home():
    return RedirectResponse(url="/campaign-analysis")


@app.get("/campaign-analysis", response_class=HTMLResponse)
def campaign_analysis() -> str:
    sections = "".join(
        f"<h2>{title}</h2>"
        + table.to_html(index=False, border=0, float_format="{:.2f}".format)
        for title, table in build_tables().items()
    )
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        f"<title>Campaign Analysis</title><style>{PAGE_STYLE}</style></head>"
        f"<body><h1>Skin Clinic Campaign Analysis</h1>{sections}</body></html>"
    )
