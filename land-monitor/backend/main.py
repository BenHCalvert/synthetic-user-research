"""
Land Parcel Monitor — FastAPI application.

Startup sequence:
  1. Initialize DB
  2. Run all scrapers once
  3. Schedule recurring scrapes
  4. Serve React frontend as static files at /
  5. Expose REST API at /api/
"""

import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from config import (
    HOST, PORT, DATA_DIR,
    LANDWATCH_INTERVAL_HOURS, HOMES_INTERVAL_HOURS, IDL_INTERVAL_HOURS,
)
from models import get_engine, init_db, get_session, Listing, PriceHistory, IDLAuction
from scorer import score_listing
from alerts import send_listing_alert, send_idl_alert
from scrapers.landwatch import scrape_landwatch
from scrapers.homes import scrape_homes
from scrapers.idl import scrape_idl

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

engine = get_engine()
scheduler = AsyncIOScheduler()

FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"


# ---------------------------------------------------------------------------
# Scrape + ingest logic
# ---------------------------------------------------------------------------

async def ingest_listings(raw_listings: list[dict], session: Session) -> int:
    new_count = 0
    for raw in raw_listings:
        url = raw.get("url")
        if not url:
            continue
        existing = session.query(Listing).filter_by(url=url).first()
        if existing:
            _update_listing(existing, raw, session)
        else:
            listing = _create_listing(raw)
            session.add(listing)
            session.flush()
            session.add(PriceHistory(listing_id=listing.id, price=listing.price or 0))
            new_count += 1
            if listing.score and listing.score >= 40:
                await send_listing_alert(raw | {"score": listing.score})
    session.commit()
    return new_count


def _create_listing(raw: dict) -> Listing:
    price = raw.get("price")
    acreage = raw.get("acreage")
    ppa = round(price / acreage, 2) if price and acreage and acreage > 0 else None
    sc = score_listing(raw)
    return Listing(
        url=raw["url"],
        source=raw.get("source", "Unknown"),
        title=raw.get("title"),
        address=raw.get("address"),
        zone=raw.get("zone"),
        price=price,
        acreage=acreage,
        price_per_acre=ppa,
        access_type=raw.get("access_type"),
        water=raw.get("water"),
        utilities=raw.get("utilities"),
        nf_adjacency=raw.get("nf_adjacency"),
        is_mining_claim=raw.get("is_mining_claim", False),
        in_snra=raw.get("in_snra", False),
        description=raw.get("description"),
        agent_name=raw.get("agent_name"),
        agent_contact=raw.get("agent_contact"),
        thumbnail_url=raw.get("thumbnail_url"),
        status=raw.get("status", "Active"),
        score=sc,
        is_new=True,
    )


def _update_listing(listing: Listing, raw: dict, session: Session) -> None:
    new_price = raw.get("price")
    if new_price and new_price != listing.price:
        session.add(PriceHistory(listing_id=listing.id, price=new_price))
        listing.price = new_price
        acreage = listing.acreage or raw.get("acreage")
        listing.price_per_acre = round(new_price / acreage, 2) if acreage and acreage > 0 else None

    new_status = raw.get("status")
    if new_status and new_status != listing.status:
        listing.status = new_status
        if new_status == "Sold" and new_price:
            listing.sold_price = new_price

    listing.date_last_updated = datetime.now(timezone.utc)
    # Re-score with latest data
    listing.score = score_listing({
        "price": listing.price,
        "acreage": listing.acreage,
        "price_per_acre": listing.price_per_acre,
        "nf_adjacency": listing.nf_adjacency,
        "access_type": listing.access_type,
        "water": listing.water,
        "utilities": listing.utilities,
        "zone": listing.zone,
        "in_snra": listing.in_snra,
        "is_mining_claim": listing.is_mining_claim,
    })


async def ingest_idl(raw_auctions: list[dict], session: Session) -> int:
    new_count = 0
    for raw in raw_auctions:
        url = raw.get("url")
        if not url:
            continue
        existing = session.query(IDLAuction).filter_by(url=url).first()
        if existing:
            existing.date_last_checked = datetime.now(timezone.utc)
        else:
            auction = IDLAuction(
                url=url,
                title=raw.get("title"),
                description=raw.get("description"),
                location=raw.get("location"),
                acreage=raw.get("acreage"),
                asking_price=raw.get("asking_price"),
                status=raw.get("status", "Active"),
                date_posted=raw.get("date_posted"),
                raw_snippet=raw.get("raw_snippet"),
                is_new=True,
            )
            session.add(auction)
            new_count += 1
            await send_idl_alert(raw)
    session.commit()
    return new_count


