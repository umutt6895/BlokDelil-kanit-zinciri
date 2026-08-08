"""
queries.py
-----------
Blokzincir Mantiğiyla Kriptografik Loglama Simülasyonu projesi icin
Kameralar ve VideoLoglari tablolarina yonelik temel CRUD fonksiyonlari.

Her fonksiyon kendi baglantisini acar, islemini yapar ve baglantiyi
guvenli bir sekilde kapatir.
"""

import pyodbc
from database.connection import get_connection


def kamera_ekle(kamera_id, cihaz_adi, public_key):
    """
    Sisteme yeni bir kamera kaydeder (Kameralar tablosuna INSERT).

    Donus:
        True  -> Kayit basarili
        False -> Baglanti veya sorgu hatasi (orn. ayni KameraID zaten var)
    """
    conn = get_connection()
    if conn is None:
        return False

    try:
        with conn:  # islem (transaction) basariliysa commit, hata olursa rollback
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO Kameralar (KameraID, CihazAdi, PublicKey)
                VALUES (?, ?, ?)
                """,
                kamera_id, cihaz_adi, public_key
            )
        print(f"[OK] KameraID={kamera_id} basariyla eklendi.")
        return True

    except pyodbc.Error as e:
        print(f"[HATA] Kamera eklenirken sorun olustu: {e}")
        return False

    finally:
        conn.close()


def kamera_kontrol_et(kamera_id):
    """
    Verilen KameraID'nin veritabaninda kayitli olup olmadigini ve
    aktiflik durumunu kontrol eder.

    Donus:
        True / False -> Kamera bulundu, AktifMi degeri
        None         -> Kamera bulunamadi ya da hata olustu
    """
    conn = get_connection()
    if conn is None:
        return None

    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT AktifMi FROM Kameralar WHERE KameraID = ?", kamera_id
        )
        satir = cursor.fetchone()

        if satir is None:
            print(f"[BILGI] KameraID={kamera_id} veritabaninda bulunamadi.")
            return None

        return bool(satir.AktifMi)

    except pyodbc.Error as e:
        print(f"[HATA] Kamera kontrol edilirken sorun olustu: {e}")
        return None

    finally:
        conn.close()


def son_log_hash_getir():
    """
    Blokzincirin bir sonraki bloguyla baglanti kurabilmesi icin,
    VideoLoglari tablosundaki en son eklenen kaydin Sha256Hash
    degerini getirir. LogID (identity) alanina gore siralama yapilir,
    cunku ZamanDamgasi'nda es zamanlilik olabilir ama LogID her zaman
    artan ve benzersizdir.

    Donus:
        str  -> En son kaydin Sha256Hash degeri
        "0"  -> Tablo bossa (zincirin baslangic/genesis degeri)
        None -> Baglanti veya sorgu hatasi
    """
    conn = get_connection()
    if conn is None:
        return None

    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT TOP 1 Sha256Hash FROM VideoLoglari ORDER BY LogID DESC"
        )
        satir = cursor.fetchone()

        if satir is None:
            return "0"  # Zincirin genesis (baslangic) degeri

        return satir.Sha256Hash

    except pyodbc.Error as e:
        print(f"[HATA] Son log hash'i getirilirken sorun olustu: {e}")
        return None

    finally:
        conn.close()


def log_kaydet(kamera_id, dosya_adi, sha256_hash, onceki_hash):
    """
    Yeni bir video kaydini VideoLoglari tablosuna ekler.
    onceki_hash parametresi, zincirdeki bir onceki bloga referanstir.

    Donus:
        True  -> Kayit basarili
        False -> Baglanti veya sorgu hatasi
    """
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
                kamera_id, dosya_adi, sha256_hash, onceki_hash
            )
        print(f"[OK] Log kaydedildi. Dosya: {dosya_adi}")
        return True

    except pyodbc.Error as e:
        print(f"[HATA] Log kaydedilirken sorun olustu: {e}")
        return False

    finally:
        conn.close()


def tum_loglari_getir():
    """
    Arayuzde listelemek uzere tum log gecmisini, en yeni kayit en
    ustte olacak sekilde (ZamanDamgasi'na gore azalan) dondurur.

    Donus:
        list[dict] -> Her kayit bir sozluk (dict) olarak listelenir
        []         -> Kayit yoksa ya da hata olustuysa
    """
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
        kolon_adlari = [kolon[0] for kolon in cursor.description]
        satirlar = cursor.fetchall()

        return [dict(zip(kolon_adlari, satir)) for satir in satirlar]

    except pyodbc.Error as e:
        print(f"[HATA] Loglar getirilirken sorun olustu: {e}")
        return []

    finally:
        conn.close()