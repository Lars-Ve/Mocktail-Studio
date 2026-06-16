from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from ..models import Recipe, RecipeIngredient, Ingredient, RecipeFlavor


def search_recipes(
    db: Session,
    query: str | None = None,
    flavors: list[str] | None = None,
    pantry_ids: list[int] | None = None,
    difficulty: str | None = None,
):
    recipes = db.query(Recipe).options(
        joinedload(Recipe.recipe_ingredients).joinedload(RecipeIngredient.ingredient),
        joinedload(Recipe.recipe_flavors),
        joinedload(Recipe.author),
    ).filter(Recipe.is_published == True)

    if query:
        q = f"%{query.lower()}%"
        recipes = recipes.outerjoin(RecipeIngredient, RecipeIngredient.recipe_id == Recipe.id)             .outerjoin(Ingredient, RecipeIngredient.ingredient_id == Ingredient.id)             .outerjoin(RecipeFlavor, RecipeFlavor.recipe_id == Recipe.id)             .filter(
                func.lower(Recipe.title).like(q) |
                func.lower(Ingredient.name).like(q) |
                func.lower(RecipeFlavor.flavor).like(q)
            )

    if flavors:
        recipes = recipes.join(RecipeFlavor).filter(RecipeFlavor.flavor.in_(flavors)).group_by(Recipe.id)

    if difficulty:
        recipes = recipes.filter(Recipe.effective_difficulty == difficulty)

    if pantry_ids:
        recipes = recipes.join(RecipeIngredient, RecipeIngredient.recipe_id == Recipe.id).group_by(Recipe.id).having(
            func.count(RecipeIngredient.id) == func.sum(
                func.case((RecipeIngredient.ingredient_id.in_(pantry_ids), 1), else_=0)
            )
        )

    return recipes.order_by(Recipe.popularity_score.desc(), Recipe.created_at.desc()).all()
