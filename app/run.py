"""Single-command entry point (extended at each checkpoint)."""
from app.config import Settings
from app.storage import Database


def main():
    settings = Settings()
    Database(settings.database_path)
    print("AI Intelligence storage ready. Mock mode:", settings.mock_mode)


if __name__ == "__main__":
    main()
