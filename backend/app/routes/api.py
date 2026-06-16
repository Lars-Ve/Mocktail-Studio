from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Ingredient, Recipe
from ..services.scoring import aggregate_flavors

router = APIRouter(prefix="/api")


@router.get("/ingredients")
def list_ingredients(db: Session = Depends(get_db)):
    items = db.query(Ingredient).order_by(Ingredient.category.asc(), Ingredient.name.asc()).all()
    return [{"id": i.id, "name": i.name, "category": i.category, "icon": i.icon} for i in items]


@router.get("/recipes/{recipe_id}/flavors")
def get_recipe_flavors(recipe_id: int, db: Session = Depends(get_db)):
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not recipe:
        return {"error": "not_found"}
    return aggregate_flavors(db, recipe_id)
