"""
queries.py
-----------
Blokzincir Mantiğiyla Kriptografik Loglama Simülasyonu projesi icin
Kameralar ve VideoLoglari tablolarina yonelik temel CRUD fonksiyonlari.
(SQLite versiyonu)
"""

import sqlite3
from database.connection import get_connection

def kamera_ekle(kamera_id, cihaz_adi, public_key):
    conn = get_connection()
    if conn is None:
        return False
    try:
        with conn: 
            cursor = conn.cursor()
            # SQLite parametreleri tuple olarak bekler
            cursor.execute(
                "INSERT INTO Kameralar (KameraID, CihazAdi, PublicKey) VALUES (?, ?, ?)",
                (kamera_id, cihaz_adi, public_key)
            )
        print(f"[OK] KameraID={kamera_id} basariyla eklendi.")
        return True
    except sqlite3.Error as e:
        print(f"[HATA] Kamera eklenirken sorun olustu: {e}")
        return False
    finally:
        conn.close()

def kamera_kontrol_et(kamera_id):
    conn = get_connection()
    if conn is None:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT AktifMi FROM Kameralar WHERE KameraID = ?", (kamera_id,))
        satir = cursor.fetchone()
        
        if satir is None:
            print(f"[BILGI] KameraID={kamera_id} veritabaninda bulunamadi.")
            return None
            
        return bool(satir['AktifMi'])
    except sqlite3.Error as e:
        print(f"[HATA] Kamera kontrol edilirken sorun olustu: {e}")
        return None
    finally:
        conn.close()

def son_log_hash_getir():
    conn = get_connection()
    if conn is None:
        return None
    try:
        cursor = conn.cursor()
        # SQL Server'daki TOP 1 yerine SQLite'ta LIMIT 1 kullanilir
        cursor.execute("SELECT Sha256Hash FROM VideoLoglari ORDER BY LogID DESC LIMIT 1")
        satir = cursor.fetchone()
        
        if satir is None:
            return "0"  # Zincirin genesis degeri
            
        return satir['Sha256Hash']
    except sqlite3.Error as e:
        print(f"[HATA] Son log hash'i getirilirken sorun olustu: {e}")
        return None
    finally:
        conn.close()

def log_kaydet(kamera_id, dosya_adi, sha256_hash, onceki_hash):
    conn = get_connection()
    if conn is None:
        return False
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO VideoLoglari (KameraID, DosyaAdi, Sha256Hash, OncekiHash)
                VALUES (?, ?, ?, ?)
                """,
                (kamera_id, dosya_adi, sha256_hash, onceki_hash)
            )
        print(f"[OK] Log kaydedildi. Dosya: {dosya_adi}")
        return True
    except sqlite3.Error as e:
        print(f"[HATA] Log kaydedilirken sorun olustu: {e}")
        return False
    finally:
        conn.close()

def tum_loglari_getir():
    conn = get_connection()
    if conn is None:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT LogID, KameraID, DosyaAdi, Sha256Hash, OncekiHash, ZamanDamgasi
            FROM VideoLoglari
            ORDER BY ZamanDamgasi DESC
            """
        )
        satirlar = cursor.fetchall()
        # sqlite3.Row sayesinde dogrudan sozluge cevirebiliriz
        return [dict(satir) for satir in satirlar]
    except sqlite3.Error as e:
        print(f"[HATA] Loglar getirilirken sorun olustu: {e}")
        return []
    finally:
        conn.close()
