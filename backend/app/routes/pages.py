from __future__ import annotations
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from slugify import slugify
from secrets import token_urlsafe

from ..database import get_db
from ..models import (
    Ingredient,
    Recipe,
    RecipeIngredient,
    RecipeFlavor,
    Review,
    FlavorVote,
    Favorite,
    DifficultyVote,
    User,
    UserBadge,
)
from ..services.badges import emit_event, process_badge_events
from ..services.scoring import aggregate_flavors, recalculate_recipe_metrics
from ..services.search import search_recipes
from ..services.weekly import get_homepage_featured, shake_to_surprise


templates = Jinja2Templates(directory="app/templates")
router = APIRouter()


def current_user(db: Session) -> User:
    return db.query(User).order_by(User.id.asc()).first()


@router.get("/", response_class=HTMLResponse)
def home(request: Request, q: str | None = None, flavor: list[str] | None = None, difficulty: str | None = None, db: Session = Depends(get_db)):
    featured, others = get_homepage_featured(db)
    ingredients = db.query(Ingredient).order_by(Ingredient.category.asc(), Ingredient.name.asc()).all()
    recipes = search_recipes(db, query=q, flavors=flavor, difficulty=difficulty)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "featured": featured,
        "others": others,
        "recipes": recipes,
        "ingredients": ingredients,
        "q": q or "",
        "selected_flavors": flavor or [],
        "selected_difficulty": difficulty or "",
    })


@router.get("/recipes/new", response_class=HTMLResponse)
def new_recipe_form(request: Request, db: Session = Depends(get_db)):
    ingredients = db.query(Ingredient).order_by(Ingredient.category.asc(), Ingredient.name.asc()).all()
    return templates.TemplateResponse("recipe_form.html", {
        "request": request,
        "ingredients": ingredients,
        "flavors": ["zoet", "zuur", "bitter", "fruitig", "kruidig", "fris"],
        "difficulties": ["Makkelijk", "Gemiddeld", "Barista-level"],
    })


@router.post("/recipes/new")
def create_recipe(
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
    glassware: str = Form(""),
    garnish: str = Form(""),
    instructions: str = Form(...),
    submitted_difficulty: str = Form(...),
    flavors: list[str] = Form([]),
    ingredient_ids: list[int] = Form([]),
    quantities: list[str] = Form([]),
    step_orders: list[int] = Form([]),
    notes: list[str] = Form([]),
    db: Session = Depends(get_db),
):
    user = current_user(db)
    slug_base = slugify(title)
    slug = slug_base
    counter = 2
    while db.query(Recipe).filter(Recipe.slug == slug).first():
        slug = f"{slug_base}-{counter}"
        counter += 1

    recipe = Recipe(
        user_id=user.id,
        title=title,
        slug=slug,
        share_token=token_urlsafe(8),
        description=description,
        glassware=glassware or None,
        garnish=garnish or None,
        instructions=instructions,
        submitted_difficulty=submitted_difficulty,
        effective_difficulty=submitted_difficulty,
    )
    db.add(recipe)
    db.commit()
    db.refresh(recipe)

    for idx, ingredient_id in enumerate(ingredient_ids):
        if idx >= len(quantities) or not quantities[idx].strip():
            continue
        db.add(RecipeIngredient(
            recipe_id=recipe.id,
            ingredient_id=ingredient_id,
            quantity=quantities[idx],
            step_order=step_orders[idx] if idx < len(step_orders) else 1,
            note=notes[idx] if idx < len(notes) else None,
        ))

    for flavor in flavors:
        db.add(RecipeFlavor(recipe_id=recipe.id, flavor=flavor, source="submitter", weight=1.0))

    db.commit()
    emit_event(db, "recipe.created", "recipe", recipe.id, {"user_id": user.id, "recipe_id": recipe.id})
    process_badge_events(db)
    recalculate_recipe_metrics(db, recipe)

    return RedirectResponse(url=f"/recipes/{recipe.slug}", status_code=303)


@router.get("/recipes/{slug}", response_class=HTMLResponse)
def recipe_detail(request: Request, slug: str, db: Session = Depends(get_db)):
    recipe = db.query(Recipe).options(
        joinedload(Recipe.author),
        joinedload(Recipe.recipe_ingredients).joinedload(RecipeIngredient.ingredient),
        joinedload(Recipe.recipe_flavors),
        joinedload(Recipe.reviews).joinedload(Review.user),
    ).filter(Recipe.slug == slug).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Recept niet gevonden")

    flavor_stats = aggregate_flavors(db, recipe.id)
    user = current_user(db)
    is_favorited = db.query(Favorite).filter(Favorite.user_id == user.id, Favorite.recipe_id == recipe.id).first() is not None
    return templates.TemplateResponse("recipe_detail.html", {
        "request": request,
        "recipe": recipe,
        "flavor_stats": flavor_stats,
        "is_favorited": is_favorited,
        "flavors": ["zoet", "zuur", "bitter", "fruitig", "kruidig", "fris"],
        "difficulties": ["Makkelijk", "Gemiddeld", "Barista-level"],
    })


