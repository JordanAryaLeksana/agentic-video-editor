from sqlalchemy import BigInteger, CheckConstraint, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class MediaAssetRecord(Base):
    __tablename__ = "media_assets"

    __table_args__ = (
        CheckConstraint(
            "size_bytes > 0",
            name="ck_media_assets_size_positive",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    original_filename: Mapped[str] = mapped_column(String, nullable=False)

    storage_key: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
