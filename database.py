import os
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, DateTime, ForeignKey
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

# .env dosyasını yükle
load_dotenv()

# Esnek Veritabanı URL'si: PostgreSQL yoksa SQLite'a geri çekil
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "sqlite:///./credit_score.db"
)

# Engine oluşturulması
# SQLite için "check_same_thread" argümanı gereklidir, PostgreSQL için yoksayılır
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)

# Session ve Base Tanımlamaları
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Customer(Base):
    """
    Müşteri demografik ve finansal bilgilerini saklayan tablo.
    """
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    age = Column(Integer, nullable=False)
    annual_income = Column(Float, nullable=False)
    employment_years = Column(Integer, nullable=False)
    housing_status = Column(String(20), nullable=False)  # RENT, OWN, MORTGAGE, OTHER
    credit_history_length = Column(Integer, nullable=False)  # Yıl cinsinden
    existing_debts = Column(Float, nullable=False)  # Toplam borç miktarı
    created_at = Column(DateTime, default=datetime.utcnow)

    # İlişkiler
    applications = relationship("CreditApplication", back_populates="customer", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Customer(id={self.id}, name='{self.first_name} {self.last_name}', email='{self.email}')>"


class CreditApplication(Base):
    """
    Müşterinin yaptığı kredi başvurularını ve otomatik sistem kararlarını saklayan tablo.
    """
    __tablename__ = "credit_applications"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    loan_amount = Column(Float, nullable=False)
    loan_purpose = Column(String(50), nullable=False)  # PERSONAL, EDUCATION, HOME_IMPROVEMENT, etc.
    interest_rate = Column(Float, nullable=False)
    term_months = Column(Integer, nullable=False)
    
    # ML & Analitik Sonuçları
    credit_score = Column(Float, nullable=True)  # İstatistiksel / ML temelli hesaplanan kredi skoru
    risk_segment = Column(String(20), nullable=True)  # Low Risk, Medium Risk, High Risk (K-Means kümesi)
    approval_status = Column(String(20), default="PENDING")  # APPROVED, REJECTED, PENDING (Lojistik Regresyon)
    approval_probability = Column(Float, nullable=True)  # Lojistik regresyon olasılık değeri
    
    applied_at = Column(DateTime, default=datetime.utcnow)

    # İlişkiler
    customer = relationship("Customer", back_populates="applications")

    def __repr__(self):
        return f"<CreditApplication(id={self.id}, customer_id={self.customer_id}, status='{self.approval_status}')>"


def init_db():
    """
    Veritabanı tablolarını oluşturur.
    """
    Base.metadata.create_all(bind=engine)


def get_db():
    """
    FastAPI Dependency injection ve session yönetimi için veritabanı session yield eder.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
