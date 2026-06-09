import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class GenerationStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class GenerationScene(Base):
    __tablename__ = "generation_scenes"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str | None] = mapped_column(String(255))
    scenario: Mapped[str | None] = mapped_column(Text)
    status: Mapped[GenerationStatus] = mapped_column(
        Enum(GenerationStatus, native_enum=False), default=GenerationStatus.PENDING
    )
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    cuts: Mapped[list["GenerationCut"]] = relationship(
        "GenerationCut", back_populates="scene", order_by="GenerationCut.order"
    )


class GenerationCut(Base):
    __tablename__ = "generation_cuts"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    scene_id: Mapped[str] = mapped_column(ForeignKey("generation_scenes.id"), nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    image_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    video_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    duration_sec: Mapped[float] = mapped_column(Float, default=5.0)
    status: Mapped[GenerationStatus] = mapped_column(
        Enum(GenerationStatus, native_enum=False), default=GenerationStatus.PENDING
    )

    scene: Mapped["GenerationScene"] = relationship("GenerationScene", back_populates="cuts")
    images: Mapped[list["CutImage"]] = relationship("CutImage", back_populates="cut")
    videos: Mapped[list["CutVideo"]] = relationship("CutVideo", back_populates="cut")


class CutImage(Base):
    __tablename__ = "cut_images"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    cut_id: Mapped[str] = mapped_column(ForeignKey("generation_cuts.id"), nullable=False)
    kie_task_id: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[GenerationStatus] = mapped_column(
        Enum(GenerationStatus, native_enum=False), default=GenerationStatus.PENDING
    )
    image_url: Mapped[str | None] = mapped_column(Text)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    cut: Mapped["GenerationCut"] = relationship("GenerationCut", back_populates="images")
    videos: Mapped[list["CutVideo"]] = relationship("CutVideo", back_populates="cut_image")


class CutVideo(Base):
    __tablename__ = "cut_videos"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    cut_id: Mapped[str] = mapped_column(ForeignKey("generation_cuts.id"), nullable=False)
    cut_image_id: Mapped[str] = mapped_column(ForeignKey("cut_images.id"), nullable=False)
    kie_task_id: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[GenerationStatus] = mapped_column(
        Enum(GenerationStatus, native_enum=False), default=GenerationStatus.PENDING
    )
    video_url: Mapped[str | None] = mapped_column(Text)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    cut: Mapped["GenerationCut"] = relationship("GenerationCut", back_populates="videos")
    cut_image: Mapped["CutImage"] = relationship("CutImage", back_populates="videos")
