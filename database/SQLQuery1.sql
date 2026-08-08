-- =====================================================================
-- DUZELTME: OncekiHash CHECK kisitlamasi genesis blok icin izin vermiyordu
-- Sorun: son_log_hash_getir() tablo bossa "0" donuyor (1 karakter),
--        ama eski kisitlama sadece NULL ya da 64 karaktere izin veriyordu.
-- Cozum: "0" degerine ozel olarak izin veren yeni bir kisitlama ekliyoruz.
-- =====================================================================

USE BlokzincirKameraLog;
GO

-- Eski (hatali) kisitlamayi kaldir
ALTER TABLE dbo.VideoLoglari
DROP CONSTRAINT CK_VideoLoglari_OncekiHashLen;
GO

-- Genesis blok ("0") disinda hala 64 karakter kuralini koruyan
-- duzeltilmis kisitlamayi ekle
ALTER TABLE dbo.VideoLoglari
ADD CONSTRAINT CK_VideoLoglari_OncekiHashLen
CHECK (OncekiHash IS NULL OR OncekiHash = '0' OR LEN(OncekiHash) = 64);
GO

PRINT 'OncekiHash kisitlamasi basariyla guncellendi.';