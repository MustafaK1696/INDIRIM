import streamlit as st
import pandas as pd
import random
import time
import os
import json
from datetime import datetime

# --- AYARLAR ---
KILIT_SURESI_DAKIKA = 5        
KOD_YENILEME_SANIYE = 10       
DOSYA_ADI = "whitelist_telefonlar.csv"
KILIT_DOSYASI = "aktif_oturumlar.json"

# --- YARDIMCI FONKSİYONLAR ---

def dosya_yolunu_bul(dosya_ismi):
    """Dosyanın tam yolunu bulur (Klasör hatasını çözer)"""
    mevcut_klasor = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(mevcut_klasor, dosya_ismi)

def numarayi_temizle(numara):
    if pd.isna(numara):
        return ""
    return ''.join(filter(str.isdigit, str(numara)))

def dosya_yukle():
    """CSV dosyasını tam yolu bularak okur"""
    tam_dosya_yolu = dosya_yolunu_bul(DOSYA_ADI)
    df = None
    
    # Farklı formatları dene
    denemeler = [
        {'encoding': 'utf-8', 'sep': ','},
        {'encoding': 'utf-16', 'sep': '\t'}, 
        {'encoding': 'utf-16', 'sep': ','},
        {'encoding': 'latin-1', 'sep': ','},
        {'encoding': 'cp1254', 'sep': ','}
    ]

    for ayar in denemeler:
        try:
            df = pd.read_csv(tam_dosya_yolu, encoding=ayar['encoding'], sep=ayar['sep'])
            if len(df.columns) > 0:
                break 
        except:
            continue

    if df is None:
        st.error(f"Dosya bulunamadı! Aranan yer: {tam_dosya_yolu}")
        return []

    try:
        # Sütun bulma
        hedef_sutun = None
        for col in df.columns:
            col_lower = str(col).lower()
            if any(x in col_lower for x in ['phone', 'telefon', 'mobil', 'value', 'numara', 'contact']):
                hedef_sutun = col
                break
        
        if hedef_sutun is None:
            hedef_sutun = df.columns[0]

        temiz_liste = df[hedef_sutun].astype(str).apply(numarayi_temizle).tolist()
        return [no for no in temiz_liste if len(no) > 5]
        
    except Exception as e:
        st.error(f"Veri hatası: {e}")
        return []

def kilit_kontrol(kullanici_no):
    kilit_yolu = dosya_yolunu_bul(KILIT_DOSYASI)
    
    if not os.path.exists(kilit_yolu):
        with open(kilit_yolu, 'w') as f:
            json.dump({}, f)
    
    try:
        with open(kilit_yolu, 'r') as f:
            oturumlar = json.load(f)
    except:
        oturumlar = {}
    
    simdi = datetime.now().timestamp()
    guncel_oturumlar = {k: v for k, v in oturumlar.items() if v > simdi}
    
    durum = False
    
    if kullanici_no in guncel_oturumlar:
        if 'giris_yapilan_no' in st.session_state and st.session_state['giris_yapilan_no'] == kullanici_no:
            guncel_oturumlar[kullanici_no] = simdi + (KILIT_SURESI_DAKIKA * 60)
            durum = True
        else:
            durum = False 
    else:
        guncel_oturumlar[kullanici_no] = simdi + (KILIT_SURESI_DAKIKA * 60)
        durum = True
        
    with open(kilit_yolu, 'w') as f:
        json.dump(guncel_oturumlar, f)
        
    return durum

# --- ARAYÜZ ---

# Sayfa başlığını da güncelledik
st.set_page_config(page_title="Psikoloji Kulübü", page_icon="☕", layout="centered")

st.markdown("""
<style>
    .big-font { font-size:20px !important; }
    .stButton button { width: 100%; height: 60px; font-size: 20px; background-color: #FF4B4B; color: white; }
</style>
""", unsafe_allow_html=True)

# İSTENİLEN DEĞİŞİKLİK 1: Başlık Güncellendi
st.markdown("<h2 style='text-align: center;'>☕ Psikoloji Kulübü İndirim Sistemi</h2>", unsafe_allow_html=True)

if 'giris_basarili' not in st.session_state:
    st.session_state['giris_basarili'] = False

# --- GİRİŞ EKRANI
