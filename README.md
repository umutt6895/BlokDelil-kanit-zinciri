# BlokDelil-kanit-zinciri
Yaka kameralarından elde edilen dijital verilerin orijinalliğini kriptografik algoritmalar ve blokzincir mimarisi ile güvence altına alan güvenlik simülasyonu
# Blokdelil: Kriptografik Kanıt Zinciri Simülasyonu

Bu proje sahadaki yaka kameralarından elde edilen dijital delillerin (video kayıtlarının) orijinalliğini kriptografik olarak güvence altına alan bir blokzincir simülasyonudur. Sistem videoları şifreleyerek birbirine bağlar ve geriye dönük veri manipülasyonunu imkansız hale getirir.

## Proje Modülleri
Sistem üç ana modülden oluşmaktadır:
1. **Kamera Kayıt:** Sisteme yeni yaka kameralarının tanımlandığı ve bu cihazlara özel kırılamaz RSA kimliklerinin (Public/Private Key) üretildiği modül.
2. **Video Logu Yükleme:** Sahadan gelen orijinal videoların dijital özetlerinin (SHA-256 Hash) alınıp kameraya ait Private Key ile mühürlenerek blokzincir defterine eklendiği merkez.
3. **Kanıt Doğrulama:** Şüpheli bir videonun sisteme girdiği ilk andaki dijital DNA'sıyla eşleşip eşleşmediğini test eden değiştirilmiş veya montajlanmış videoları anında tespit eden bağımsız denetim noktası.

## Kullanılan Teknolojiler
* **Backend:** Python, Flask
* **Kriptografi ve Mimari:** SHA-256 Hashing, RSA Şifreleme, Blokzincir Veri Yapısı
* **Frontend:** HTML5, CSS3, Bootstrap5, HTMX, Alpine.js
* **Veritabanı:** MS SQL Server

## Kurulum ve Çalıştırma
Sistemi lokal ortamda ayağa kaldırmak için:
1. Bu repoyu bilgisayarınıza klonlayın veya indirin.
2. Gerekli Python kütüphanelerini kurun.
3. Ana dizindeki `baslat.bat` dosyasını çalıştırarak sunucuyu başlatın ve tarayıcınızdan `http://127.0.0.1:5000` adresine gidin.
