from __future__ import annotations
from collections import Counter
from math import log10
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..models import Recipe, RecipeFlavor, FlavorVote, Review, Favorite, DifficultyVote


FLAVOR_WEIGHTS = {
    "submitter": 2.0,
    "community": 1.0,
}

DIFFICULTIES = ["Makkelijk", "Gemiddeld", "Barista-level"]


def recalculate_recipe_metrics(db: Session, recipe: Recipe) -> Recipe:
    avg_rating, review_count = db.query(func.avg(Review.stars), func.count(Review.id)).filter(Review.recipe_id == recipe.id).one()
    favorite_count = db.query(func.count(Favorite.id)).filter(Favorite.recipe_id == recipe.id).scalar() or 0
    avg_rating = float(avg_rating or 0.0)
    review_count = int(review_count or 0)

    # Popularity balances quality, proof and saves.
    popularity_score = round((avg_rating * 0.55) + (log10(review_count + 1) * 1.7) + (favorite_count * 0.12), 4)

    recipe.avg_rating = avg_rating
    recipe.review_count = review_count
    recipe.favorite_count = favorite_count
    recipe.popularity_score = popularity_score
    recipe.effective_difficulty = compute_effective_difficulty(db, recipe.id, recipe.submitted_difficulty)
    db.add(recipe)
    db.commit()
    db.refresh(recipe)
    return recipe


def aggregate_flavors(db: Session, recipe_id: int):
    submitter_entries = db.query(RecipeFlavor).filter(RecipeFlavor.recipe_id == recipe_id).all()
    community_entries = db.query(FlavorVote).filter(FlavorVote.recipe_id == recipe_id).all()

    scores = Counter()
    total = 0.0

    for entry in submitter_entries:
        weight = entry.weight * FLAVOR_WEIGHTS[entry.source]
        scores[entry.flavor] += weight
        total += weight

    for vote in community_entries:
        weight = vote.weight * FLAVOR_WEIGHTS["community"]
        scores[vote.flavor] += weight
        total += weight

    if total == 0:
        return {"dominant": [], "breakdown": {}}

    breakdown = {flavor: round((value / total) * 100, 1) for flavor, value in scores.items()}
    dominant = [flavor for flavor, pct in sorted(breakdown.items(), key=lambda kv: kv[1], reverse=True) if pct >= 18][:3]
    return {"dominant": dominant, "breakdown": breakdown}


def compute_effective_difficulty(db: Session, recipe_id: int, submitted_difficulty: str) -> str:
    counts = Counter({submitted_difficulty: 3})  # author gets a head start, but not absolute power
    community_votes = db.query(DifficultyVote).filter(DifficultyVote.recipe_id == recipe_id).all()
    for vote in community_votes:
        counts[vote.difficulty] += 1
    best = sorted(counts.items(), key=lambda kv: (-kv[1], DIFFICULTIES.index(kv[0]) if kv[0] in DIFFICULTIES else 999))[0][0]
    return best