async def run_landwatch():
    logger.info("Starting LandWatch scrape...")
    with get_session(engine) as session:
        listings = await scrape_landwatch()
        n = await ingest_listings(listings, session)
        logger.info("LandWatch: %d new listings ingested", n)


async def run_homes():
    logger.info("Starting Homes.com scrape...")
    with get_session(engine) as session:
        listings = await scrape_homes()
        n = await ingest_listings(listings, session)
        logger.info("Homes.com: %d new listings ingested", n)


async def run_idl():
    logger.info("Starting IDL scrape...")
    with get_session(engine) as session:
        auctions = scrape_idl()
        n = await ingest_idl(auctions, session)
        logger.info("IDL: %d new auction items ingested", n)


async def run_all_scrapers():
    await asyncio.gather(run_landwatch(), run_homes(), run_idl(), return_exceptions=True)


# ---------------------------------------------------------------------------
# App lifecycle
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db(engine)
    logger.info("Database initialized at %s", DATA_DIR)

    # Initial scrape on startup
    asyncio.create_task(run_all_scrapers())

    # Recurring schedule
    scheduler.add_job(run_landwatch, "interval", hours=LANDWATCH_INTERVAL_HOURS, id="landwatch")
    scheduler.add_job(run_homes, "interval", hours=HOMES_INTERVAL_HOURS, id="homes")
    scheduler.add_job(run_idl, "interval", hours=IDL_INTERVAL_HOURS, id="idl")
    scheduler.start()
    logger.info("Scheduler started")

    yield

    scheduler.shutdown(wait=False)


app = FastAPI(title="Land Parcel Monitor", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Dependency
# ---------------------------------------------------------------------------

def get_db():
    with get_session(engine) as session:
        yield session


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class ListingPatch(BaseModel):
    notes: str | None = None
    is_starred: bool | None = None
    is_new: bool | None = None


class ScrapeRequest(BaseModel):
    source: str = "all"  # all | landwatch | homes | idl


# ---------------------------------------------------------------------------
# API routes
# ---------------------------------------------------------------------------

@app.get("/api/stats")
def get_stats(db: Session = Depends(get_db)) -> dict:
    from sqlalchemy import func

    total = db.query(func.count(Listing.id)).scalar() or 0
    new_count = db.query(func.count(Listing.id)).filter(Listing.is_new == True).scalar() or 0
    active = db.query(func.count(Listing.id)).filter(Listing.status == "Active").scalar() or 0
    avg_score = db.query(func.avg(Listing.score)).filter(
        Listing.status == "Active", Listing.score.isnot(None)
    ).scalar()
    avg_price = db.query(func.avg(Listing.price)).filter(
        Listing.status == "Active", Listing.price.isnot(None)
    ).scalar()
    idl_new = db.query(func.count(IDLAuction.id)).filter(IDLAuction.is_new == True).scalar() or 0

    return {
        "total_listings": total,
        "active_listings": active,
        "new_listings": new_count,
        "avg_score": round(avg_score, 1) if avg_score else None,
        "avg_price": int(avg_price) if avg_price else None,
        "idl_new": idl_new,
    }


@app.get("/api/listings")
def get_listings(
    db: Session = Depends(get_db),
    zone: list[str] = Query(default=[]),
    source: list[str] = Query(default=[]),
    status: list[str] = Query(default=[]),
    min_score: float = Query(default=0),
    max_price: int = Query(default=0),
    min_price: int = Query(default=0),
    min_acreage: float = Query(default=0),
    max_acreage: float = Query(default=0),
    nf_adjacency: list[str] = Query(default=[]),
    is_new: bool | None = Query(default=None),
    is_starred: bool | None = Query(default=None),
    sort: str = Query(default="score_desc"),
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0),
) -> dict[str, Any]:
    from sqlalchemy import desc, asc

    q = db.query(Listing)

    if zone:
        q = q.filter(Listing.zone.in_(zone))
    if source:
        q = q.filter(Listing.source.in_(source))
    if status:
        q = q.filter(Listing.status.in_(status))
    else:
        q = q.filter(Listing.status != "Sold")
    if min_score > 0:
        q = q.filter(Listing.score >= min_score)
    if max_price > 0:
        q = q.filter(Listing.price <= max_price)
    if min_price > 0:
        q = q.filter(Listing.price >= min_price)
    if min_acreage > 0:
        q = q.filter(Listing.acreage >= min_acreage)
    if max_acreage > 0:
        q = q.filter(Listing.acreage <= max_acreage)
    if nf_adjacency:
        q = q.filter(Listing.nf_adjacency.in_(nf_adjacency))
    if is_new is not None:
        q = q.filter(Listing.is_new == is_new)
    if is_starred is not None:
        q = q.filter(Listing.is_starred == is_starred)

    total = q.count()

    sort_map = {
        "score_desc": desc(Listing.score),
        "score_asc": asc(Listing.score),
        "price_asc": asc(Listing.price),
        "price_desc": desc(Listing.price),
        "date_desc": desc(Listing.date_first_seen),
        "date_asc": asc(Listing.date_first_seen),
        "ppa_asc": asc(Listing.price_per_acre),
    }
    q = q.order_by(sort_map.get(sort, desc(Listing.score)))
    listings = q.offset(offset).limit(limit).all()

    return {"total": total, "listings": [_listing_to_dict(l) for l in listings]}


