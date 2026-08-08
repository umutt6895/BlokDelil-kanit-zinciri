"""
app.py
-------
blokdelil/app.py

Projenin Flask tabanli sunum katmani (presentation layer). Bu dosya
veritabani (database.queries), sifreleme (core.crypto) ve blokzincir
(core.blockchain) katmanlarini birlestirerek HTMX tabanli arayuze
API uc noktalari (endpoint) sunar.

Arayuz, tek sayfalik bir dashboard degil; bir Ana Menu (/) ve 3 ayri
modul sayfasindan (/kamera-kayit, /video-yukle, /kanit-dogrula) olusan
cok sayfali (multi-page) bir yapidadir. API rotalari (/api/...) sayfa
yapisindan bagimsiz olarak ayni sekilde calismaya devam eder.
"""

import os
import tempfile

from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename

from database.queries import kamera_ekle, tum_loglari_getir
from core.crypto import rsa_anahtar_cifti_uret, video_hash_hesapla
from core.blockchain import yeni_blok_ekle


# =====================================================================
# UYGULAMA AYARLARI
# =====================================================================
app = Flask(__name__)

# Video dosyalarinin fiziksel olarak saklanacagi klasor (blokdelil/kamera_kayitlari)
KAYIT_KLASORU = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kamera_kayitlari")

# Uygulama baslarken kamera_kayitlari/ klasoru yoksa otomatik olustur
os.makedirs(KAYIT_KLASORU, exist_ok=True)


# =====================================================================
# ROTALAR (ROUTES) - ARAYUZ (GET) ROTALARI
# =====================================================================
# Uygulama artik tek sayfalik bir dashboard degil; bir ana menu ve
# 3 ayri modul sayfasindan olusan cok sayfali (multi-page) bir yapida.
# Asagidaki 4 rota SADECE sablon render eder; API mantigina (asagidaki
# /api/... rotalarina) hicbir sekilde dokunulmamistir.

@app.route("/", methods=["GET"])
def index():
    """
    Ana Karsilama ve Menu sayfasi.

    Herhangi bir veritabani sorgusu yapmaz; sadece 3 module
    (Kamera Kayit, Video Yukle, Kanit Dogrula) yonlendiren linkleri
    iceren index.html sablonunu render eder.
    """
    return render_template("index.html")


@app.route("/kamera-kayit", methods=["GET"])
def kamera_kayit_sayfa():
    """
    Kamera Kayit modul sayfasi.

    Sadece kamera olusturma formunu iceren kamera.html sablonunu
    render eder. Form gonderimi /api/kamera_ekle uzerinden Alpine.js
    + fetch ile yapilir (bu rotayla dogrudan ilgisi yoktur).
    """
    return render_template("kamera.html")


@app.route("/video-yukle", methods=["GET"])
def video_yukle_sayfa():
    """
    Video Yukle modul sayfasi.

    Bu sayfada hem yukleme formu hem de zincirin tum gecmisini
    gosteren log tablosu bulundugu icin, tum_loglari_getir() burada
    calistirilip sonuc yukleme.html sablonuna gonderilir.
    """
    loglar = tum_loglari_getir()
    return render_template("yukleme.html", loglar=loglar)


@app.route("/kanit-dogrula", methods=["GET"])
def kanit_dogrula_sayfa():
    """
    Kanit Dogrula modul sayfasi.

    Sadece supheli video dosyasi yukleme formunu iceren dogrulama.html
    sablonunu render eder. Sonuc /api/video_dogrula uzerinden HTMX ile
    ayni sayfa icinde gosterilir.
    """
    return render_template("dogrulama.html")


@app.route("/api/kamera_ekle", methods=["POST"])
def api_kamera_ekle():
    """
    Sisteme yeni bir sanal kamera ekler.

    HTMX'ten form-data olarak gelen alanlar:
        KameraID (int)  -> Yeni kameranin benzersiz kimligi
        CihazAdi (str)  -> Kameranin goruntulenecek adi

    Islem:
        1. rsa_anahtar_cifti_uret() ile yeni bir public/private anahtar
           cifti uretilir.
        2. Sadece public_key veritabanina (Kameralar.PublicKey) kaydedilir.
        3. private_key VERITABANINA KAYDEDILMEZ; kullanicinin guvenli
           sekilde saklayabilmesi icin JSON yanit olarak GERI DONULUR.
           Bu yanit kaybedilirse anahtar bir daha geri getirilemez.

    Donus (JSON):
        basarili (bool), mesaj (str), kamera_id (int),
        public_key (str), private_key (str) -> SADECE bu istekte gosterilir!
    """
    cihaz_adi = request.form.get("CihazAdi", "").strip()
    kamera_id_raw = request.form.get("KameraID", "").strip()

    # Temel girdi kontrolu
    if not cihaz_adi or not kamera_id_raw:
        return jsonify({
            "basarili": False,
            "mesaj": "KameraID ve CihazAdi alanlari zorunludur."
        }), 400

    try:
        kamera_id = int(kamera_id_raw)
    except ValueError:
        return jsonify({
            "basarili": False,
            "mesaj": "KameraID sayisal bir deger olmalidir."
        }), 400

    try:
        # 1) RSA anahtar cifti uret
        public_key_pem, private_key_pem = rsa_anahtar_cifti_uret()

        # 2) Sadece public key'i veritabanina kaydet
        eklendi = kamera_ekle(kamera_id, cihaz_adi, public_key_pem)

        if not eklendi:
            return jsonify({
                "basarili": False,
                "mesaj": f"KameraID={kamera_id} eklenemedi (zaten kayitli olabilir)."
            }), 400

        # 3) private_key SADECE bu yanitla kullaniciya gosterilir, saklanmaz
        return jsonify({
            "basarili": True,
            "mesaj": "Kamera basariyla olusturuldu. Private key'i guvenli bir yere kaydedin!",
            "kamera_id": kamera_id,
            "public_key": public_key_pem,
            "private_key": private_key_pem
        }), 201

    except Exception as e:
        return jsonify({
            "basarili": False,
            "mesaj": f"Kamera eklenirken beklenmeyen bir hata olustu: {e}"
        }), 500


