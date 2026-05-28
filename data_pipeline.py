import random
import numpy as np
import pandas as pd
from faker import Faker
from database import SessionLocal, Customer, CreditApplication, init_db

# Tekrarlanabilir sonuçlar için seed ayarı
np.random.seed(42)
random.seed(42)

fake = Faker('tr_TR')  # Türkçe isimler ve veriler için

def generate_correlated_data(num_records=1000):
    print(f"Generating {num_records} synthetic credit records with realistic correlations...")
    
    # 1. Yaş dağılımı (Düzgün normal dağılım, 18-70 yaş arası)
    ages = np.random.normal(loc=40, scale=12, size=num_records).astype(int)
    ages = np.clip(ages, 18, 70)
    
    # 2. İş tecrübesi (Yaşla doğrudan ilişkili: iş tecrübesi < yaş - 18)
    employment_years = []
    for age in ages:
        max_exp = max(0, age - 18)
        # Genç yaşta tecrübe az, yaşlandıkça tecrübe ortalaması ve varyansı artar
        exp = int(np.random.beta(a=2, b=3) * max_exp)
        employment_years.append(exp)
    employment_years = np.array(employment_years)
    
    # 3. Yıllık Gelir (Yaş ve tecrübe ile korelasyonlu)
    # Temel gelir 40.000 TL, her tecrübe yılı geliri artırır, üzerine log-normal gürültü eklenir
    base_income = 180000  # Asgari geçim/temel gelir tabanı
    income_per_exp = 35000
    noise = np.random.lognormal(mean=0, sigma=0.4, size=num_records)
    annual_incomes = (base_income + (employment_years * income_per_exp)) * noise
    annual_incomes = np.round(annual_incomes, -3)  # En yakın binliğe yuvarla
    
    # 4. Ev Sahipliği Durumu (Gelire göre olasılık dağılımı)
    housing_statuses = []
    for income in annual_incomes:
        if income > 800000:
            status = np.random.choice(["OWN", "MORTGAGE", "RENT"], p=[0.5, 0.4, 0.1])
        elif income > 400000:
            status = np.random.choice(["OWN", "MORTGAGE", "RENT"], p=[0.25, 0.5, 0.25])
        else:
            status = np.random.choice(["OWN", "MORTGAGE", "RENT"], p=[0.1, 0.2, 0.7])
        housing_statuses.append(status)
        
    # 5. Kredi Geçmişi Süresi (Yaşla ilişkili, tecrübeden bağımsız değil ama yaş sınırı var)
    credit_histories = []
    for age in ages:
        max_history = max(1, age - 18)
        if max_history > 1:
            history = int(np.random.triangular(1, min(max_history, 5), max_history))
        else:
            history = 1
        credit_histories.append(history)
    credit_histories = np.array(credit_histories)
    
    # 6. Mevcut Borçlar (Gelir ile orantılı)
    # Borç/Gelir Oranı (DTI) %0 ile %60 arasında dağılmıştır.
    dti_ratios = np.random.beta(a=1.5, b=4, size=num_records) * 0.6
    existing_debts = np.round(annual_incomes * dti_ratios, -2)
    
    # 7. Kredi İstek Tutarı (Yıllık Gelirin %10'u ile %50'si arasında)
    loan_amounts = np.round(annual_incomes * np.random.uniform(0.1, 0.5, size=num_records), -3)
    
    # Kredi Amacı Dağılımı
    purposes = ["PERSONAL", "EDUCATION", "HOME_IMPROVEMENT", "DEBT_CONSOLIDATION", "CAR"]
    loan_purposes = np.random.choice(purposes, size=num_records, p=[0.3, 0.15, 0.2, 0.25, 0.1])
    
    # Vade ayları
    terms = [12, 24, 36, 48, 60]
    term_months = np.random.choice(terms, size=num_records, p=[0.1, 0.3, 0.4, 0.1, 0.1])
    
    # Faiz oranları (Vadeye göre hafif artış gösteren baz faiz + rastgelelik)
    interest_rates = []
    for term in term_months:
        base_rate = 1.5 + (term / 60) * 1.5  # %1.5 ile %3.0 arası baz faiz
        rate = round(base_rate + np.random.uniform(-0.3, 0.3), 2)
        interest_rates.append(rate)
    
    # 8. Sentetik Kredi Skoru (Kurallı Hesaplama - Makine Öğrenmesi için zemin hazırlar)
    # Temel formül: Gelir (+), Geçmiş (+), Tecrübe (+), Borç Oranı (-)
    credit_scores = []
    for i in range(num_records):
        score = 500  # Başlangıç puanı
        
        # Gelir etkisi (Max +100 puan)
        income_score = min(100, (annual_incomes[i] / 150000) * 15)
        score += income_score
        
        # Tecrübe etkisi (Max +50 puan)
        exp_score = min(50, employment_years[i] * 4)
        score += exp_score
        
        # Kredi geçmişi etkisi (Max +75 puan)
        hist_score = min(75, credit_histories[i] * 5)
        score += hist_score
        
        # Ev sahipliği etkisi (Max +50 puan)
        if housing_statuses[i] == "OWN":
            score += 50
        elif housing_statuses[i] == "MORTGAGE":
            score += 25
            
        # Borç / Gelir oranı etkisi (Max -150 puan)
        dti = existing_debts[i] / max(1, annual_incomes[i])
        score -= min(150, dti * 300)
        
        # Rastgele gürültü (Max +-30 puan)
        score += np.random.randint(-30, 30)
        
        # Kredi Skorunu FICO benzeri 300-850 aralığına sıkıştır
        score = int(np.clip(score, 300, 850))
        credit_scores.append(score)
    
    # 9. Otomatik Karar (Kurallı Onay Durumu)
    # Skoru yüksek olan ve Borç Oranı düşük olanlar onaylanır
    approval_statuses = []
    for i in range(num_records):
        dti = existing_debts[i] / max(1, annual_incomes[i])
        # Onay şartı: Skor >= 600 ve DTI < 0.40
        # Hafif gri alan yaratmak için biraz rastgelelik ekleyelim
        if credit_scores[i] >= 610 and dti < 0.42:
            status = "APPROVED" if np.random.rand() > 0.05 else "REJECTED"
        elif credit_scores[i] >= 550 and dti < 0.35:
            status = "APPROVED" if np.random.rand() > 0.3 else "REJECTED"
        else:
            status = "REJECTED" if np.random.rand() > 0.05 else "APPROVED"
        approval_statuses.append(status)
        
    return {
        "ages": ages,
        "employment_years": employment_years,
        "annual_incomes": annual_incomes,
        "housing_statuses": housing_statuses,
        "credit_histories": credit_histories,
        "existing_debts": existing_debts,
        "loan_amounts": loan_amounts,
        "loan_purposes": loan_purposes,
        "term_months": term_months,
        "interest_rates": interest_rates,
        "credit_scores": credit_scores,
        "approval_statuses": approval_statuses
    }

