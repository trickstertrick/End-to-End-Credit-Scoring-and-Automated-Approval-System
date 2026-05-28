import os
import joblib
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score
from database import SessionLocal, Customer, CreditApplication

def train_and_save_models():
    print("Fetching data from database...")
    db = SessionLocal()
    try:
        # Müşteri ve Kredi Başvurusu verilerini join ederek çekelim
        query = db.query(Customer, CreditApplication).join(
            CreditApplication, Customer.id == CreditApplication.customer_id
        )
        
        data_list = []
        for cust, app in query.all():
            data_list.append({
                "app_id": app.id,
                "customer_id": cust.id,
                "age": cust.age,
                "annual_income": cust.annual_income,
                "employment_years": cust.employment_years,
                "housing_status": cust.housing_status,
                "credit_history_length": cust.credit_history_length,
                "existing_debts": cust.existing_debts,
                "loan_amount": app.loan_amount,
                "loan_purpose": app.loan_purpose,
                "interest_rate": app.interest_rate,
                "term_months": app.term_months,
                "credit_score": app.credit_score,
                "approval_status": app.approval_status
            })
            
        df = pd.DataFrame(data_list)
        if len(df) == 0:
            print("[ERROR] No data found in the database. Run data_pipeline.py first!")
            return
            
        print(f"[SUCCESS] Loaded {len(df)} records from database.")
        
        # ==========================================
        # 1. K-Means Kümeleme (Müşteri Risk Segmentasyonu)
        # ==========================================
        print("\nTraining K-Means (K=3) for Risk Segmentation...")
        # Segmentasyon için finansal göstergeleri seçiyoruz
        kmeans_features = ["annual_income", "existing_debts", "credit_score"]
        X_kmeans = df[kmeans_features].copy()
        
        kmeans_scaler = StandardScaler()
        X_kmeans_scaled = kmeans_scaler.fit_transform(X_kmeans)
        
        kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
        df["cluster"] = kmeans.fit_predict(X_kmeans_scaled)
        
        # Kümeleri iş mantığına göre etiketleyelim ("Low Risk", "Medium Risk", "High Risk")
        # Kredi Skoru ortalaması en yüksek olan küme -> Low Risk
        # Kredi Skoru ortalaması en düşük olan küme -> High Risk
        cluster_means = df.groupby("cluster")["credit_score"].mean().sort_values(ascending=False)
        
        cluster_mapping = {
            cluster_means.index[0]: "Low Risk",
            cluster_means.index[1]: "Medium Risk",
            cluster_means.index[2]: "High Risk"
        }
        
        df["risk_segment"] = df["cluster"].map(cluster_mapping)
        print("K-Means Cluster Profiles (Average Credit Score):")
        for cl, name in cluster_mapping.items():
            avg_score = cluster_means[cl]
            print(f"  - Cluster {cl} ({name}): Avg Credit Score = {avg_score:.1f}")
            
        # ==========================================
        # 2. Lojistik Regresyon (Kredi Onay Tahmini)
        # ==========================================
        print("\nTraining Logistic Regression for Credit Approval Prediction...")
        
        # Kategorik değişken (housing_status) için One-Hot Encoding
        df_encoded = pd.get_dummies(df, columns=["housing_status"], drop_first=False)
        
        # Gerekli kolonların mevcut olduğundan emin olalım (One-hot encoding sonrası)
        for status in ["housing_status_OWN", "housing_status_MORTGAGE", "housing_status_RENT"]:
            if status not in df_encoded.columns:
                df_encoded[status] = 0
                
        # Model Özellikleri
        model_features = [
            "age", "annual_income", "employment_years", "credit_history_length", 
            "existing_debts", "loan_amount", "term_months", "interest_rate", "credit_score",
            "housing_status_OWN", "housing_status_MORTGAGE", "housing_status_RENT"
        ]
        
        X_lr = df_encoded[model_features].astype(float)
        y_lr = df_encoded["approval_status"].apply(lambda x: 1 if x == "APPROVED" else 0)
        
        lr_scaler = StandardScaler()
        X_lr_scaled = lr_scaler.fit_transform(X_lr)
        
        logistic_model = LogisticRegression(random_state=42, max_iter=1000)
        logistic_model.fit(X_lr_scaled, y_lr)
        
        # Model Performansı
        y_pred = logistic_model.predict(X_lr_scaled)
        y_proba = logistic_model.predict_proba(X_lr_scaled)[:, 1]
        
        accuracy = accuracy_score(y_lr, y_pred)
        print(f"[SUCCESS] Logistic Regression Model Accuracy: {accuracy:.4f}")
        print("\nClassification Report:")
        print(classification_report(y_lr, y_pred, target_names=["REJECTED", "APPROVED"]))
        
        # ==========================================
        # 3. Veritabanını Güncelleme (Risk Segmenti ve Onay Olasılığı)
        # ==========================================
        print("\nUpdating database with risk segments and approval probabilities...")
        df["approval_probability"] = y_proba
        
        # Toplu güncelleme yerine veritabanı oturumu üzerinden güncelliyoruz
        update_count = 0
        for _, row in df.iterrows():
            app = db.query(CreditApplication).filter(CreditApplication.id == int(row["app_id"])).first()
            if app:
                app.risk_segment = row["risk_segment"]
                app.approval_probability = float(row["approval_probability"])
                update_count += 1
                
        db.commit()
        print(f"[SUCCESS] Updated {update_count} database application records with ML outputs.")
        
        # ==========================================
        # 4. Modelleri Kaydetme
        # ==========================================
        print("\nSaving model files to disk...")
        os.makedirs("models", exist_ok=True)
        
        joblib.dump(kmeans_scaler, "models/kmeans_scaler.pkl")
        joblib.dump(kmeans, "models/kmeans_model.pkl")
        joblib.dump(cluster_mapping, "models/cluster_mapping.pkl")
        
        joblib.dump(lr_scaler, "models/lr_scaler.pkl")
        joblib.dump(logistic_model, "models/logistic_model.pkl")
        # Feature kolonlarının sırasını kaydetmek prediction aşamasında çok önemlidir
        joblib.dump(model_features, "models/model_features.pkl")
        
        print("[SUCCESS] All model files successfully saved in 'models/' directory:")
        print("  - models/kmeans_scaler.pkl")
        print("  - models/kmeans_model.pkl")
        print("  - models/cluster_mapping.pkl")
        print("  - models/lr_scaler.pkl")
        print("  - models/logistic_model.pkl")
        print("  - models/model_features.pkl")
        
    except Exception as e:
        print(f"[ERROR] Model training flow failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    train_and_save_models()