@app.route("/api/video_yukle", methods=["POST"])
def api_video_yukle():
    """
    Bir kameranin urettigi video dosyasini alir, diske kaydeder ve
    blokzincire (VideoLoglari) yeni bir blok olarak ekler.

    HTMX'ten form-data olarak gelen alanlar:
        video       (dosya) -> Yuklenecek video dosyasi
        KameraID    (int)   -> Videoyu gonderen kameranin kimligi
        PrivateKey  (str)   -> Kameranin PEM formatindaki private key'i
                                (imzalama icin kullanici tarafindan girilir)

    Islem:
        1. Dosya secure_filename ile guvenli hale getirilip
           kamera_kayitlari/ klasorune kaydedilir.
        2. core.blockchain.yeni_blok_ekle() tetiklenir; bu fonksiyon
           kamera dogrulama, hash hesaplama, imzalama ve zincire ekleme
           islemlerinin tamamini yonetir.

    Donus:
        HTMX'in dogrudan sayfaya basabilecegi kisa bir metin ve
        uygun HTTP durum kodu.
    """
    video_dosyasi = request.files.get("video")
    kamera_id_raw = request.form.get("KameraID", "").strip()
    private_key_pem = request.form.get("PrivateKey", "").strip()

    # Temel girdi kontrolu
    if not video_dosyasi or video_dosyasi.filename == "":
        return "[HATA] Yuklenecek bir video dosyasi secilmedi.", 400

    if not kamera_id_raw or not private_key_pem:
        return "[HATA] KameraID ve Private Key alanlari zorunludur.", 400

    try:
        kamera_id = int(kamera_id_raw)
    except ValueError:
        return "[HATA] KameraID sayisal bir deger olmalidir.", 400

    try:
        # 1) Dosyayi guvenli isimle kamera_kayitlari/ klasorune kaydet
        guvenli_dosya_adi = secure_filename(video_dosyasi.filename)
        kayit_yolu = os.path.join(KAYIT_KLASORU, guvenli_dosya_adi)
        video_dosyasi.save(kayit_yolu)

        # 2) Blokzincire ekle (kamera dogrulama + hash + imza + kayit)
        sonuc = yeni_blok_ekle(kamera_id, kayit_yolu, private_key_pem)

        if sonuc:
            return f"[Blokzincir] '{guvenli_dosya_adi}' basariyla zincire eklendi.", 200

        return f"[Blokzincir] '{guvenli_dosya_adi}' zincire eklenemedi. Terminal loglarini kontrol edin.", 400

    except Exception as e:
        return f"[HATA] Video yuklenirken beklenmeyen bir sorun olustu: {e}", 500


@app.route("/api/video_dogrula", methods=["POST"])
def api_video_dogrula():
    """
    Supheli bir video dosyasinin, veritabanindaki kayitlarla eslesip
    eslesmedigini kontrol ederek orijinalligini dogrular.

    HTMX'ten form-data olarak gelen alan:
        video (dosya) -> Dogrulanacak supheli video dosyasi

    Islem:
        1. Dosya kalici olmayan, gecici bir konuma kaydedilir.
        2. video_hash_hesapla() ile SHA-256 hash'i hesaplanir.
        3. tum_loglari_getir() ile cekilen tum kayitlar arasinda bu
           hash'in olup olmadigina bakilir.
        4. Gecici dosya islemin sonunda (basarili ya da basarisiz
           fark etmeksizin) mutlaka silinir.

    Donus:
        HTMX'in dogrudan sayfaya basabilecegi sonuc metni.
    """
    video_dosyasi = request.files.get("video")

    if not video_dosyasi or video_dosyasi.filename == "":
        return "[HATA] Dogrulanacak bir video dosyasi secilmedi.", 400

    gecici_yol = None

    try:
        # 1) Dosyayi gecici bir konuma kaydet (orijinal uzantisini koruyarak)
        guvenli_dosya_adi = secure_filename(video_dosyasi.filename)
        _, uzanti = os.path.splitext(guvenli_dosya_adi)

        with tempfile.NamedTemporaryFile(delete=False, suffix=uzanti) as gecici_dosya:
            gecici_yol = gecici_dosya.name
        video_dosyasi.save(gecici_yol)

        # 2) Supheli dosyanin hash'ini hesapla
        supheli_hash = video_hash_hesapla(gecici_yol)

        if supheli_hash is None:
            return "[HATA] Dosyanin hash'i hesaplanamadi.", 500

        # 3) Veritabanindaki tum loglar icinde bu hash'i ara
        tum_loglar = tum_loglari_getir()
        eslesme_var_mi = any(log.get("Sha256Hash") == supheli_hash for log in tum_loglar)

        if eslesme_var_mi:
            return "[Dogrulama] Video Orijinal (Veritabaninda Onayli)", 200

        return "[Dogrulama] UYARI: Video Degistirilmis veya Sahte!", 200

    except Exception as e:
        return f"[HATA] Video dogrulanirken beklenmeyen bir sorun olustu: {e}", 500

    finally:
        # 4) Gecici dosyayi her durumda temizle
        if gecici_yol and os.path.exists(gecici_yol):
            os.remove(gecici_yol)


# =====================================================================
# UYGULAMAYI CALISTIR
# =====================================================================
if __name__ == "__main__":
    app.run(debug=True)