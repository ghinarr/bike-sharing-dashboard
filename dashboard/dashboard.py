import os
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import streamlit as st
import numpy as np
from pandas.api.types import CategoricalDtype

#  PAGE CONFIG & THEME
st.set_page_config(
    page_title="🚲 Bike Sharing", page_icon="🚲", layout="wide", initial_sidebar_state="expanded"
)

st.markdown("""
<style>
/* Font */
html, body, [class*="css"] {font-family: 'Nunito', sans-serif;}

/* Background */
.stApp {background-color: #091425;}

/* Sidebar */
[data-testid="stSidebar"] {background-color: #163460; color: white;}

/* Metric box */
[data-testid="metric-container"] {background-color: #4da3ff; border-radius: 12px; padding: 15px;}

/* Tabs aktif */
[data-testid="stTabs"] button[aria-selected="true"] {color: #3b82f6;}

/* Card sederhana */
.info-card {background-color: #132f5b; border-left: 4px solid #4da3ff; padding: 12px; margin: 10px 0; border-radius: 10px; color: white;}

/* Judul section */
.section-title {font-weight: bold; color: #4da3ff; margin-top: 20px;}
</style>
""", unsafe_allow_html=True)

#  PLOT HELPERS
BG, AX_BG = "#f0f6ff", "#e8f2ff"
C_DARK, C_MID, C_MAIN = "#1a3a6e", "#2563eb", "#4da3ff"
PALETTE = [C_DARK, C_MID, C_MAIN, "#7ec8ff", "#b3d9ff", "#1e90ff"]

def style_ax(ax):
    ax.set_facecolor("#e8f2ff")
    for sp in ax.spines.values():
        sp.set_edgecolor("#b3cce8")
    ax.tick_params(colors="#0d2b5e", labelsize=9)
    ax.xaxis.label.set_color("#0d2b5e")
    ax.yaxis.label.set_color("#0d2b5e")
    ax.title.set_color("#0d2b5e")
    ax.grid(color="#c5daf5", linestyle="--", linewidth=0.5)

def make_fig(w=10, h=4):
    fig, ax = plt.subplots(figsize=(w, h))
    fig.patch.set_facecolor("#f0f6ff")
    style_ax(ax)
    return fig, ax

def make_fig2(w=13, h=4.5):
    fig, axes = plt.subplots(1, 2, figsize=(w, h))
    fig.patch.set_facecolor("#f0f6ff")
    for ax in axes:
        style_ax(ax)
    return fig, axes

def card(text): st.markdown(f'<div class="info-card">{text}</div>', unsafe_allow_html=True)
def sec(text): st.markdown(f'<div class="section-title">{text}</div>', unsafe_allow_html=True)

#  DATA LOADING
@st.cache_data
def load_data():
    BASE = os.path.dirname(os.path.abspath(__file__))
    day  = pd.read_csv(os.path.join(BASE, "day_clean.csv"))
    hour = pd.read_csv(os.path.join(BASE, "hour_clean.csv"))
    s_ord = CategoricalDtype(["Spring","Summer","Fall","Winter"], ordered=True)
    w_ord = CategoricalDtype(["Clear","Mist","Light Rain/Snow","Heavy Rain/Snow"], ordered=True)
    m_ord = CategoricalDtype(["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"], ordered=True)
    d_ord = CategoricalDtype(["Sun","Mon","Tue","Wed","Thu","Fri","Sat"], ordered=True)
    for df in [day, hour]:
        df["dteday"] = pd.to_datetime(df["dteday"])
        df["yr"] = df["yr"].astype(str)
        for col, dtype in [("season",s_ord),("weathersit",w_ord),("mnth",m_ord),("weekday",d_ord)]:
            if col in df.columns: df[col] = df[col].astype(dtype)
    if "hr" in hour.columns: hour["hr"] = hour["hr"].astype(int)
    day["temp_c"] = (day["temp"] * 41).round(1)
    day["day_type"] = day.apply(lambda r: "Libur" if r["holiday"]==1 else ("Kerja" if r["workingday"]==1 else "Weekend"), axis=1)
    return day, hour

