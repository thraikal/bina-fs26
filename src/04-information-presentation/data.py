import io
import sys
from pathlib import Path

import pandas as pd
import requests
import certifi

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT / "src"))

from utils.fetch_cantons import load_cantons_geojson

cantons = load_cantons_geojson(ROOT / "data/dashboard")

_response = requests.get(
    "https://raw.githubusercontent.com/plotly/datasets/master/gapminder_unfiltered.csv",
    timeout=60, verify=certifi.where(),
)
_response.raise_for_status()
df_gapminder = pd.read_csv(io.StringIO(_response.text))

_df_costs_raw = pd.read_csv(ROOT / "data/processed/gesundheitskosten.csv")
_df_pop_raw = pd.read_csv(ROOT / "data/processed/bevoelkerung.csv")

_df_costs_canton = (
    _df_costs_raw[
        (_df_costs_raw['age'] == 'Total') & (_df_costs_raw['cantons'] != 'Total')
    ][['year', 'cantons', 'costs_chf']]
    .rename(columns={'cantons': 'canton'})
)
_df_pop_canton = (
    _df_pop_raw[
        (_df_pop_raw['age_label'] == 'Alter - Total') & (_df_pop_raw['canton'] != 'Schweiz')
    ][['year', 'canton', 'population']]
)

df_per_person = (
    _df_costs_canton.merge(_df_pop_canton, on=['year', 'canton'])
    .assign(cost_per_capita=lambda d: d['costs_chf'] / d['population'])
)
YEARS = sorted(df_per_person['year'].unique())

_df_66_raw = pd.read_csv(ROOT / "data/processed/bevoelkerung_66_share.csv")
_df_kantone = pd.read_csv(ROOT / "data/processed/kantone.csv")

df_aging = (
    df_per_person[['year', 'canton', 'cost_per_capita']]
    .merge(
        _df_66_raw[_df_66_raw['canton'] != 'Schweiz'][['year', 'canton', 'population_share_66_plus']],
        on=['year', 'canton'],
    )
    .merge(_df_kantone, on='canton')
    .assign(share_pct=lambda d: d['population_share_66_plus'] * 100)
)
SQ3_YEARS = sorted(df_aging['year'].unique())

df_aging_ch = (
    _df_costs_raw[(_df_costs_raw['age'] == 'Total') & (_df_costs_raw['cantons'] == 'Total')][['year', 'costs_chf']]
    .merge(
        _df_pop_raw[(_df_pop_raw['age_label'] == 'Alter - Total') & (_df_pop_raw['canton'] == 'Schweiz')][['year', 'population']],
        on='year',
    )
    .assign(cost_per_capita=lambda d: d['costs_chf'] / d['population'])
    .merge(_df_66_raw[_df_66_raw['canton'] == 'Schweiz'][['year', 'population_share_66_plus']], on='year')
    .assign(share_pct=lambda d: d['population_share_66_plus'] * 100)
)[['year', 'cost_per_capita', 'share_pct']].sort_values('year')

df_analysis_panel = pd.read_csv(ROOT / "data/processed/analysis_panel.csv")
df_manager_priorities = pd.read_csv(ROOT / "data/processed/manager_priorities.csv")
