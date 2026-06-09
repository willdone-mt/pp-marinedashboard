import pandas as pd
import numpy as np
import streamlit as st
from scipy.interpolate import griddata

# import
# input data
# data quality awal
# Jika file memiliki baris satuan di baris kedua, hapus baris pertama data (sesuai file contoh) dan namain kolom ulang
# konversi kolom penting di reDtype
# cek data kosong, duplikat
# reformat satuan dan besaran
# tambah kolom tahun, bulan, musim, tahun musim,

# Fungsi penentuan musim (sama dengan salinitas.ipynb)
def assign_season(month):
    if month in [12, 1, 2]:
        return 'Musim Barat'
    elif month in [3, 4, 5]:
        return 'Musim Peralihan 1'
    elif month in [6, 7, 8]:
        return 'Musim Timur'
    else:
        return 'Musim Peralihan 2'

import os
import pandas as pd
import streamlit as st

# 1. Get the absolute path of the directory containing this script (src/)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. Build the unbreakable absolute path to your default csv file
DEFAULT_PATH = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "data", "df_master.csv"))

# 3. Use the absolute path as your default argument value
@st.cache_data  # Highly recommended to speed up your Streamlit app
def load_data(pathfile=DEFAULT_PATH):
    required_cols = ['year_month', 'season', 'latitude', 'longitude', 'sss', 'analysed_sst', 'chlor_a']
    df = pd.read_csv(pathfile, usecols=required_cols)
    df['year_month'] = pd.to_datetime(df['year_month'])
    
    df = df.sort_values(by='year_month')
    df['Base_Year'] = df['year_month'].dt.year
    df['Month'] = df['year_month'].dt.month
    
    def calculate_season_year(row):
        if row['season'] == 'Musim Barat' and row['Month'] == 12:
            return row['Base_Year'] + 1
        return row['Base_Year']
    
    df['Season_Year'] = df.apply(calculate_season_year, axis=1)
    df['Year_Season'] = df['Season_Year'].astype(str) + " - " + df['season'].astype(str)
    
    return pd.DataFrame(df)
