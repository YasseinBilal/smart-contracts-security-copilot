from sqlalchemy import String, Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Finding(Base):
    __tablename__ = "findings"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    scan_id: Mapped[str] = mapped_column(String, ForeignKey("scans.id"), nullable=False)
    filename: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    severity: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    affected_lines: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    affected_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendation: Mapped[str] = mapped_column(Text, nullable=False, default="")
    exploit_scenario: Mapped[str] = mapped_column(Text, nullable=False, default="")
    test_stub: Mapped[str | None] = mapped_column(Text, nullable=True)
    cvl_property: Mapped[str | None] = mapped_column(Text, nullable=True)
    false_positive: Mapped[bool] = mapped_column(Boolean, default=False)
    confidence: Mapped[str] = mapped_column(String, nullable=False, default="MEDIUM")

    scan: Mapped["Scan"] = relationship("Scan", back_populates="findings")  # noqa: F821
