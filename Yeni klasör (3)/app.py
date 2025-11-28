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
VERI_DOSYASI = "Whatsapp-Group-Contacts.csv" 
KILIT_DOSYASI = "aktif_oturumlar.json"

# --- YARDIMCI FONKSİYONLAR ---

def numarayi_temizle(numara):
    """
    Telefon numaralarındaki harf, boşluk, +, - gibi işaretleri temizler.
    Sadece rakamları bırakır.
    """
    if pd.isna(numara):
        return ""
    # Sadece rakamları al
    temiz = ''.join(filter(str.isdigit, str(numara)))
    return temiz

def dosya_yukle():
    """
    CSV dosyasını okur. Ayırıcıyı (virgül, noktalı virgül vb.) OTOMATİK algılar.
    """
    df = None
    
    # Python motoru 'sep=None' ile ayırıcıyı kendi tahmin eder
    try:
        df = pd.read_csv(VERI_DOSYASI, sep=None, engine='python', encoding='utf-8')
    except:
        try:
            # UTF-8 olmazsa UTF-16 (WhatsApp standardı) dene
            df = pd.read_csv(VERI_DOSYASI, sep=None, engine='python', encoding='utf-16')
        except Exception as e:
            st.error(f"Dosya okuma hatası: {e}. Lütfen dosyanın GitHub'da yüklü olduğundan emin olun.")
            return []

    if df is None or len(df) == 0:
        return []

    try:
        # --- OTOMATİK SÜTUN BULMA ---
        hedef_sutun = None
        
        # Sütun isimlerini küçük harfe çevirip içinde anahtar kelime arıyoruz
        for col in df.columns:
            col_lower = str(col).lower()
            if "phone" in col_lower or "telefon" in col_lower or "mobil" in col_lower or "value" in col_lower or "numara" in col_lower:
                hedef_sutun = col
                break
        
        # Eğer isimden bulamazsa, içinde en çok rakam barındıran sütunu seçelim
        if hedef_sutun is None:
             # İlk 5 satıra bakıp en uzun sayısal değer içeren sütunu tahmin etmeye çalış
             hedef_sutun = df.columns[0] 

        # Numaraları temizleyip listeye çevir
        # Sütunu string'e çevirip temizliyoruz
        temiz_liste = df[hedef_sutun].astype(str).apply(numarayi_temizle).tolist()
        
        # Boş ve kısa olanları çıkar (En az 7 haneli olmalı)
        return [no for no in temiz_liste if len(no) > 7]
        
    except Exception as e:
        st.error(f"Veri işleme hatası: {e}")
        return []

def kilit_kontrol(kullanici_no):
    if not os.path.exists(KILIT_DOSYASI):
        with open(KILIT_DOSYASI, 'w') as f:
            json.dump({}, f)
    
    try:
        with open(KILIT_DOSYASI, 'r') as f:
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
        
    with open(KILIT_DOSYASI, 'w') as f:
        json.dump(guncel_oturumlar, f)
        
    return durum

# --- ARAYÜZ ---

st.set_page_config(page_title="Psikoloji İndirim", page_icon="☕", layout="centered")

st.markdown("""
<style>
    .big-font { font-size:20px !important; }
    .stButton button { width: 100%; height: 60px; font-size: 20px; background-color: #FF4B4B; color: white; }
</style>
""", unsafe_allow_html=True)

st.markdown("<h2 style='text-align: center;'>☕ Psikoloji Bölümü İndirim Sistemi</h2>", unsafe_allow_html=True)

if 'giris_basarili' not in st.session_state:
    st.session_state['giris_basarili'] = False

# --- GİRİŞ EKRANI ---
if not st.session_state['giris_basarili']:
    st.info("Lütfen sistemde kayıtlı numaranızı giriniz.")
    
    with st.form("giris_formu"):
        girilen_ham_no = st.text_input("Telefon Numaranız:", max_chars=15)
        buton = st.form_submit_button("Doğrula ve Kod Al")
        
    if buton and girilen_ham_no:
        girilen_temiz_no = numarayi_temizle(girilen_ham_no)
        kayitli_numaralar = dosya_yukle()
        
        eslesme = False
        # Numara eşleşmesi kontrolü (Son 10 haneyi kontrol eder)
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
                st.error("⛔ Bu numara şu an başka bir cihazda aktif! Lütfen 5 dakika bekleyin.")
        else:
            st.error("❌ Bu numara indirim listesinde bulunamadı.")

# --- KOD EKRANI ---
else:
    kilit_kontrol(st.session_state['giris_yapilan_no'])
    
    st.success("✅ Doğrulama Başarılı!")
    st.write("Aşağıdaki kodu kasa görevlisine gösteriniz.")
    
    kod_kutusu = st.empty()
    cubuk_kutusu = st.empty()
    
    while True:
        yeni_kod = random.randint(1000, 9999)
        
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
                {yeni_kod}
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        for i in range(100):
            cubuk_kutusu.progress(100 - i)
            time.sleep(KOD_YENILEME_SANIYE / 100)
