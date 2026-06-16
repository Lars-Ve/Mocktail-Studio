# Mocktail Studio V1

Community-gedreven platform voor alcoholvrije drankjes.

## Architectuurkeuze
- **Backend:** FastAPI + SQLAlchemy
- **Frontend:** server-rendered HTML templates + CSS
- **Database V1:** SQLite (swapbaar naar PostgreSQL zonder modelwijzigingen)
- **Stijl:** custom CSS tokens i.p.v. zwaar framework, zodat de zomeravond / kleurrijk-keukenblad sfeer exact te sturen blijft.

## Waarom deze stack voor V1?
- Snel te prototypen en toch production-friendly.
- Server-rendered HTML maakt de eerste versie eenvoudig, SEO-vriendelijk en beheersbaar.
- SQLAlchemy-model is al voorbereid op schaalbare relationele queries, badges, weekly features en uitbreidingen zoals nutrition, AI suggestions en meertaligheid.

## Kernlogica
### Smaakprofiel-aggregatie
- Submitter-tags tellen dubbel (`source=submitter`, factor 2.0).
- Community-votes tellen enkel (`factor 1.0`).
- Per recept berekenen we percentages per smaak.
- Smaken met >= 18% verschijnen als dominante tags.

### Moeilijkheidsgraad
- Auteur kiest initieel label.
- Dat telt als 3 virtuele stemmen.
- Elke community-vote telt als 1.
- Het label met hoogste score wordt `effective_difficulty`.

### Mocktail van de week
- Kandidaten: gepubliceerde recepten met minimaal 1 review en rating >= 3.5.
- Score combineert kwaliteit, review-trust, favorites en een verkenningsboost voor nieuwere / minder vaak beoordeelde recepten.
- Resultaat wordt per week vastgelegd in `weekly_features`.

### Shake to Surprise
- Sluit recepten uit die echt slecht presteren: `avg_rating < 2.5` wanneer er minstens 3 reviews zijn.

### Badges (event-driven)
- Elke belangrijke actie schrijft een event naar `domain_events`.
- Badge processor leest events en kent badges toe zonder business logic hard in de request flow te veren.

## Run lokaal
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open daarna `http://127.0.0.1:8000`.
