from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st

st.set_page_config(page_title="Dashboard Kualitas Udara Beijing", layout="wide")
sns.set_style("whitegrid")

BASE_DIR = Path(__file__).parent
SEASON_ORDER = ["Spring", "Summer", "Autumn", "Winter"]
KATEGORI_ORDER = [
    "Baik",
    "Sedang",
    "Tidak Sehat (Sensitif)",
    "Tidak Sehat",
    "Sangat Tidak Sehat",
    "Berbahaya",
]
AMBANG = 75


@st.cache_data
def load_data():
    df = pd.read_csv(BASE_DIR / "all_data.csv", parse_dates=["datetime"])
    geo = pd.read_csv(BASE_DIR / "station_geo.csv")[["station", "lat", "lon"]]
    return df, geo


df, geo = load_data()

# ---------------- Sidebar (filter) ----------------
st.sidebar.header("Filter Data")

semua_stasiun = sorted(df["station"].unique())
pilih_stasiun = st.sidebar.multiselect("Stasiun", semua_stasiun, default=semua_stasiun)

pilih_musim = st.sidebar.multiselect("Musim", SEASON_ORDER, default=SEASON_ORDER)

tgl_min = df["datetime"].min().date()
tgl_max = df["datetime"].max().date()
rentang = st.sidebar.date_input(
    "Rentang tanggal", value=(tgl_min, tgl_max), min_value=tgl_min, max_value=tgl_max
)

if len(rentang) != 2:
    st.info("Pilih tanggal awal dan tanggal akhir pada filter di sebelah kiri.")
    st.stop()

mulai, akhir = pd.to_datetime(rentang[0]), pd.to_datetime(rentang[1]) + pd.Timedelta(days=1)

data = df[
    df["station"].isin(pilih_stasiun)
    & df["season"].isin(pilih_musim)
    & (df["datetime"] >= mulai)
    & (df["datetime"] < akhir)
]

if data.empty:
    st.warning("Tidak ada data untuk filter yang dipilih. Ubah filter di sebelah kiri.")
    st.stop()

# ---------------- Header ----------------
st.title("Dashboard Kualitas Udara Beijing (PM2.5)")
st.caption(
    "Data: Beijing Multi-Site Air Quality, 12 stasiun, Maret 2013 sampai Februari 2017. "
    "Nilai PM2.5 dalam µg/m³."
)

# ---------------- Ringkasan ----------------
rata_stasiun = data.groupby("station")["PM2.5"].mean().sort_values(ascending=False)
rata_musim = data.groupby("season")["PM2.5"].mean()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Rata-rata PM2.5", f"{data['PM2.5'].mean():.1f} µg/m³")
c2.metric("Stasiun tertinggi", rata_stasiun.index[0], f"{rata_stasiun.iloc[0]:.1f} µg/m³", delta_color="off")
c3.metric("Musim tertinggi", rata_musim.idxmax(), f"{rata_musim.max():.1f} µg/m³", delta_color="off")
c4.metric(f"Jam di atas {AMBANG} µg/m³", f"{(data['PM2.5'] > AMBANG).mean() * 100:.1f}%")

st.caption(
    "Catatan: data 2013 mulai Maret dan data 2017 hanya Januari-Februari, "
    "jadi kedua tahun ini tidak bisa dibandingkan langsung dengan 2014-2016."
)

tab1, tab2, tab3, tab4 = st.tabs(
    ["Pertanyaan 1: Antarstasiun", "Pertanyaan 2: Antarmusim", "Tren & Pola", "Analisis Lanjutan"]
)

