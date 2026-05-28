import os
from contextlib import asynccontextmanager
import joblib
import pandas as pd
import numpy as np
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from database import get_db, init_db, Customer, CreditApplication

# ==========================================
# ML Model Yükleme ve Hata Kontrolü
# ==========================================
models = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Veritabanını hazırla
    init_db()
    
    # Modelleri diskten yükle
    model_paths = {
        "kmeans_scaler": "models/kmeans_scaler.pkl",
        "kmeans": "models/kmeans_model.pkl",
        "cluster_mapping": "models/cluster_mapping.pkl",
        "lr_scaler": "models/lr_scaler.pkl",
        "logistic_model": "models/logistic_model.pkl",
        "model_features": "models/model_features.pkl"
    }
    
    missing_files = [k for k, path in model_paths.items() if not os.path.exists(path)]
    if missing_files:
        print(f"[WARNING] Modeller bulunamadı! Lütfen önce 'train_models.py' scriptini çalıştırın. Eksik dosyalar: {missing_files}")
    else:
        for name, path in model_paths.items():
            models[name] = joblib.load(path)
        print("[SUCCESS] Tüm makine öğrenmesi modelleri başarıyla yüklendi.")
        
    yield
    # Kapanışta yapılacak işlemler (gerekirse)
    models.clear()

app = FastAPI(
    title="Kredi Skoru ve Otomatik Onay API",
    description="Müşteri finansal profiline göre risk segmentasyonu ve otomatik kredi onaylama kararı veren ML tabanlı servis.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Ayarları (Streamlit Frontend için)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# Pydantic Şemaları (Veri Doğrulama)
# ==========================================
class CustomerSchema(BaseModel):
    first_name: str = Field(..., min_length=2, max_length=50, examples=["Mehmet"])
    last_name: str = Field(..., min_length=2, max_length=50, examples=["Öztürk"])
    email: EmailStr = Field(..., examples=["mehmet.ozturk@example.com"])
    age: int = Field(..., ge=18, le=100, examples=[35])
    annual_income: float = Field(..., ge=0, examples=[450000.0])
    employment_years: int = Field(..., ge=0, examples=[8])
    housing_status: str = Field(..., examples=["MORTGAGE"])  # OWN, MORTGAGE, RENT, OTHER
    credit_history_length: int = Field(..., ge=0, examples=[10])
    existing_debts: float = Field(..., ge=0, examples=[25000.0])

class CreditApplicationSchema(BaseModel):
    loan_amount: float = Field(..., ge=1000, examples=[100000.0])
    loan_purpose: str = Field(..., examples=["PERSONAL"])  # PERSONAL, EDUCATION, HOME_IMPROVEMENT, etc.
    interest_rate: float = Field(..., ge=0.1, examples=[2.15])
    term_months: int = Field(..., ge=1, le=120, examples=[36])

class PredictionRequest(BaseModel):
    customer: CustomerSchema
    application: CreditApplicationSchema

class PredictionResponse(BaseModel):
    customer_id: int
    application_id: int
    credit_score: float
    risk_segment: str
    approval_status: str
    approval_probability: float

# ==========================================
# Yardımcı Hesaplama Fonksiyonları
# ==========================================
def calculate_fico_score(
    income: float, 
    exp_years: int, 
    hist_len: int, 
    housing: str, 
    debts: float
) -> float:
    """
    FICO benzeri kurallı Kredi Skoru (300-850) hesaplama mantığı.
    """
    score = 500.0
    
    # 1. Gelir Etkisi (Max +100 puan)
    income_score = min(100.0, (income / 150000.0) * 15.0)
    score += income_score
    
    # 2. Tecrübe Etkisi (Max +50 puan)
    exp_score = min(50.0, exp_years * 4.0)
    score += exp_score
    
    # 3. Kredi Geçmişi Etkisi (Max +75 puan)
    hist_score = min(75.0, hist_len * 5.0)
    score += hist_score
    
    # 4. Ev Sahipliği Etkisi (Max +50 puan)
    if housing == "OWN":
        score += 50.0
    elif housing == "MORTGAGE":
        score += 25.0
        
    # 5. Borç / Gelir Oranı (DTI) Etkisi (Max -150 puan)
    dti = debts / max(1.0, income)
    score -= min(150.0, dti * 300.0)
    
    return float(np.clip(score, 300.0, 850.0))

# ==========================================
# API Endpoint'leri
# ==========================================

@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "Kredi Skoru Hesaplama ve Otomatik Onay API Sistemine Hoş Geldiniz.",
        "models_loaded": len(models) > 0
    }