try:
    day_df, hour_df = load_data()
except FileNotFoundError:
    st.error("❌ **day_clean.csv** atau **hour_clean.csv** tidak ditemukan di folder yang sama dengan dashboard.py")
    st.stop()

#  SIDEBAR FILTERS
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding:15px 0;'>
        <div style='font-size:40px;'>🚲</div>
        <div style='font-weight:700; color:#ffffff;'>BIKE SHARING</div>
        <div style='font-size:11px; color:#ffffff'>Analytics · 2011–2012</div>
    </div><hr>""", unsafe_allow_html=True)

    st.markdown("### 🎛️ Filter")
    yr_sel  = st.multiselect("📆 Tahun",  ["2011","2012"], default=["2011","2012"])

    season_options = ["Spring", "Summer", "Fall", "Winter"]
    sea_sel_raw = st.multiselect("🌿 Musim", options=["All Season"] + season_options, default=["All Season"])
    sea_sel = season_options if "All Season" in sea_sel_raw else sea_sel_raw
    if not sea_sel:
        sea_sel = season_options 

    weather_options = ["Clear","Mist","Light Rain/Snow", "Heavy Rain/Snow"]  
    wea_sel_raw = st.multiselect("☁️ Cuaca", options=["All Weathers"] + weather_options, default=["All Weathers"])
    wea_sel = weather_options if "All Weathers" in wea_sel_raw else wea_sel_raw
    if not wea_sel:
        wea_sel = weather_options

    min_d, max_d = day_df["dteday"].min().date(), day_df["dteday"].max().date()
    dr = st.date_input(label='Rentang Waktu', min_value=min_d, max_value=max_d, value=(min_d,max_d))
    s_date, e_date = (dr[0], dr[1]) if len(dr) == 2 else (min_d, max_d)

    st.markdown("---")
    hr_range = st.slider("⏰ Filter Jam", 0, 23, (0, 23))
    st.markdown("""<div style='font-size:11px; color:#ffffff; text-align:center;margin-top:16px;'>
        Ghina Roudlotul Jannah<br> Coding Camp 2026</div>""", unsafe_allow_html=True)

#  FILTER DATA
dm = day_df[
    (day_df["dteday"].dt.date >= s_date) & (day_df["dteday"].dt.date <= e_date) &
    (day_df["yr"].isin(yr_sel)) & (day_df["season"].isin(sea_sel)) &
    (day_df["weathersit"].isin(wea_sel))
].copy()

hm = hour_df[
    (hour_df["yr"].isin(yr_sel)) &
    (hour_df["hr"].between(hr_range[0], hr_range[1]))
].copy()

if dm.empty:
    st.warning("⚠️ Tidak ada data untuk filter yang dipilih."); st.stop()

#  HEADER
st.markdown("""
<div style='background:#163460; border:1px solid #2a5298; border-radius:16px; padding:20px 28px; margin-bottom:20px;'>
  <div style='font-size:1.8rem; font-weight:800; color:#e8f1ff;'>🚲 Bike Sharing Dashboard</div>
  <div style='color:#90b4e8; font-size:0.9rem; margin-top:4px;'>
    Bike Sharing · Washington D.C. · 2011–2012</div>
