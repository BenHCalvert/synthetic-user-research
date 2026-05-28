from datetime import datetime, timezone
from sqlalchemy import (
    Boolean, DateTime, Float, ForeignKey, Integer, String, Text,
    create_engine, UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, Session

from config import DATABASE_URL, DATA_DIR


class Base(DeclarativeBase):
    pass


class Listing(Base):
    __tablename__ = "listings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    url: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    source: Mapped[str] = mapped_column(String, nullable=False)  # LandWatch | Homes | IDL | Manual

    title: Mapped[str | None] = mapped_column(String)
    address: Mapped[str | None] = mapped_column(String)
    zone: Mapped[str | None] = mapped_column(String)  # one of ZONES keys

    price: Mapped[int | None] = mapped_column(Integer)
    acreage: Mapped[float | None] = mapped_column(Float)
    price_per_acre: Mapped[float | None] = mapped_column(Float)

    # Keyword-extracted fields
    access_type: Mapped[str | None] = mapped_column(String)   # year_round_paved|year_round_gravel|seasonal|hike_in|unknown
    water: Mapped[str | None] = mapped_column(String)          # drilled_well|creek_river|community|none|unknown
    utilities: Mapped[str | None] = mapped_column(String)      # power|off_grid|unknown
    nf_adjacency: Mapped[str | None] = mapped_column(String)   # inholding|adjacent|near|none

    is_mining_claim: Mapped[bool] = mapped_column(Boolean, default=False)
    in_snra: Mapped[bool] = mapped_column(Boolean, default=False)

    description: Mapped[str | None] = mapped_column(Text)
    agent_name: Mapped[str | None] = mapped_column(String)
    agent_contact: Mapped[str | None] = mapped_column(String)
    thumbnail_url: Mapped[str | None] = mapped_column(String)

    status: Mapped[str] = mapped_column(String, default="Active")  # Active|Under Contract|Sold
    sold_price: Mapped[int | None] = mapped_column(Integer)

    score: Mapped[float | None] = mapped_column(Float)

    is_new: Mapped[bool] = mapped_column(Boolean, default=True)
    is_starred: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text)

    date_first_seen: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    date_last_updated: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    price_history: Mapped[list["PriceHistory"]] = relationship(
        "PriceHistory", back_populates="listing", cascade="all, delete-orphan"
    )


class PriceHistory(Base):
    __tablename__ = "price_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    listing_id: Mapped[int] = mapped_column(Integer, ForeignKey("listings.id"), nullable=False)
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    listing: Mapped["Listing"] = relationship("Listing", back_populates="price_history")


class IDLAuction(Base):
    __tablename__ = "idl_auctions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    url: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    title: Mapped[str | None] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(String)
    acreage: Mapped[float | None] = mapped_column(Float)
    asking_price: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str | None] = mapped_column(String)
    date_posted: Mapped[str | None] = mapped_column(String)
    date_first_seen: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    date_last_checked: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    is_new: Mapped[bool] = mapped_column(Boolean, default=True)
    raw_snippet: Mapped[str | None] = mapped_column(Text)


def get_engine():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False,
    )


def init_db(engine):
    Base.metadata.create_all(engine)


def get_session(engine) -> Session:
    return Session(engine)
