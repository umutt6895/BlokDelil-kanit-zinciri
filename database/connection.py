import os
import sqlite3

# Veritabaninin ana dizinde olusturulmasi icin yol belirliyoruz
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'blokdelil.db')

def init_db():
    """Tablolar yoksa Render sunucusunda otomatik olusturur."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Kameralar tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Kameralar (
            KameraID INTEGER PRIMARY KEY,
            CihazAdi TEXT NOT NULL,
            PublicKey TEXT NOT NULL,
            AktifMi INTEGER DEFAULT 1
        )
    ''')
    
    # VideoLoglari tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS VideoLoglari (
            LogID INTEGER PRIMARY KEY AUTOINCREMENT,
            KameraID INTEGER NOT NULL,
            DosyaAdi TEXT NOT NULL,
            Sha256Hash TEXT NOT NULL,
            OncekiHash TEXT NOT NULL,
            ZamanDamgasi DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (KameraID) REFERENCES Kameralar (KameraID)
        )
    ''')
    conn.commit()
    conn.close()

def get_connection():
    """SQLite veritabanina baglanti dondurur."""
    try:
        # Eger veritabani dosyasi/tablolar yoksa once onlari olustur
        if not os.path.exists(DB_PATH):
            init_db()
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row # Sutun isimleriyle erisim icin (pyodbc uyumlulugu)
        return conn
    except sqlite3.Error as e:
        print(f"[HATA] SQLite baglantisi kurulamadi: {e}")
        return None
        
# Uygulama ilk baslarken tablolari kontrol et ve olustur
init_db()
    