</div>""", unsafe_allow_html=True)

#  KPI METRICS
g = 0
if "2011" in yr_sel and "2012" in yr_sel:
    y11, y12 = dm[dm["yr"]=="2011"]["cnt"].sum(), dm[dm["yr"]=="2012"]["cnt"].sum()
    g = round((y12-y11)/y11*100, 1) if y11 > 0 else 0

c1,c2,c3,c4,c5 = st.columns(5)
c1.metric("🚲 Total Sewa",      f"{dm['cnt'].sum():,.0f}",      f"+{g}%" if g else None)
c2.metric("📅 Rata-rata/Hari",  f"{dm['cnt'].mean():,.0f}")
c3.metric("🏆 Hari Terbanyak",    f"{dm['cnt'].max():,.0f}")
c4.metric("👤 Casual",          f"{dm['casual'].sum():,.0f}")
c5.metric("🏢 Registered",      f"{dm['registered'].sum():,.0f}")

st.markdown("<br>", unsafe_allow_html=True)

# TABS
tab1, tab2, tab3, tab4 = st.tabs(["📈 Tren & Perbandingan", "🌿 Musim & Cuaca", "⏰ Jam & Hari", "🔍 Analisis Lanjutan"])

# TAB 1

with tab1:
    sec("Tren Penyewaan Bulanan")
    col1, col2 = st.columns([3,1])
    with col2:
        chart = st.radio("Tipe Chart", ["Line","Bar","Area"], key="t1c")
        split = st.checkbox("Casual vs Registered", key="t1s")

    dm["my"] = dm["dteday"].dt.to_period("M").astype(str)
    mdf = dm.groupby("my")[["cnt","casual","registered"]].sum().reset_index().sort_values("my")

    with col1: 
        fig, ax = make_fig(11, 4)
        if split:
            ax.plot(mdf["my"], mdf["registered"], color="#3b82f6", label="Registered")
            ax.plot(mdf["my"], mdf["casual"], color="#60a5fa", label="Casual")
            ax.fill_between(mdf["my"], mdf["registered"], alpha=0.2, color="#1a3a6e")
            ax.fill_between(mdf["my"], mdf["casual"], alpha=0.2, color="#4da3ff")
            ax.legend()
        else:
            if chart == "Bar":
                ax.bar(mdf["my"], mdf["cnt"], color="#3b82f6")
            else:
                ax.plot(mdf["my"], mdf["cnt"], color="#3b82f6")
                if chart == "Area":
                    ax.fill_between(mdf["my"], mdf["cnt"], alpha=0.2, color="#3b82f6")
        plt.xticks(rotation=45, ha="right", fontsize=8)
        ax.set_title("Total Penyewaan per Bulan")
        plt.tight_layout(); st.pyplot(fig); plt.close()
        best_month = mdf.loc[mdf["cnt"].idxmax(), "my"]; worst_month = mdf.loc[mdf["cnt"].idxmin(), "my"]; best_val = mdf["cnt"].max()
        card(f"💡 Puncak penyewaan terjadi pada <b>{best_month}</b> ({best_val:,.0f} unit). "f"Terendah pada <b>{worst_month}</b>.")

    sec("Perbandingan 2011 vs 2012")
    m_ord = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    cdf = dm.groupby(["mnth","yr"])["cnt"].sum().reset_index()
    fig, ax = make_fig(11, 4)
    x = np.arange(len(m_ord))
    w = 0.35
    for i, yr in enumerate(sorted(cdf["yr"].unique())):
        sub = cdf[cdf["yr"]==yr].set_index("mnth").reindex(m_ord)["cnt"].fillna(0)
        ax.bar(x + i*w, sub.values, w, label=yr, color=["#1a3a6e", "#4da3ff"][i])
    ax.set_xticks(x + w/2); ax.set_xticklabels(m_ord, fontsize=8)
    ax.legend(); ax.set_title("Penyewaan Bulanan: 2011 vs 2012")
    plt.tight_layout(); st.pyplot(fig); plt.close()
    if "2011" in yr_sel and "2012" in yr_sel:
        y11 = dm[dm["yr"]=="2011"]["cnt"].sum()
        y12 = dm[dm["yr"]=="2012"]["cnt"].sum()
        growth = round((y12-y11)/y11*100,1) if y11>0 else 0
        card(f"📈 Total 2011: <b>{y11:,.0f}</b> unit menuju 2012: <b>{y12:,.0f}</b> unit. "f"Pertumbuhan <b>{growth}%</b>.")

# TAB 2
with tab2:
    c1, c2 = st.columns(2)
    with c1:
        sec("Rata-rata per Musim")
        sdf = dm.groupby("season")[["cnt","casual","registered"]].mean().reset_index()
        fig, ax = make_fig(6, 4)
        x = np.arange(len(sdf)); w = 0.35
        ax.bar(x, sdf["registered"], w, label="Registered", color="#1a3a6e")
        ax.bar(x + w, sdf["casual"], w, label="Casual", color="#4da3ff")
        ax.set_xticks(x + w/2); ax.set_xticklabels(sdf["season"].astype(str))
        ax.legend(); ax.set_title("Rata-rata Penyewaan per Musim")
        plt.tight_layout(); st.pyplot(fig); plt.close()
        top_s = sdf.loc[sdf["cnt"].idxmax(), "season"]; low_s = sdf.loc[sdf["cnt"].idxmin(), "season"]; top_sv = sdf["cnt"].max(); low_sv = sdf["cnt"].min()
        card(f"🍂 Musim terbaik: <b>{top_s}</b> (~{top_sv:,.0f}/hari). "f"Terendah: <b>{low_s}</b> (~{low_sv:,.0f}/hari).")

    with c2:
        sec("Rata-rata per Kondisi Cuaca")
        wdf = dm.groupby("weathersit")["cnt"].mean().reset_index()
        fig, ax = make_fig(6, 4)
        colors = ["#4da3ff"]
        bars = ax.bar(wdf["weathersit"].astype(str), wdf["cnt"], color=colors[:len(wdf)])
        for b in bars:
            ax.text(b.get_x() + b.get_width()/2, b.get_height() + 20, f"{b.get_height():.0f}",
                    ha="center", fontsize=9, color="#1e3a8a")
        ax.set_title("Rata-rata per Kondisi Cuaca")
        plt.tight_layout(); st.pyplot(fig); plt.close()
        top_w = wdf.loc[wdf["cnt"].idxmax(), "weathersit"]; low_w = wdf.loc[wdf["cnt"].idxmin(), "weathersit"]; top_wv = wdf["cnt"].max(); low_wv = wdf["cnt"].min(); drop = round((1 - low_wv/top_wv)*100, 1)
        card(f"☀️ <b>{top_w}</b>: ~{top_wv:,.0f}/hari. "f"<b>{low_w}</b> turun <b>{drop}%</b> menjadi ~{low_wv:,.0f}/hari.")
        
    sec("Heatmap Musim × Cuaca")
    pivot = dm.groupby(["season","weathersit"])["cnt"].mean().unstack(fill_value=0)
    fig, ax = make_fig(12, 3.5)
    sns.heatmap(pivot, cmap="Blues", annot=True, fmt=".0f", linewidths=0.5, ax=ax)
    ax.set_title("Rata-rata Penyewaan: Musim × Cuaca")
    plt.tight_layout(); st.pyplot(fig); plt.close()
    ax.set_facecolor(AX_BG)
    best_combo = pivot.stack().idxmax(); best_combo_val = pivot.stack().max()
    card(f"🔥 Kombinasi terbaik: musim <b>{best_combo[0]}</b> + cuaca <b>{best_combo[1]}</b> "f"(~{best_combo_val:,.0f} unit/hari).")
    
# TAB 3
with tab3:
    sec("Pola Penyewaan per Jam")
    col1, col2 = st.columns([3,1])
    with col2:
        day_f  = st.selectbox("Tipe Hari", ["Semua","Hari Kerja","Weekend"], key="t3d")
        user_f = st.radio("Pengguna", ["Total","Casual","Registered"], key="t3u")
    hm2 = hm.copy()
    if day_f == "Hari Kerja": hm2 = hm2[hm2["workingday"]==1]
    elif day_f == "Weekend":  hm2 = hm2[hm2["workingday"]==0]
    ucol = {"Total":"cnt","Casual":"casual","Registered":"registered"}[user_f]
    hdf  = hm2.groupby("hr")[ucol].mean().reset_index()

    with col1:
        fig, ax = make_fig(10, 4)
        ax.plot(hdf["hr"], hdf[ucol], color="#3b82f6", marker="o")
        ax.fill_between(hdf["hr"], hdf[ucol], alpha=0.2, color="#3b82f6")
        if not hdf.empty:
            top2 = hdf.nlargest(2, ucol)
            ax.scatter(top2["hr"], top2[ucol], color="#1d4ed8", s=60)
        ax.set_xticks(range(0,24,2)); ax.set_xlabel("Jam"); ax.set_ylabel("Rata-rata")
        ax.set_title(f"Rata-rata Penyewaan per Jam — {user_f} ({day_f})")
        plt.tight_layout(); st.pyplot(fig); plt.close()
        if not hdf.empty:
            top2 = hdf.nlargest(2, ucol)
            jam1 = int(top2.iloc[0]["hr"]); val1 = top2.iloc[0][ucol]; jam2 = int(top2.iloc[1]["hr"]); val2 = top2.iloc[1][ucol]
            card(f"⏰ Puncak pertama: <b>pukul {jam1:02d}:00</b> (~{val1:,.0f}/jam). "f"Puncak kedua: <b>pukul {jam2:02d}:00</b> (~{val2:,.0f}/jam).")

    sec("Pola per Hari dalam Seminggu")
    d_ord2 = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"]
    wdf2 = dm.groupby("weekday")[["cnt","casual","registered"]].mean().reset_index()
    wdf2["weekday"] = pd.Categorical(wdf2["weekday"].astype(str), categories=d_ord2, ordered=True)
    wdf2 = wdf2.sort_values("weekday")
    fig, axes = make_fig2(13, 4)
    # Bar total 
    colors = [ "#2c62b9"]
    axes[0].bar(wdf2["weekday"].astype(str), wdf2["cnt"], color=colors[:len(wdf2)])
    axes[0].set_title("Total per Hari")
    # Stacked bar 
    axes[1].bar(wdf2["weekday"].astype(str), wdf2["registered"], label="Registered", color="#1a3a6e")
    axes[1].bar(wdf2["weekday"].astype(str), wdf2["casual"], bottom=wdf2["registered"], label="Casual", color="#4da3ff")
    axes[1].legend()
    axes[1].set_title("Casual vs Registered per Hari")
    plt.tight_layout(); st.pyplot(fig); plt.close()
    top_day = wdf2.loc[wdf2["cnt"].idxmax(), "weekday"]
    low_day = wdf2.loc[wdf2["cnt"].idxmin(), "weekday"]
    top_dv  = wdf2["cnt"].max()
    low_dv  = wdf2["cnt"].min()
    card(f"📅 Hari tertinggi: <b>{top_day}</b> (~{top_dv:,.0f}/hari). "f"Terendah: <b>{low_day}</b> (~{low_dv:,.0f}/hari).")

    sec("Heatmap Jam × Hari")
    h_ord = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
    if not hm.empty:
        pivot2 = hm.groupby(["weekday","hr"])["cnt"].mean().unstack(fill_value=0)
        pivot2.index = pivot2.index.astype(str)
        pivot2 = pivot2.reindex(h_ord)
        fig, ax = make_fig(14, 4)
        sns.heatmap(pivot2, cmap="Blues",ax=ax)
        ax.set_title("Intensitas Penyewaan: Jam × Hari")
        plt.tight_layout(); st.pyplot(fig); plt.close()
        card("🔥 Intensitas tertinggi terjadi pada <b>hari kerja Selasa–Kamis pukul 17:00–18:00</b>." "Weekend lebih merata di siang hari (10:00–16:00).")

# TAB 4
with tab4:
    c1, c2 = st.columns(2)
    with c1:
        sec("Distribusi Penyewaan Harian")
        fig, ax = make_fig(6, 4)
        ax.hist(dm["cnt"], bins=30, color="#3b82f6", alpha=0.8)
        ax.axvline(dm["cnt"].mean(), color="#1d4ed8", ls="--", label="Mean")
        ax.axvline(dm["cnt"].median(), color="#60a5fa", ls="--", label="Median")
        ax.legend()
        ax.set_title("Distribusi Penyewaan Harian")
        plt.tight_layout(); st.pyplot(fig); plt.close()
        mean_val = dm["cnt"].mean(); median_val = dm["cnt"].median()
        card(f"📊 Rata-rata: <b>{mean_val:,.0f}</b>/hari. "f"Median: <b>{median_val:,.0f}</b>/hari. "f"Distribusi <i>right-skewed</i> — ada hari dengan penyewaan sangat tinggi.")
        
    with c2:
        sec("Segmentasi Tipe Hari")
        dtdf = dm.groupby("day_type")["cnt"].agg(["mean","max"]).reset_index()
        fig, ax = make_fig(6, 4)
        colors = ["#1d4ed8"]
        bars = ax.bar(dtdf["day_type"], dtdf["mean"], color=colors[:len(dtdf)])
        for b in bars:
            ax.text(b.get_x()+b.get_width()/2, b.get_height()+20, f"{b.get_height():.0f}",
                    ha="center", fontsize=9, color="#1e3a8a")
        ax.set_title("Rata-rata per Tipe Hari")
        plt.tight_layout(); st.pyplot(fig); plt.close()
        top_dt = dtdf.loc[dtdf["mean"].idxmax(), "day_type"]
        low_dt = dtdf.loc[dtdf["mean"].idxmin(), "day_type"]; top_dtv = dtdf["mean"].max(); low_dtv = dtdf["mean"].min()
        card(f"🏢 <b>{top_dt}</b> tertinggi (~{top_dtv:,.0f}/hari). "f"<b>{low_dt}</b> terendah (~{low_dtv:,.0f}/hari).")

    sec("Korelasi Suhu vs Penyewaan")
    col1, col2 = st.columns([3,1])
    with col2:
        clr_by = st.selectbox("Warnai berdasarkan", ["season","weathersit","yr"], key="sc")
        bins_n = st.slider("Bin suhu", 4, 10, 6, key="tb")
    with col1:
        fig, ax = make_fig(10, 4)
        cats = sorted(dm[clr_by].astype(str).unique())
        blues = ["#04133B", "#F11772", "#3b82f6", "#023572", "#93c5fd"]
        for i, cat in enumerate(cats):
            sub = dm[dm[clr_by].astype(str)==cat]
            ax.scatter(sub["temp_c"], sub["cnt"], alpha=0.6, s=20,
                       color=blues[i % len(blues)], label=cat)
        z = np.polyfit(dm["temp_c"], dm["cnt"], 1)
        p = np.poly1d(z)
        xs = np.linspace(dm["temp_c"].min(), dm["temp_c"].max(), 100)
        ax.plot(xs, p(xs), color="#1e3a8a", lw=2, ls="--", label="Trend")
        ax.legend()
        ax.set_xlabel("Suhu (°C)"); ax.set_ylabel("Jumlah Penyewaan")
        ax.set_title(f"Suhu vs Penyewaan (warna: {clr_by})")
        plt.tight_layout(); st.pyplot(fig); plt.close()
        corr = dm["temp_c"].corr(dm["cnt"]).round(2)
        opt_temp = dm.groupby(pd.cut(dm["temp_c"], bins=5))["cnt"].mean().idxmax()

    sec("Rata-rata Penyewaan per Rentang Suhu")
    dm2 = dm.copy()
    dm2["temp_bin"] = pd.cut(dm2["temp_c"], bins=bins_n)
    tgdf = dm2.groupby("temp_bin")["cnt"].mean().reset_index()
    tgdf["label"] = tgdf["temp_bin"].astype(str)
    fig, ax = make_fig(11, 3.5)
    colors = ["#2563eb"]
    ax.bar(tgdf["label"], tgdf["cnt"], color=colors[:len(tgdf)])
    ax.set_xlabel("Rentang Suhu (°C)"); ax.set_title(f"Penyewaan per Bin Suhu ({bins_n} bin)")
    plt.xticks(rotation=30, ha="right"); plt.tight_layout(); st.pyplot(fig); plt.close()

#  FOOTER
st.markdown("---")
st.caption("🚲 Bike Sharing Dashboard · Ghina Roudlotul Jannah · Coding Camp 2026")
