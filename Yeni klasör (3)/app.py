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

# Sayfa başlığını Türkçe yaptık
st.set_page_config(page_title="Psikoloji Kulübü", page_icon="☕", layout="centered")

st.markdown("""
<style>
    .big-font { font-size:20px !important; }
    .stButton button { width: 100%; height: 60px; font-size: 20px; background-color: #FF4B4B; color: white; }
    /* Hata mesajı kutularını biraz daha estetik yapalım */
    .stAlert { font-size: 16px; }
</style>
""", unsafe_allow_html=True)

# Ana Başlık
st.markdown("<h2 style='text-align: center;'>☕ Psikoloji Kulübü İndirim Sistemi</h2>", unsafe_allow_html=True)

if 'giris_basarili' not in st.session_state:
    st.session_state['giris_basarili'] = False

# --- GİRİŞ EKRANI ---
if not st.session_state['giris_basarili']:
    # Bilgi mesajı Türkçe
    st.info("Lütfen sistemde kayıtlı telefon numaranızı giriniz.")
    
    with st.form("giris_formu"):
        # Input etiketi ve Buton Türkçe
        girilen_ham_no = st.text_input("Telefon Numaranız:", max_chars=15, placeholder="Örn: 5551234567")
        buton = st.form_submit_button("Doğrula ve Kod Al")
        
    if buton and girilen_ham_no:
        girilen_temiz_no = numarayi_temizle(girilen_ham_no)
        kayitli_numaralar = dosya_yukle()
        
        eslesme = False
        for kayit in kayitli_numaralar:
            if len(girilen_temiz_no) > 9 and len(kayit) > 9:
                if girilen_temiz_no[-10:] == kayit[-10:]:
                    eslesme = True
                    break
        
        if eslesme:
            if kilit_kontrol(girilen_temiz_no):
                st.session_state['giris_basarili'] = True
                st.session_state['giris_yapilan_no'] = girilen_temiz_no
                st.rerun()
            else:
                # Hata Mesajı 1 - Türkçe
                st.error("⛔ Bu numara şu an başka bir cihazda aktif! Lütfen 5 dakika bekleyin.")
        else:
            # Hata Mesajı 2 - Türkçe
            st.error("❌ Bu numara indirim listesinde bulunamadı.")

# --- KOD EKRANI (SENKRONİZE) ---
else:
    kilit_kontrol(st.session_state['giris_yapilan_no'])
    
    # Başarı Mesajı Türkçe
    st.success("✅ Doğrulama Başarılı!")
    
    # Yönerge Türkçe
    st.markdown("<h4 style='text-align: center;'>Bu kodu baristaya gösteriniz.</h4>", unsafe_allow_html=True)
    
    kod_kutusu = st.empty()
    cubuk_kutusu = st.empty()
    
    while True:
        # --- ZAMAN BAZLI KOD ÜRETİMİ ---
        simdi = time.time()
        zaman_blogu = int(simdi // KOD_YENILEME_SANIYE)
        
        random.seed(zaman_blogu)
        ortak_kod = random.randint(1000, 9999)
        
        gecen_sure = simdi % KOD_YENILEME_SANIYE
        kalan_yuzde = 1.0 - (gecen_sure / KOD_YENILEME_SANIYE)
        
        # Ekrana Bas
        kod_kutusu.markdown(
            f"""
            <div style="
                background-color: #2ecc71;
                color: white;
                padding: 30px;
                border-radius: 15px;
                text-align: center;
                font-size: 70px;
                font-weight: bold;
                font-family: monospace;
                letter-spacing: 5px;
                margin: 20px 0;
                border: 2px solid white;
                box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2);
            ">
                {ortak_kod}
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        cubuk_kutusu.progress(kalan_yuzde)
        
        time.sleep(0.1)