@app.post("/predict", response_model=PredictionResponse)
def predict_credit(payload: PredictionRequest, db: Session = Depends(get_db)):
    # 1. Modeller yüklü mü kontrol et
    if not models:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Makine öğrenmesi modelleri API sunucusunda yüklü değil."
        )
        
    cust_data = payload.customer
    app_data = payload.application
    
    # 2. FICO benzeri kredi skorunu hesapla
    calculated_score = calculate_fico_score(
        income=cust_data.annual_income,
        exp_years=cust_data.employment_years,
        hist_len=cust_data.credit_history_length,
        housing=cust_data.housing_status,
        debts=cust_data.existing_debts
    )
    
    # 3. K-Means ile Risk Segmentasyonunu Tahmin Et
    try:
        # Segmentasyon özellikleri: ["annual_income", "existing_debts", "credit_score"]
        kmeans_raw = np.array([[cust_data.annual_income, cust_data.existing_debts, calculated_score]])
        kmeans_scaled = models["kmeans_scaler"].transform(kmeans_raw)
        cluster_id = models["kmeans"].predict(kmeans_scaled)[0]
        risk_segment = models["cluster_mapping"].get(cluster_id, "Unknown Risk")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"K-Means segmentasyonu sırasında hata oluştu: {str(e)}"
        )
        
    # 4. Lojistik Regresyon ile Kredi Onay Kararını ve Olasılığını Tahmin Et
    try:
        # Feature kolon sıralamasına göre dict oluştur
        feat_dict = {
            "age": cust_data.age,
            "annual_income": cust_data.annual_income,
            "employment_years": cust_data.employment_years,
            "credit_history_length": cust_data.credit_history_length,
            "existing_debts": cust_data.existing_debts,
            "loan_amount": app_data.loan_amount,
            "term_months": app_data.term_months,
            "interest_rate": app_data.interest_rate,
            "credit_score": calculated_score,
            "housing_status_OWN": 1.0 if cust_data.housing_status == "OWN" else 0.0,
            "housing_status_MORTGAGE": 1.0 if cust_data.housing_status == "MORTGAGE" else 0.0,
            "housing_status_RENT": 1.0 if cust_data.housing_status == "RENT" else 0.0
        }
        
        # model_features sıralamasına uygun dizi oluştur
        ordered_features = [feat_dict[feat] for feat in models["model_features"]]
        lr_raw = np.array([ordered_features])
        lr_scaled = models["lr_scaler"].transform(lr_raw)
        
        proba = float(models["logistic_model"].predict_proba(lr_scaled)[0, 1])
        approval_status_str = "APPROVED" if proba >= 0.5 else "REJECTED"
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lojistik regresyon onay kararı sırasında hata oluştu: {str(e)}"
        )
        
    # 5. Sonuçları Veritabanına Kaydet (Katmanlı Yapı Entegrasyonu)
    try:
        # Önce bu emaile sahip müşteri zaten var mı diye bakalım
        db_customer = db.query(Customer).filter(Customer.email == cust_data.email).first()
        
        if not db_customer:
            db_customer = Customer(
                first_name=cust_data.first_name,
                last_name=cust_data.last_name,
                email=cust_data.email,
                age=cust_data.age,
                annual_income=cust_data.annual_income,
                employment_years=cust_data.employment_years,
                housing_status=cust_data.housing_status,
                credit_history_length=cust_data.credit_history_length,
                existing_debts=cust_data.existing_debts
            )
            db.add(db_customer)
            db.commit()
            db.refresh(db_customer)
            
        db_app = CreditApplication(
            customer_id=db_customer.id,
            loan_amount=app_data.loan_amount,
            loan_purpose=app_data.loan_purpose,
            interest_rate=app_data.interest_rate,
            term_months=app_data.term_months,
            credit_score=calculated_score,
            risk_segment=risk_segment,
            approval_status=approval_status_str,
            approval_probability=proba
        )
        db.add(db_app)
        db.commit()
        db.refresh(db_app)
        
        return PredictionResponse(
            customer_id=db_customer.id,
            application_id=db_app.id,
            credit_score=calculated_score,
            risk_segment=risk_segment,
            approval_status=approval_status_str,
            approval_probability=proba
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Kayıt işlemi sırasında veritabanı hatası oluştu: {str(e)}"
        )

@app.get("/applications")
def get_applications(limit: int = 50, db: Session = Depends(get_db)):
    """
    Geçmiş başvuruları listeler.
    """
    results = db.query(CreditApplication, Customer).join(
        Customer, Customer.id == CreditApplication.customer_id
    ).order_by(CreditApplication.applied_at.desc()).limit(limit).all()
    
    app_list = []
    for app, cust in results:
        app_list.append({
            "application_id": app.id,
            "customer_name": f"{cust.first_name} {cust.last_name}",
            "email": cust.email,
            "annual_income": cust.annual_income,
            "existing_debts": cust.existing_debts,
            "loan_amount": app.loan_amount,
            "loan_purpose": app.loan_purpose,
            "credit_score": app.credit_score,
            "risk_segment": app.risk_segment,
            "approval_status": app.approval_status,
            "approval_probability": app.approval_probability,
            "applied_at": app.applied_at
        })
    return app_list

@app.get("/metrics")
def get_metrics(db: Session = Depends(get_db)):
    """
    Gösterge paneli istatistikleri için metrikleri döner.
    """
    total_apps = db.query(CreditApplication).count()
    if total_apps == 0:
        return {
            "total_applications": 0,
            "approval_rate": 0,
            "risk_segment_distribution": {},
            "average_credit_score": 0
        }
        
    approved_apps = db.query(CreditApplication).filter(CreditApplication.approval_status == "APPROVED").count()
    
    from sqlalchemy import func
    avg_score_res = db.query(func.avg(CreditApplication.credit_score)).scalar() or 0
    
    # Risk segmenti dağılımı
    segments = db.query(
        CreditApplication.risk_segment, func.count(CreditApplication.id)
    ).group_by(CreditApplication.risk_segment).all()
    
    segment_dist = {seg: count for seg, count in segments if seg is not None}
    
    return {
        "total_applications": total_apps,
        "approval_rate": round(approved_apps / total_apps, 4),
        "average_credit_score": round(float(avg_score_res), 1),
        "risk_segment_distribution": segment_dist
    }