@router.post("/recipes/{recipe_id}/reviews")
def add_review(recipe_id: int, stars: int = Form(...), review_text: str = Form(...), db: Session = Depends(get_db)):
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    user = current_user(db)
    existing = db.query(Review).filter(Review.user_id == user.id, Review.recipe_id == recipe_id).first()
    if existing:
        existing.stars = stars
        existing.review_text = review_text
    else:
        db.add(Review(user_id=user.id, recipe_id=recipe_id, stars=stars, review_text=review_text))
    db.commit()
    emit_event(db, "review.created", "recipe", recipe_id, {"user_id": user.id, "recipe_id": recipe_id})
    process_badge_events(db)
    recalculate_recipe_metrics(db, recipe)
    return RedirectResponse(url=f"/recipes/{recipe.slug}", status_code=303)


@router.post("/recipes/{recipe_id}/favorite")
def toggle_favorite(recipe_id: int, db: Session = Depends(get_db)):
    user = current_user(db)
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    existing = db.query(Favorite).filter(Favorite.user_id == user.id, Favorite.recipe_id == recipe_id).first()
    if existing:
        db.delete(existing)
    else:
        db.add(Favorite(user_id=user.id, recipe_id=recipe_id))
    db.commit()
    recalculate_recipe_metrics(db, recipe)
    return RedirectResponse(url=f"/recipes/{recipe.slug}", status_code=303)


@router.post("/recipes/{recipe_id}/flavor-vote")
def vote_flavor(recipe_id: int, flavors: list[str] = Form([]), db: Session = Depends(get_db)):
    user = current_user(db)
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    db.query(FlavorVote).filter(FlavorVote.user_id == user.id, FlavorVote.recipe_id == recipe_id).delete()
    for flavor in flavors:
        db.add(FlavorVote(user_id=user.id, recipe_id=recipe_id, flavor=flavor, weight=1.0))
    db.commit()
    return RedirectResponse(url=f"/recipes/{recipe.slug}", status_code=303)


@router.post("/recipes/{recipe_id}/difficulty-vote")
def vote_difficulty(recipe_id: int, difficulty: str = Form(...), db: Session = Depends(get_db)):
    user = current_user(db)
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    existing = db.query(DifficultyVote).filter(DifficultyVote.user_id == user.id, DifficultyVote.recipe_id == recipe_id).first()
    if existing:
        existing.difficulty = difficulty
    else:
        db.add(DifficultyVote(user_id=user.id, recipe_id=recipe_id, difficulty=difficulty))
    db.commit()
    recalculate_recipe_metrics(db, recipe)
    return RedirectResponse(url=f"/recipes/{recipe.slug}", status_code=303)


@router.get("/shake", response_class=RedirectResponse)
def random_recipe(db: Session = Depends(get_db)):
    recipe = shake_to_surprise(db)
    if not recipe:
        return RedirectResponse(url="/", status_code=303)
    return RedirectResponse(url=f"/recipes/{recipe.slug}", status_code=303)


@router.get("/profile", response_class=HTMLResponse)
def profile(request: Request, db: Session = Depends(get_db)):
    user = current_user(db)
    badges = db.query(UserBadge).filter(UserBadge.user_id == user.id).all()
    favorites = db.query(Favorite).options(joinedload(Favorite.recipe)).filter(Favorite.user_id == user.id).all()
    return templates.TemplateResponse("profile.html", {
        "request": request,
        "user": user,
        "badges": badges,
        "favorites": favorites,
    })


@router.get("/r/{share_slug}", response_class=RedirectResponse)
def share_redirect(share_slug: str, db: Session = Depends(get_db)):
    if "-" not in share_slug:
        return RedirectResponse(url="/", status_code=303)
    *slug_parts, token = share_slug.split("-")
    slug = "-".join(slug_parts)
    recipe = db.query(Recipe).filter(Recipe.slug == slug, Recipe.share_token == token).first()
    if not recipe:
        return RedirectResponse(url="/", status_code=303)
    return RedirectResponse(url=f"/recipes/{recipe.slug}", status_code=303)
