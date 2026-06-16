from __future__ import annotations
from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc
from ..models import Recipe, WeeklyFeature
from .badges import emit_event


def monday_of_week(day: date | None = None) -> date:
    day = day or date.today()
    return day - timedelta(days=day.weekday())


def compute_weekly_scores(recipes: list[Recipe]):
    scored = []
    for recipe in recipes:
        freshness_boost = 1.4 if recipe.review_count < 5 else 1.0
        quality = recipe.avg_rating * 0.55
        trust = min(recipe.review_count / 8, 1.0) * 2.5
        saves = recipe.favorite_count * 0.10
        exploration = freshness_boost * 0.65
        total = round(quality + trust + saves + exploration, 4)
        scored.append((recipe, total))
    return sorted(scored, key=lambda item: item[1], reverse=True)


def select_weekly_feature(db: Session):
    week_start = monday_of_week()
    existing = db.query(WeeklyFeature).filter(WeeklyFeature.week_start == week_start).first()
    if existing:
        return existing

    candidates = db.query(Recipe).filter(Recipe.is_published == True, Recipe.review_count >= 1, Recipe.avg_rating >= 3.5).all()
    ranked = compute_weekly_scores(candidates)
    if not ranked:
        return None

    top_recipe, _ = ranked[0]
    feature = WeeklyFeature(week_start=week_start, recipe_id=top_recipe.id, rank=1, reason="Beste mix van kwaliteit, votes en ontdekbaarheid")
    db.add(feature)
    db.commit()
    db.refresh(feature)

    emit_event(db, "weekly_feature.won", "recipe", top_recipe.id, {"user_id": top_recipe.user_id, "recipe_id": top_recipe.id})

    for idx, (recipe, _) in enumerate(ranked[1:5], start=2):
        db.add(WeeklyFeature(week_start=week_start, recipe_id=recipe.id, rank=idx, reason="Populaire alternatieve keuze"))
    db.commit()
    return feature


def get_homepage_featured(db: Session):
    week_start = monday_of_week()
    all_items = db.query(WeeklyFeature).filter(WeeklyFeature.week_start == week_start).order_by(WeeklyFeature.rank.asc()).all()
    if all_items:
        return all_items[0], all_items[1:]

    feature = select_weekly_feature(db)
    if not feature:
        return None, []
    all_items = db.query(WeeklyFeature).filter(WeeklyFeature.week_start == week_start).order_by(WeeklyFeature.rank.asc()).all()
    return all_items[0], all_items[1:]


def shake_to_surprise(db: Session):
    candidates = db.query(Recipe).filter(
        Recipe.is_published == True,
        ((Recipe.review_count < 3) | (Recipe.avg_rating >= 2.5))
    ).order_by(Recipe.created_at.desc()).all()
    if not candidates:
        return None
    # deterministic enough for V1 demo without JS: pick middle-ish candidate to avoid always top result.
    return candidates[len(candidates) // 2]
