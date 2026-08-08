import os
import pyodbc
from dotenv import load_dotenv

# .env dosyasindaki degiskenleri ortam degiskenlerine yukler
load_dotenv()


def get_connection():
    """
    .env dosyasindaki DB_SERVER / DB_DATABASE bilgilerini kullanarak
    Windows Authentication (Trusted Connection) ile SQL Server'a baglanir.

    Donus:
        pyodbc.Connection  -> Baglanti basariliysa
        None                -> Baglanti basarisiz olursa
    """
    server = os.getenv("DB_SERVER")
    database = os.getenv("DB_DATABASE")
    driver = os.getenv("DB_DRIVER", "{ODBC Driver 17 for SQL Server}")

    connection_string = (
        f"DRIVER={driver};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"Trusted_Connection=yes;"
    )

    try:
        connection = pyodbc.connect(connection_string)
        print(f"[OK] '{database}' veritabanina basariyla baglanildi. (Sunucu: {server})")
        return connection

    except pyodbc.Error as e:
        print("=" * 60)
        print("[HATA] Veritabani baglantisi kurulamadi!")
        print(f"Detay : {e}")
        print("=" * 60)
        return None


if __name__ == "__main__":
    # Dosyayi dogrudan calistirarak baglantiyi test edebilirsiniz
    conn = get_connection()
    if conn:
        conn.close()
        print("[BILGI] Test baglantisi kapatildi.")