def seed_database():
    # Veritabanını sıfırla ve tabloları oluştur
    init_db()
    
    data = generate_correlated_data(1000)
    db = SessionLocal()
    
    print("\nSeeding database with generated records...")
    try:
        customers = []
        applications = []
        
        for i in range(1000):
            first_name = fake.first_name()
            last_name = fake.last_name()
            # Benzersiz e-posta adresi
            email = f"{first_name.lower()}.{last_name.lower()}.{i}@example.com"
            # Türkçe karakter temizleme
            email = email.replace("ı", "i").replace("ş", "s").replace("ğ", "g").replace("ü", "u").replace("ö", "o").replace("ç", "c")
            
            customer = Customer(
                first_name=first_name,
                last_name=last_name,
                email=email,
                age=int(data["ages"][i]),
                annual_income=float(data["annual_incomes"][i]),
                employment_years=int(data["employment_years"][i]),
                housing_status=data["housing_statuses"][i],
                credit_history_length=int(data["credit_histories"][i]),
                existing_debts=float(data["existing_debts"][i])
            )
            customers.append(customer)
            
        db.add_all(customers)
        db.commit()  # Customer ID'lerin oluşması için commit ediyoruz
        
        for i in range(1000):
            # Oluşan customer objesinden ID'yi alıyoruz
            app = CreditApplication(
                customer_id=customers[i].id,
                loan_amount=float(data["loan_amounts"][i]),
                loan_purpose=data["loan_purposes"][i],
                interest_rate=float(data["interest_rates"][i]),
                term_months=int(data["term_months"][i]),
                credit_score=float(data["credit_scores"][i]),
                approval_status=data["approval_statuses"][i],
                risk_segment=None,  # K-Means eğitimi sonrası doldurulacak
                approval_probability=None  # Lojistik Regresyon eğitimi sonrası doldurulacak
            )
            applications.append(app)
            
        db.add_all(applications)
        db.commit()
        print(f"[SUCCESS] Successfully seeded 1000 customer and credit application records.")
        
    except Exception as e:
        print(f"[ERROR] Database seeding failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
