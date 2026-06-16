from datetime import datetime, date
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    recipes = relationship("Recipe", back_populates="author")
    reviews = relationship("Review", back_populates="user")
    favorites = relationship("Favorite", back_populates="user")


class Ingredient(Base):
    __tablename__ = "ingredients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    category: Mapped[str] = mapped_column(String(60), index=True)
    is_common: Mapped[bool] = mapped_column(Boolean, default=True)
    icon: Mapped[str | None] = mapped_column(String(10), nullable=True)


class Recipe(Base):
    __tablename__ = "recipes"
    __table_args__ = (
        Index("ix_recipes_title_lower", "title"),
        Index("ix_recipes_difficulty_effective", "effective_difficulty"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(220), unique=True, nullable=False, index=True)
    share_token: Mapped[str] = mapped_column(String(24), unique=True, nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    glassware: Mapped[str | None] = mapped_column(String(80), nullable=True)
    garnish: Mapped[str | None] = mapped_column(String(120), nullable=True)
    instructions: Mapped[str] = mapped_column(Text, nullable=False)
    submitted_difficulty: Mapped[str] = mapped_column(String(20), default="Gemiddeld", index=True)
    effective_difficulty: Mapped[str] = mapped_column(String(20), default="Gemiddeld", index=True)
    avg_rating: Mapped[float] = mapped_column(Float, default=0.0)
    review_count: Mapped[int] = mapped_column(Integer, default=0)
    favorite_count: Mapped[int] = mapped_column(Integer, default=0)
    popularity_score: Mapped[float] = mapped_column(Float, default=0.0)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    author = relationship("User", back_populates="recipes")
    recipe_ingredients = relationship("RecipeIngredient", back_populates="recipe", cascade="all, delete-orphan")
    recipe_flavors = relationship("RecipeFlavor", back_populates="recipe", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="recipe", cascade="all, delete-orphan")
    flavor_votes = relationship("FlavorVote", back_populates="recipe", cascade="all, delete-orphan")
    difficulty_votes = relationship("DifficultyVote", back_populates="recipe", cascade="all, delete-orphan")
    favorites = relationship("Favorite", back_populates="recipe", cascade="all, delete-orphan")


class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    recipe_id: Mapped[int] = mapped_column(ForeignKey("recipes.id"), index=True)
    ingredient_id: Mapped[int] = mapped_column(ForeignKey("ingredients.id"), index=True)
    quantity: Mapped[str] = mapped_column(String(50), nullable=False)
    step_order: Mapped[int] = mapped_column(Integer, default=1)
    note: Mapped[str | None] = mapped_column(String(180), nullable=True)

    recipe = relationship("Recipe", back_populates="recipe_ingredients")
    ingredient = relationship("Ingredient")


class RecipeFlavor(Base):
    __tablename__ = "recipe_flavors"
    __table_args__ = (UniqueConstraint("recipe_id", "flavor", name="uq_recipe_flavor"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    recipe_id: Mapped[int] = mapped_column(ForeignKey("recipes.id"), index=True)
    flavor: Mapped[str] = mapped_column(String(30), index=True)
    source: Mapped[str] = mapped_column(String(20), default="submitter")
    weight: Mapped[float] = mapped_column(Float, default=1.0)

    recipe = relationship("Recipe", back_populates="recipe_flavors")


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (UniqueConstraint("user_id", "recipe_id", name="uq_user_recipe_review"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    recipe_id: Mapped[int] = mapped_column(ForeignKey("recipes.id"), nullable=False, index=True)
    stars: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    review_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="reviews")
    recipe = relationship("Recipe", back_populates="reviews")


class FlavorVote(Base):
    __tablename__ = "flavor_votes"
    __table_args__ = (UniqueConstraint("user_id", "recipe_id", "flavor", name="uq_user_recipe_flavor_vote"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    recipe_id: Mapped[int] = mapped_column(ForeignKey("recipes.id"), index=True)
    flavor: Mapped[str] = mapped_column(String(30), index=True)
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    recipe = relationship("Recipe", back_populates="flavor_votes")


class DifficultyVote(Base):
    __tablename__ = "difficulty_votes"
    __table_args__ = (UniqueConstraint("user_id", "recipe_id", name="uq_user_recipe_difficulty_vote"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    recipe_id: Mapped[int] = mapped_column(ForeignKey("recipes.id"), index=True)
    difficulty: Mapped[str] = mapped_column(String(20), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    recipe = relationship("Recipe", back_populates="difficulty_votes")


class Favorite(Base):
    __tablename__ = "favorites"
    __table_args__ = (UniqueConstraint("user_id", "recipe_id", name="uq_user_recipe_favorite"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    recipe_id: Mapped[int] = mapped_column(ForeignKey("recipes.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="favorites")
    recipe = relationship("Recipe", back_populates="favorites")


class Badge(Base):
    __tablename__ = "badges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)


class UserBadge(Base):
    __tablename__ = "user_badges"
    __table_args__ = (UniqueConstraint("user_id", "badge_id", name="uq_user_badge"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    badge_id: Mapped[int] = mapped_column(ForeignKey("badges.id"), index=True)
    awarded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    badge = relationship("Badge")


class DomainEvent(Base):
    __tablename__ = "domain_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_type: Mapped[str] = mapped_column(String(50), index=True)
    aggregate_type: Mapped[str] = mapped_column(String(50), index=True)
    aggregate_id: Mapped[int] = mapped_column(Integer, index=True)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    processed: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class WeeklyFeature(Base):
    __tablename__ = "weekly_features"
    __table_args__ = (UniqueConstraint("week_start", name="uq_week_start"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    week_start: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    recipe_id: Mapped[int] = mapped_column(ForeignKey("recipes.id"), nullable=False, index=True)
    rank: Mapped[int] = mapped_column(Integer, default=1)
    reason: Mapped[str] = mapped_column(String(180), default="Best weekly blend")

    recipe = relationship("Recipe")
