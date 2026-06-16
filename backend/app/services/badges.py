import json
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..models import Badge, UserBadge, DomainEvent, Recipe, Review


def emit_event(db: Session, event_type: str, aggregate_type: str, aggregate_id: int, payload: dict):
    event = DomainEvent(
        event_type=event_type,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        payload_json=json.dumps(payload),
    )
    db.add(event)
    db.commit()


def award_badge_if_missing(db: Session, user_id: int, code: str):
    badge = db.query(Badge).filter(Badge.code == code).first()
    if not badge:
        return
    exists = db.query(UserBadge).filter(UserBadge.user_id == user_id, UserBadge.badge_id == badge.id).first()
    if exists:
        return
    db.add(UserBadge(user_id=user_id, badge_id=badge.id))
    db.commit()


def process_badge_events(db: Session):
    events = db.query(DomainEvent).filter(DomainEvent.processed == False).order_by(DomainEvent.id.asc()).all()
    for event in events:
        payload = json.loads(event.payload_json)

        if event.event_type == "recipe.created":
            recipe_count = db.query(func.count(Recipe.id)).filter(Recipe.user_id == payload["user_id"]).scalar() or 0
            if recipe_count >= 1:
                award_badge_if_missing(db, payload["user_id"], "first_recipe")

        if event.event_type == "review.created":
            review_count = db.query(func.count(Review.id)).filter(Review.user_id == payload["user_id"]).scalar() or 0
            if review_count >= 10:
                award_badge_if_missing(db, payload["user_id"], "ten_reviews")

        if event.event_type == "weekly_feature.won":
            award_badge_if_missing(db, payload["user_id"], "weekly_winner")

        event.processed = True
        db.add(event)

    db.commit()
