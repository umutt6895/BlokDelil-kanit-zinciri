"""
blockchain.py
--------------
core/blockchain.py

Bu modul, veritabani (database.queries) ve sifreleme (core.crypto)
katmanlarini bir araya getirerek blokzincir mantigiyla yeni video
loglarinin zincire eklenmesini saglar. Projenin "kalbi" olan
yeni_blok_ekle() fonksiyonunu icerir.
"""

import os

from database.queries import kamera_kontrol_et, son_log_hash_getir, log_kaydet
from core.crypto import video_hash_hesapla, hash_imzala


def yeni_blok_ekle(kamera_id, dosya_yolu, private_key_pem):
    """
    Yeni bir video kaydini blokzincir mantigiyla zincire ekler.

    Islem sirasi:
        1. Kameranin veritabaninda kayitli ve aktif oldugu dogrulanir.
        2. Video dosyasinin guncel SHA-256 hash'i hesaplanir.
        3. Hash, kameranin private key'i ile imzalanir (muhurleme simulasyonu).
        4. Zincirin bir onceki halkasinin hash'i veritabanindan cekilir.
        5. Tum adimlar basariliysa yeni kayit VideoLoglari tablosuna yazilir.

    Herhangi bir adimda hata olursa islem guvenli sekilde iptal edilir;
    yarim kalmis ya da tutarsiz bir kayit veritabanina yazilmaz.

    Parametreler:
        kamera_id (int): Videonun ait oldugu kameranin KameraID degeri.
        dosya_yolu (str): Islenecek video dosyasinin tam ya da goreli yolu.
        private_key_pem (str): Kameranin PEM formatindaki private key metni.

    Donus:
        True  -> Blok basariyla zincire eklendi
        False -> Islem herhangi bir adimda basarisiz oldu / iptal edildi
    """
    print("[Blokzincir] Yeni video isleniyor...")

    # ---------------------------------------------------------------
    # 1. ADIM: Kamera veritabaninda kayitli mi ve aktif mi kontrol et
    # ---------------------------------------------------------------
    try:
        kamera_aktif_mi = kamera_kontrol_et(kamera_id)
    except Exception as e:
        print(f"[Blokzincir] HATA: Kamera kontrolu sirasinda beklenmeyen sorun: {e}")
        return False

    if kamera_aktif_mi is None:
        print(f"[Blokzincir] IPTAL: KameraID={kamera_id} veritabaninda kayitli degil.")
        return False

    if kamera_aktif_mi is False:
        print(f"[Blokzincir] IPTAL: KameraID={kamera_id} pasif durumda, islem yapilamaz.")
        return False

    print(f"[Blokzincir] KameraID={kamera_id} dogrulandi ve aktif.")

    # ---------------------------------------------------------------
    # 2. ADIM: Video dosyasinin SHA-256 hash'ini hesapla
    # ---------------------------------------------------------------
    try:
        hesaplanan_hash = video_hash_hesapla(dosya_yolu)
    except Exception as e:
        print(f"[Blokzincir] HATA: Hash hesaplanirken beklenmeyen sorun: {e}")
        return False

    if hesaplanan_hash is None:
        print(f"[Blokzincir] IPTAL: '{dosya_yolu}' dosyasinin hash'i hesaplanamadi.")
        return False

    print(f"[Blokzincir] Video hash'i hesaplandi: {hesaplanan_hash[:16]}...")

    # ---------------------------------------------------------------
    # 3. ADIM: Hash'i kameranin private key'i ile imzala (muhurleme)
    #    Not: Imza veritabanina yazilmiyor; burada sadece kameranin
    #    kendi verisini gecerli sekilde imzalayabildigi simule ediliyor.
    # ---------------------------------------------------------------
    try:
        imza = hash_imzala(private_key_pem, hesaplanan_hash)
    except Exception as e:
        print(f"[Blokzincir] HATA: Hash imzalanirken beklenmeyen sorun: {e}")
        return False

    if imza is None:
        print("[Blokzincir] IPTAL: Hash imzalanamadi, kameranin kimligi dogrulanamadi.")
        return False

    print("[Blokzincir] Hash basariyla kameranin private key'i ile imzalandi.")

    # ---------------------------------------------------------------
    # 4. ADIM: Zincirin bir onceki halkasinin hash'ini getir
    #    (Bu deger yeni blogun OncekiHash'i olacak)
    # ---------------------------------------------------------------
    try:
        onceki_hash = son_log_hash_getir()
    except Exception as e:
        print(f"[Blokzincir] HATA: Onceki hash getirilirken beklenmeyen sorun: {e}")
        return False

    if onceki_hash is None:
        print("[Blokzincir] IPTAL: Zincirin onceki halkasina ulasilamadi (veritabani hatasi).")
        return False

    print(f"[Blokzincir] Zincirin bir onceki halkasi bulundu: {onceki_hash[:16]}...")

    # ---------------------------------------------------------------
    # 5. ADIM: Dosya adini tam yoldan ayikla ve yeni blogu kaydet
    # ---------------------------------------------------------------
    dosya_adi = os.path.basename(dosya_yolu)  # orn: "videolar/video1.mp4" -> "video1.mp4"

    try:
        basarili = log_kaydet(kamera_id, dosya_adi, hesaplanan_hash, onceki_hash)
    except Exception as e:
        print(f"[Blokzincir] HATA: Blok veritabanina yazilirken beklenmeyen sorun: {e}")
        return False

    if not basarili:
        print("[Blokzincir] IPTAL: Blok veritabanina yazilamadi.")
        return False

    print("[Blokzincir] Blok basariyla zincire eklendi!")
    return True


if __name__ == "__main__":
    # Hizli manuel test icin ornek kullanim
    ornek_kamera_id = 1
    ornek_dosya_yolu = "videolar/video_003.mp4"
    ornek_private_key = "----- BURAYA PEM FORMATINDA PRIVATE KEY GELECEK -----"

    yeni_blok_ekle(ornek_kamera_id, ornek_dosya_yolu, ornek_private_key)