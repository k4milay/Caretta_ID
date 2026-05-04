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

    # Gömme vektörü boyutu (EfficientNet-B0 projeksiyon başlığı çıkışı)
    embedding_dim: int = 512

    # Benzerlik eşiği — tam vücut + 3 bölge ağırlıklı gömme için 0.78
    # (Tek bölge baş gömmeleri için 0.60 kullanılıyordu)
    similarity_threshold: float = 0.78

    # Döndürülecek maksimum eşleşme sayısı
    top_n_matches: int = 5


@lru_cache
def get_settings() -> Settings:
    """Ayarları önbellekten döndürür — her istekte yeniden okumaz."""
    return Settings()