# ---------------- Tab 1 ----------------
with tab1:
    st.subheader("Stasiun mana yang rata-rata PM2.5-nya tertinggi dan terendah?")

    fig, ax = plt.subplots(figsize=(11, 5))
    sns.barplot(x=rata_stasiun.index, y=rata_stasiun.values, color="steelblue", ax=ax)
    for i, v in enumerate(rata_stasiun.values):
        ax.text(i, v + 1, f"{v:.1f}", ha="center", fontsize=9)
    ax.set_xlabel("Stasiun")
    ax.set_ylabel("Rata-rata PM2.5 (µg/m³)")
    ax.set_title("Rata-rata PM2.5 per Stasiun (Tertinggi ke Terendah)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    st.pyplot(fig)

    if len(rata_stasiun) >= 2:
        selisih = (rata_stasiun.max() - rata_stasiun.min()) / rata_stasiun.min() * 100
        st.write(
            f"**{rata_stasiun.index[0]}** paling tinggi ({rata_stasiun.iloc[0]:.1f} µg/m³) dan "
            f"**{rata_stasiun.index[-1]}** paling rendah ({rata_stasiun.iloc[-1]:.1f} µg/m³). "
            f"Selisihnya sekitar **{selisih:.1f}%**."
        )
        st.caption(
            "Selisih antarstasiun relatif kecil dibanding variasi PM2.5 per jam, "
            "jadi semua stasiun tetap menghadapi risiko polusi."
        )
    else:
        st.info("Pilih minimal 2 stasiun untuk melihat selisih antarstasiun.")

# ---------------- Tab 2 ----------------
with tab2:
    st.subheader("Musim apa yang rata-rata PM2.5-nya tertinggi, dan berapa persen jam di atas ambang?")

    stat_musim = data.groupby("season").agg(
        rata2=("PM2.5", "mean"),
        pct_di_atas=("PM2.5", lambda x: (x > AMBANG).mean() * 100),
    )
    stat_musim = stat_musim.reindex([s for s in SEASON_ORDER if s in stat_musim.index]).round(1)

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    sns.barplot(x=stat_musim.index, y=stat_musim["rata2"], color="steelblue", ax=axes[0])
    for i, v in enumerate(stat_musim["rata2"]):
        axes[0].text(i, v + 1, f"{v}", ha="center")
    axes[0].axhline(AMBANG, color="red", linestyle="--", label=f"Ambang {AMBANG} µg/m³")
    axes[0].set_title("Rata-rata PM2.5 per Musim")
    axes[0].set_xlabel("Musim")
    axes[0].set_ylabel("Rata-rata PM2.5 (µg/m³)")
    axes[0].legend()

    sns.barplot(x=stat_musim.index, y=stat_musim["pct_di_atas"], color="indianred", ax=axes[1])
    for i, v in enumerate(stat_musim["pct_di_atas"]):
        axes[1].text(i, v + 0.5, f"{v}%", ha="center")
    axes[1].set_title(f"Persentase Jam di Atas {AMBANG} µg/m³")
    axes[1].set_xlabel("Musim")
    axes[1].set_ylabel("Persentase jam pengamatan (%)")
    plt.tight_layout()
    st.pyplot(fig)

    if len(stat_musim) >= 2:
        selisih = (stat_musim["rata2"].max() - stat_musim["rata2"].min()) / stat_musim["rata2"].min() * 100
        st.write(
            f"Musim **{stat_musim['rata2'].idxmax()}** paling tinggi ({stat_musim['rata2'].max()} µg/m³), "
            f"sekitar **{selisih:.1f}%** lebih tinggi daripada musim **{stat_musim['rata2'].idxmin()}** "
            f"({stat_musim['rata2'].min()} µg/m³)."
        )
    else:
        st.info("Pilih minimal 2 musim untuk melihat perbandingan antarmusim.")

# ---------------- Tab 3 ----------------
with tab3:
    st.subheader("Tren bulanan")
    bulanan = data.set_index("datetime")["PM2.5"].resample("MS").mean().dropna().reset_index()

    fig, ax = plt.subplots(figsize=(13, 4.5))
    ax.plot(bulanan["datetime"], bulanan["PM2.5"], marker="o", markersize=3)
    ax.axhline(AMBANG, color="red", linestyle="--", label=f"Ambang {AMBANG} µg/m³")
    ax.set_xlabel("Tahun-Bulan")
    ax.set_ylabel("Rata-rata PM2.5 (µg/m³)")
    ax.set_title("Tren Rata-rata PM2.5 Bulanan")
    ax.legend()
    plt.tight_layout()
    st.pyplot(fig)

    st.subheader("Pola berdasarkan jam")
    per_jam = data.groupby("hour")["PM2.5"].mean()

    fig, ax = plt.subplots(figsize=(13, 4))
    ax.plot(per_jam.index, per_jam.values, marker="o")
    ax.set_xticks(range(0, 24))
    ax.set_xlabel("Jam")
    ax.set_ylabel("Rata-rata PM2.5 (µg/m³)")
    ax.set_title("Rata-rata PM2.5 Berdasarkan Jam")
    plt.tight_layout()
    st.pyplot(fig)

# ---------------- Tab 4 ----------------
with tab4:
    st.subheader("Pengelompokan tingkat PM2.5 (binning)")
    kat = (
        data["kategori"].value_counts(normalize=True).reindex(KATEGORI_ORDER).fillna(0) * 100
    ).round(1)

    fig, ax = plt.subplots(figsize=(10, 4.5))
    sns.barplot(x=kat.index, y=kat.values, color="steelblue", ax=ax)
    for i, v in enumerate(kat.values):
        ax.text(i, v + 0.5, f"{v}%", ha="center")
    ax.set_xlabel("Kategori PM2.5")
    ax.set_ylabel("Persentase jam pengamatan (%)")
    ax.set_title("Distribusi Jam Pengamatan per Kategori PM2.5")
    plt.xticks(rotation=20)
    plt.tight_layout()
    st.pyplot(fig)
    st.caption(
        "Batas kategori: Baik (sampai 35), Sedang (35-75), Tidak Sehat untuk Kelompok Sensitif (75-115), "
        "Tidak Sehat (115-150), Sangat Tidak Sehat (150-250), Berbahaya (di atas 250) µg/m³. "
        "Ini pendekatan pada data per jam, bukan perhitungan AQI resmi."
    )

    st.subheader("Sebaran rata-rata PM2.5 per stasiun (geospatial)")
    peta = rata_stasiun.reset_index().rename(columns={"PM2.5": "pm25"}).merge(geo, on="station")

    fig, ax = plt.subplots(figsize=(10, 7))
    ukuran = (peta["pm25"] - peta["pm25"].min()) * 15 + 150
    sc = ax.scatter(
        peta["lon"], peta["lat"], s=ukuran, c=peta["pm25"],
        cmap="YlOrRd", edgecolor="black", alpha=0.85,
    )
    offset = {
        "Wanshouxigong": (-15, -22),
        "Tiantan": (12, -22),
        "Dongsi": (-8, 14),
        "Nongzhanguan": (14, 8),
        "Aotizhongxin": (-10, 14),
        "Guanyuan": (-45, -22),
    }
    for _, r in peta.iterrows():
        dx, dy = offset.get(r["station"], (12, 8))
        ax.annotate(
            f"{r['station']}\n{r['pm25']:.1f}", (r["lon"], r["lat"]),
            xytext=(dx, dy), textcoords="offset points", fontsize=8,
        )
    fig.colorbar(sc, ax=ax, label="Rata-rata PM2.5 (µg/m³)")
    ax.set_xlabel("Bujur")
    ax.set_ylabel("Lintang")
    ax.set_title("Sebaran Rata-rata PM2.5 per Stasiun di Beijing")
    ax.grid(alpha=0.3)
    plt.tight_layout()
    st.pyplot(fig)
    st.caption("Koordinat stasiun adalah perkiraan.")
