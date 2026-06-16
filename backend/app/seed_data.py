from sqlalchemy.orm import Session
from .models import Ingredient, Badge, User


DEFAULT_INGREDIENTS = [
    ("Sinaasappelsap", "Sap", True, "🍊"),
    ("Citroensap", "Sap", True, "🍋"),
    ("Limoensap", "Sap", True, "🍈"),
    ("Ananassap", "Sap", True, "🍍"),
    ("Cranberrysap", "Sap", True, "🫐"),
    ("Appelsap", "Sap", True, "🍎"),
    ("Mangosap", "Sap", False, "🥭"),
    ("Passievruchtpuree", "Puree", False, "🥭"),
    ("Tonic", "Mixer", True, "🥤"),
    ("Ginger beer", "Mixer", True, "🫚"),
    ("Sprite / lemon-lime soda", "Mixer", True, "✨"),
    ("Bruiswater", "Mixer", True, "💧"),
    ("Cola", "Mixer", True, "🥤"),
    ("Kokoswater", "Mixer", False, "🥥"),
    ("Muntsiroop", "Siroop", False, "🌿"),
    ("Grenadine", "Siroop", True, "❤️"),
    ("Suikersiroop", "Siroop", True, "🍯"),
    ("Vanillesiroop", "Siroop", False, "🍦"),
    ("Komkommer", "Vers", True, "🥒"),
    ("Munt", "Vers", True, "🌱"),
    ("Basilicum", "Vers", False, "🌿"),
    ("Rozemarijn", "Vers", False, "🌲"),
    ("Gember", "Vers", True, "🫚"),
    ("Aardbeien", "Vers", True, "🍓"),
    ("Bosbessen", "Vers", False, "🫐"),
    ("Watermeloen", "Vers", False, "🍉"),
    ("Kokosmelk", "Zuivelvrij", False, "🥥"),
    ("Eiwithoudende aquafaba", "Bar-tool", False, "☁️"),
    ("IJsblokjes", "Bar-tool", True, "🧊"),
    ("Gebroken ijs", "Bar-tool", True, "❄️"),
]


DEFAULT_BADGES = [
    ("first_recipe", "Eerste Shake", "Toegekend wanneer je je eerste recept publiceert."),
    ("ten_reviews", "Smaakjury", "Toegekend na tien geschreven beoordelingen."),
    ("weekly_winner", "Mocktail van de Week", "Toegekend wanneer jouw recept de weekly feature wint."),
]


DEFAULT_USERS = [
    ("lina", "Lina Citrus"),
    ("milo", "Milo Mint"),
    ("nova", "Nova Nectar"),
]


def seed_defaults(db: Session):
    if db.query(Ingredient).count() == 0:
        for name, category, is_common, icon in DEFAULT_INGREDIENTS:
            db.add(Ingredient(name=name, category=category, is_common=is_common, icon=icon))

    if db.query(Badge).count() == 0:
        for code, name, description in DEFAULT_BADGES:
            db.add(Badge(code=code, name=name, description=description))

    if db.query(User).count() == 0:
        for username, display_name in DEFAULT_USERS:
            db.add(User(username=username, display_name=display_name))

    db.commit()
