"""Uygulama yapılandırma ayarları — ortam değişkenlerinden veya .env dosyasından okunur."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Veritabanı bağlantı dizesi
    database_url: str = "postgresql+asyncpg://caretta:caretta@localhost:5432/carettaid"

    # Loglama seviyesi
    log_level: str = "INFO"

    # Fotoğraf yükleme dizini
    upload_dir: str = "uploads"

    # Gömme vektörü boyutu — [semantic_512 | spatial_color_512] = 1024
    embedding_dim: int = 1024

    # Kabul eşiği — bu değerin üzerindeki skor "eşleşme" sayılır
    # 60% semantic + 40% spatial: aynı kaplumbağa ~0.67-0.78, alakasız görseller ~0.50-0.58
    similarity_threshold: float = 0.70

    # Aday gösterme tabanı — bu değerin üzerindeki sonuçlar "olası aday" olarak
    # döndürülür, kabul edilmeseler bile frontend onları gösterebilir
    # Tamamen alakasız görseller (kupa, araba, kişi) ~0.50-0.58 → bu değer altında kalır
    similarity_floor: float = 0.62

    # Döndürülecek maksimum eşleşme sayısı
    top_n_matches: int = 5


@lru_cache
def get_settings() -> Settings:
    """Ayarları önbellekten döndürür — her istekte yeniden okumaz."""
    return Settings()
