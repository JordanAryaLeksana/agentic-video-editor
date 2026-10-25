from sqlalchemy import BigInteger, CheckConstraint, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, UniqueConstraint


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


class ProcessingJobRecord(Base):
    __tablename__ = "processing_job"

    __table_args__ = (
        CheckConstraint(
            "max_attempts >= 1",
            name="ck_processing_jobs_max_attempts",
        ),
        CheckConstraint(
            "attempts >= 0 AND attempts <= max_attempts",
            name="ck_processing_jobs_attempts",
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
    )

    media_id: Mapped[str] = mapped_column(
        ForeignKey("media_assets.id"),
        nullable=False,
        index=True,
    )

    job_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    max_attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=3,
    )

    

class ProcessingArtifactRecord(Base):
    __tablename__ = "processing_artifacts"

    __table_args__ = (
        CheckConstraint(
            "size_bytes > 0",
            name="ck_artifact_size_positive",
        ),
        UniqueConstraint(
            "job_id",
            "artifact_type",
            name="uq_artifact_job_type",
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
    )

    job_id: Mapped[str] = mapped_column(
        ForeignKey("processing_job.id"),
        nullable=False,
        index=True,
    )

    artifact_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    storage_key: Mapped[str] = mapped_column(
        String,
        unique=True,
        nullable=False,
    )

    size_bytes: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )
