"""
crypto.py
-----------
core/crypto.py

Bu modul, projenin sifreleme (kriptografi) islemlerinden sorumludur.
Veritabani ile hicbir iliskisi yoktur; sadece matematiksel/kriptografik
hesaplamalari yapar (RSA anahtar uretimi, SHA-256 hashleme, dijital imza
olusturma ve dogrulama).

Kullanilan kutuphaneler:
    - rsa     (pip install rsa)     -> RSA anahtar uretimi, imzalama, dogrulama
    - hashlib (standart kutuphane)  -> SHA-256 hash hesaplama
"""

import hashlib
import rsa


def rsa_anahtar_cifti_uret(anahtar_boyutu=2048):
    """
    Yeni bir sanal kamera icin RSA public/private anahtar cifti uretir.

    Parametreler:
        anahtar_boyutu (int): Anahtar uzunlugu (bit). Varsayilan: 2048.

    Donus:
        tuple(str, str):
            public_key_pem  -> Kameralar.PublicKey sutununda saklanacak,
                                PEM formatinda public key metni.
            private_key_pem -> Kameranin kendi tarafinda (guvenli sekilde)
                                saklamasi gereken PEM formatinda private
                                key metni. VERITABANINA KAYDEDILMEMELIDIR.
    """
    public_key, private_key = rsa.newkeys(anahtar_boyutu)

    # PEM (PKCS#1) formatina cevirip, DB'de/dosyada metin olarak
    # saklanabilmesi icin bytes -> string donusumu yapiyoruz.
    public_key_pem = public_key.save_pkcs1().decode("utf-8")
    private_key_pem = private_key.save_pkcs1().decode("utf-8")

    return public_key_pem, private_key_pem


def video_hash_hesapla(dosya_yolu, chunk_boyutu=8192):
    """
    Verilen dosya yolundaki videonun SHA-256 hash degerini hesaplar.
    Buyuk boyutlu video dosyalarinda RAM'in sismemesi icin dosyanin
    tamami tek seferde okunmaz; 'chunk_boyutu' kadar parcalar halinde
    okunup hash nesnesi kademeli olarak guncellenir.

    Parametreler:
        dosya_yolu (str): Hash'i hesaplanacak video dosyasinin yolu.
        chunk_boyutu (int): Her okuma isleminde alinacak byte miktari.
                             Varsayilan: 8192 byte.

    Donus:
        str  -> Dosyanin SHA-256 hash degeri (64 karakterlik hex string)
        None -> Dosya bulunamazsa ya da okuma sirasinda hata olusursa
    """
    sha256 = hashlib.sha256()

    try:
        with open(dosya_yolu, "rb") as dosya:
            # Dosyayi kucuk parcalar (chunk) halinde okuyup hash'i
            # adim adim guncelliyoruz; tum dosya asla RAM'e yuklenmiyor.
            for parca in iter(lambda: dosya.read(chunk_boyutu), b""):
                sha256.update(parca)

        return sha256.hexdigest()

    except (FileNotFoundError, OSError) as e:
        print(f"[HATA] Video hash'i hesaplanirken sorun olustu: {e}")
        return None


def hash_imzala(private_key, hash_metni):
    """
    Bir kameranin, uretmis oldugu SHA-256 hash'ini kendi private key'i ile
    dijital olarak imzalamasini (muhurlemesini) saglar. Bu sayede hash'in
    gercekten o kameraya ait oldugu daha sonra dogrulanabilir.

    Parametreler:
        private_key (str | rsa.PrivateKey): PEM formatinda private key
                                             metni ya da hazir bir
                                             rsa.PrivateKey nesnesi.
        hash_metni (str): Imzalanacak SHA-256 hash degeri (hex string).

    Donus:
        bytes -> Uretilen dijital imza
        None  -> Imzalama sirasinda hata olusursa
    """
    try:
        # private_key PEM metni olarak geldiyse rsa.PrivateKey nesnesine ceviriyoruz.
        if isinstance(private_key, str):
            private_key = rsa.PrivateKey.load_pkcs1(private_key.encode("utf-8"))

        imza = rsa.sign(hash_metni.encode("utf-8"), private_key, "SHA-256")
        return imza

    except Exception as e:
        print(f"[HATA] Hash imzalanirken sorun olustu: {e}")
        return None


def imza_dogrula(public_key, hash_metni, imza):
    """
    Verilen dijital imzanin, ilgili hash ve public key ile uyumlu olup
    olmadigini; yani hash'in gercekten o kameraya ait private key ile
    imzalanip imzalanmadigini dogrular.

    Parametreler:
        public_key (str | rsa.PublicKey): PEM formatinda public key metni
                                           ya da hazir bir rsa.PublicKey
                                           nesnesi.
        hash_metni (str): Dogrulanacak SHA-256 hash degeri (hex string).
        imza (bytes): hash_imzala() fonksiyonundan donen dijital imza.

    Donus:
        True  -> Imza gecerli (hash ve public key birbiriyle eslesiyor)
        False -> Imza gecersiz ya da dogrulama sirasinda hata olustu
    """
    try:
        # public_key PEM metni olarak geldiyse rsa.PublicKey nesnesine ceviriyoruz.
        if isinstance(public_key, str):
            public_key = rsa.PublicKey.load_pkcs1(public_key.encode("utf-8"))

        # rsa.verify() basariliysa kullanilan hash algoritmasini dondurur,
        # basarisizsa rsa.VerificationError firlatir.
        rsa.verify(hash_metni.encode("utf-8"), imza, public_key)
        return True

    except rsa.VerificationError:
        # Imza gecersiz: hash sonradan degistirilmis ya da farkli bir
        # private key ile imzalanmis olabilir (sahtecilik supheli).
        return False

    except Exception as e:
        print(f"[HATA] Imza dogrulanirken beklenmeyen bir sorun olustu: {e}")
        return False


if __name__ == "__main__":
    # Modulun dogru calistigini hizlica test etmek icin ornek kullanim
    pub_pem, priv_pem = rsa_anahtar_cifti_uret()
    test_hash = "ornek_sha256_hash_degeri"

    imza = hash_imzala(priv_pem, test_hash)
    sonuc = imza_dogrula(pub_pem, test_hash, imza)

    print("Imza dogrulama sonucu:", sonuc)  # True donmeli