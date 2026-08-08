-- =====================================================================
-- PROJE : Yaka Kameralarý Ýçin Blokzincir Mantýðýyla Kriptografik
--         Loglama Simülasyonu
-- AMAÇ  : 3NF (Üçüncü Normal Form) standartlarýna uygun temel þema
-- =====================================================================

IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = N'BlokzincirKameraLog')
BEGIN
    CREATE DATABASE BlokzincirKameraLog;
END
GO

USE BlokzincirKameraLog;
GO

-- ---------------------------------------------------------------------
-- 1. TABLO: Kameralar
--    Fiziksel yaka kamerasý cihazlarýný ve RSA açýk anahtarlarýný tutar.
-- ---------------------------------------------------------------------
CREATE TABLE dbo.Kameralar
(
    KameraID        INT             NOT NULL,
    CihazAdi        VARCHAR(100)    NOT NULL,
    PublicKey       VARCHAR(MAX)    NOT NULL,
    AktifMi         BIT             NOT NULL CONSTRAINT DF_Kameralar_AktifMi     DEFAULT (1),
    KayitTarihi     DATETIME        NOT NULL CONSTRAINT DF_Kameralar_KayitTarihi DEFAULT (GETDATE()),

    CONSTRAINT PK_Kameralar        PRIMARY KEY CLUSTERED (KameraID),
    CONSTRAINT UQ_Kameralar_Cihaz  UNIQUE (CihazAdi)
);
GO

-- ---------------------------------------------------------------------
-- 2. TABLO: VideoLoglari
--    Her kaydýn SHA-256 özetini ve bir önceki kaydýn hash'ine olan
--    referansýný tutarak blokzincir zincirlemesini simüle eder.
-- ---------------------------------------------------------------------
CREATE TABLE dbo.VideoLoglari
(
    LogID           INT             IDENTITY(1,1) NOT NULL,
    KameraID        INT             NOT NULL,
    DosyaAdi        VARCHAR(255)    NOT NULL,
    Sha256Hash      VARCHAR(64)     NOT NULL,   -- SHA-256 -> 64 hex karakter
    OncekiHash      VARCHAR(64)     NULL,       -- Zincirin ilk bloðunda NULL olabilir
    ZamanDamgasi    DATETIME        NOT NULL CONSTRAINT DF_VideoLoglari_ZamanDamgasi DEFAULT (GETDATE()),

    CONSTRAINT PK_VideoLoglari         PRIMARY KEY CLUSTERED (LogID),
    CONSTRAINT UQ_VideoLoglari_Hash    UNIQUE (Sha256Hash),

    CONSTRAINT FK_VideoLoglari_Kameralar FOREIGN KEY (KameraID)
        REFERENCES dbo.Kameralar (KameraID)
        ON DELETE NO ACTION
        ON UPDATE NO ACTION,

    CONSTRAINT CK_VideoLoglari_HashLen      CHECK (LEN(Sha256Hash) = 64),
    CONSTRAINT CK_VideoLoglari_OncekiHashLen CHECK (OncekiHash IS NULL OR LEN(OncekiHash) = 64)
);
GO

-- FK sütunu üzerinde sorgu performansý için index
CREATE NONCLUSTERED INDEX IX_VideoLoglari_KameraID
    ON dbo.VideoLoglari (KameraID);
GO

-- Zincir sýrasýný hýzlý sorgulamak için index
CREATE NONCLUSTERED INDEX IX_VideoLoglari_ZamanDamgasi
    ON dbo.VideoLoglari (ZamanDamgasi);
GO