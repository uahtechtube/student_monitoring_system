import os

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


class Config:
    """Base configuration shared by every environment."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'kiu_monitoring.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MODEL_DIR = os.path.join(BASE_DIR, "app", "static", "models")


    # --- Business rules (Chapter 3 constants) ---
    MIN_DATASET_SIZE = 30          # Section 3.3, Step 4: Size Validation
    N_CLUSTERS = 3                 # High / Average / At Risk
    KMEANS_N_INIT = 10
    KMEANS_MAX_ITER = 300
    TEST_SPLIT_SIZE = 0.20         # Section 3.8.1: 80/20 train/test split
    RANDOM_STATE = 42
    IQR_MULTIPLIER = 1.5           # Section 3.3, Step 2: Outlier Detection


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    MIN_DATASET_SIZE = 5  # relaxed so small unit-test fixtures still pass validation


class ProductionConfig(Config):
    DEBUG = False


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
