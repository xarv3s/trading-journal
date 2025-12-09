from app.core.config import get_settings

settings = get_settings()
print(f"Database URL: {settings.SUPABASE_URL}")
