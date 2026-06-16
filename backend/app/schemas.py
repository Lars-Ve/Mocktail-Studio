from pydantic import BaseModel, Field
from typing import List


FLAVORS = ["zoet", "zuur", "bitter", "fruitig", "kruidig", "fris"]
DIFFICULTIES = ["Makkelijk", "Gemiddeld", "Barista-level"]


class RecipeIngredientInput(BaseModel):
    ingredient_id: int
    quantity: str = Field(..., max_length=50)
    step_order: int = 1
    note: str | None = None


class RecipeCreate(BaseModel):
    user_id: int
    title: str
    description: str
    glassware: str | None = None
    garnish: str | None = None
    instructions: str
    submitted_difficulty: str = "Gemiddeld"
    flavors: List[str]
    ingredients: List[RecipeIngredientInput]


class ReviewCreate(BaseModel):
    user_id: int
    stars: int = Field(..., ge=1, le=5)
    review_text: str


class FlavorVoteCreate(BaseModel):
    user_id: int
    flavors: List[str]


class DifficultyVoteCreate(BaseModel):
    user_id: int
    difficulty: str


class FavoriteCreate(BaseModel):
    user_id: int