@app.get("/api/listings/{listing_id}")
def get_listing(listing_id: int, db: Session = Depends(get_db)) -> dict:
    listing = db.query(Listing).filter_by(id=listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return _listing_to_dict(listing, include_description=True)


@app.patch("/api/listings/{listing_id}")
def patch_listing(listing_id: int, body: ListingPatch, db: Session = Depends(get_db)) -> dict:
    listing = db.query(Listing).filter_by(id=listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if body.notes is not None:
        listing.notes = body.notes
    if body.is_starred is not None:
        listing.is_starred = body.is_starred
    if body.is_new is not None:
        listing.is_new = body.is_new
    db.commit()
    return _listing_to_dict(listing)


@app.get("/api/listings/{listing_id}/price-history")
def get_price_history(listing_id: int, db: Session = Depends(get_db)) -> list[dict]:
    rows = (
        db.query(PriceHistory)
        .filter_by(listing_id=listing_id)
        .order_by(PriceHistory.recorded_at)
        .all()
    )
    return [{"price": r.price, "date": r.recorded_at.isoformat()} for r in rows]


@app.get("/api/auctions")
def get_auctions(
    db: Session = Depends(get_db),
    is_new: bool | None = Query(default=None),
) -> list[dict]:
    q = db.query(IDLAuction).order_by(IDLAuction.date_first_seen.desc())
    if is_new is not None:
        q = q.filter(IDLAuction.is_new == is_new)
    return [_auction_to_dict(a) for a in q.all()]


@app.post("/api/scrape")
async def trigger_scrape(body: ScrapeRequest) -> dict:
    source = body.source.lower()
    if source == "landwatch":
        asyncio.create_task(run_landwatch())
    elif source == "homes":
        asyncio.create_task(run_homes())
    elif source == "idl":
        asyncio.create_task(run_idl())
    else:
        asyncio.create_task(run_all_scrapers())
    return {"status": "scrape started", "source": source}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _listing_to_dict(l: Listing, include_description: bool = False) -> dict:
    d = {
        "id": l.id,
        "url": l.url,
        "source": l.source,
        "title": l.title,
        "address": l.address,
        "zone": l.zone,
        "price": l.price,
        "acreage": l.acreage,
        "price_per_acre": l.price_per_acre,
        "access_type": l.access_type,
        "water": l.water,
        "utilities": l.utilities,
        "nf_adjacency": l.nf_adjacency,
        "is_mining_claim": l.is_mining_claim,
        "in_snra": l.in_snra,
        "agent_name": l.agent_name,
        "thumbnail_url": l.thumbnail_url,
        "status": l.status,
        "sold_price": l.sold_price,
        "score": l.score,
        "is_new": l.is_new,
        "is_starred": l.is_starred,
        "notes": l.notes,
        "date_first_seen": l.date_first_seen.isoformat() if l.date_first_seen else None,
        "date_last_updated": l.date_last_updated.isoformat() if l.date_last_updated else None,
    }
    if include_description:
        d["description"] = l.description
    return d


def _auction_to_dict(a: IDLAuction) -> dict:
    return {
        "id": a.id,
        "url": a.url,
        "title": a.title,
        "description": a.description,
        "location": a.location,
        "acreage": a.acreage,
        "asking_price": a.asking_price,
        "status": a.status,
        "date_posted": a.date_posted,
        "date_first_seen": a.date_first_seen.isoformat() if a.date_first_seen else None,
        "is_new": a.is_new,
    }


# ---------------------------------------------------------------------------
# Frontend SPA
# ---------------------------------------------------------------------------

if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")

    @app.get("/")
    @app.get("/{full_path:path}")
    def serve_spa(full_path: str = ""):
        index = FRONTEND_DIST / "index.html"
        if index.exists():
            return FileResponse(str(index))
        return {"message": "Frontend not built. Run: cd frontend && npm run build"}
else:
    @app.get("/")
    def root():
        return {"message": "Land Parcel Monitor API running. Build frontend with: cd frontend && npm run build"}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=HOST, port=PORT, reload=False)
