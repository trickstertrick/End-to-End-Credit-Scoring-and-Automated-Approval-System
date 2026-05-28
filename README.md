# End-to-End-Credit-Scoring-and-Automated-Approval-System
EN//
An end-to-end credit scoring system built with PostgreSQL, FastAPI, and Streamlit. It stores financial data, performs risk segmentation using K-Means, and predicts loan approval probabilities via Logistic Regression. Features a real-time, interactive dashboard with dynamic data visualizations.
TR//
# Uçtan Uca Kredi Skoru Hesaplama ve Otomatik Onay Sistemi

Modern finansal risk yönetimi için tasarlanmış, uçtan uca (End-to-End) çalışan bir kredi skorlama ve kredi onay simülasyon platformudur. Bu proje; veri mühendisliği (PostgreSQL), istatistiksel modelleme/makine öğrenmesi (K-Means & Lojistik Regresyon) ve canlıya alma/dağıtım (FastAPI & Streamlit) süreçlerini bir araya getirerek istatistik teorisi ile yazılım mühendisliği arasında güçlü bir köprü kurar.

---

## 🚀 Projeye Genel Bakış ve Mimari

Çoğu makine öğrenmesi projesi Jupyter Notebook'ların içinde izole kalır. Bu proje ise kullanıcıdan finansal verileri alan, bunları iki aşamalı bir makine öğrenmesi mimarisiyle işleyen, tüm operasyonları ilişkisel bir veri tabanına kaydeden ve modeli güvenli bir API ile etkileşimli bir arayüze açan üretim standartlarında (production-ready) bir boru hattıdır (pipeline).
EN//
# End-to-End Credit Scoring & Automated Approval System

An end-to-end credit scoring and loan approval simulation platform built for modern financial risk management. This project bridges the gap between statistical theory and software engineering by combining data engineering (PostgreSQL), statistical modeling/machine learning (K-Means & Logistic Regression), and deployment (FastAPI & Streamlit).

---

## 🚀 Project Overview & Architecture

Most machine learning projects are isolated inside Jupyter Notebooks. This project serves as a production-ready pipeline that ingests user financial data, processes it via a dual-stage machine learning architecture, logs operations into a relational database, and exposes the model through a secure API and interactive frontend dashboard.
---

## 🛠️ Tech Stack

* **Backend Engine:** Python, FastAPI
* **Frontend Dashboard:** Streamlit, Plotly (Dynamic Gauge & Risk Charts)
* **Database Management:** PostgreSQL (psycopg2 / SQLAlchemy)
* **Statistical Modeling & ML:** Scikit-learn, Pandas, NumPy
* **Data Synthesis:** Faker

---

## 🔬 Statistical & Machine Learning Architecture

The core decision engine operates in a robust **two-stage pipeline** to ensure deep statistical validity over raw heuristics:

### Stage A: K-Means Clustering (Risk Segmentation)
* **Objective:** Group existing customers based on financial behavior and automatically assign new applicants to an empirical "Risk Cluster".
* **Features Used:** `annual_income`, `total_debt`, `credit_count`, `past_due_days`.
* **Output:** 3 Distinct Behavioral Segments:
  * `Cluster 0`: Low Risk (Green)
  * `Cluster 1`: Medium Risk (Yellow)
  * `Cluster 2`: High Risk (Red)
* **Statistical Rigor:** Features are standardized using `StandardScaler` to handle magnitude variances (e.g., income in thousands vs. credit count in single digits). The optimal cluster count ($K=3$) is selected using the **Elbow Method**.

### Stage B: Logistic Regression (Probability of Approval)
* **Objective:** Calculate the exact mathematical probability of a loan application being safely approved.
* **Feature Engineering:** The predicted `risk_cluster` from Stage A is leveraged as a highly predictive interaction feature for the classifier.
* **Mathematical Formulation:**
  $$P(\text{Approval}) = \frac{1}{1 + e^{-(\beta_0 + \beta_1 \cdot \text{Income} + \beta_2 \cdot \text{Debt} + \beta_3 \cdot \text{RiskCluster})}}$$
* **Decision Boundary:** 
  * If $P(\text{Approval}) \ge 0.50 \rightarrow$ **APPROVED**
  * If $P(\text{Approval}) < 0.50 \rightarrow$ **REJECTED**

---

## 🗄️ Database Design (PostgreSQL Schema)

The database architecture guarantees data persistence for both core customer financial profiles and the audit logs of model evaluations.

### 1. `customers` Table
Stores primary demographic and structural financial metrics.

| Column Name | Data Type | Description |
| :--- | :--- | :--- |
| `id` | SERIAL (PK) | Unique Customer Identifier |
| `first_name` | VARCHAR(50) | Customer's First Name |
| `last_name` | VARCHAR(50) | Customer's Last Name |
| `annual_income` | NUMERIC | Total Annual Income |
| `total_debt` | NUMERIC | Aggregate Active Debt |
| `past_due_days` | INT | Max Days Past Due on Historical Payments |
| `credit_count` | INT | Number of Active Lines of Credit / Cards |

### 2. `credit_applications` Table
Logs inference data, structural model outputs, and metadata for audit trails.

| Column Name | Data Type | Description |
| :--- | :--- | :--- |
| `application_id` | SERIAL (PK) | Unique Evaluation ID |
| `customer_id` | INT (FK) | References `customers.id` |
| `risk_cluster` | INT | Assigned Cluster Label via K-Means (0, 1, or 2) |
| `approval_probability` | NUMERIC | Precise Probability Output from Logistic Regression (0.0 - 1.0) |
| `status` | VARCHAR(10) | Final System Decision (`APPROVED` / `REJECTED`) |
| `created_at` | TIMESTAMP | Timestamp of Application Submission |

---

## 🗺️ Implementation Roadmap

* [ ] **Phase 1: Synthetic Data Pipeline & ETL** 
  * Generate a highly correlated, statistically realistic dataset of 1,000 customers using Python `Faker` and `NumPy`.
  * Establish connection to PostgreSQL and build automated data injection scripts.
* [ ] **Phase 2: Model Training & Validation**
  * Fetch relational database records into an analytical environment (Jupyter Notebook).
  * Train K-Means and Logistic Regression pipelines; validate via Confusion Matrices, ROC-AUC curves, and classification metrics.
  * Serialize production models to binary `.pkl` files using `joblib`.
* [ ] **Phase 3: Production API Layer (FastAPI)**
  * Design a secure `/predict` POST endpoint accepting JSON structured payloads.
  * Implement backend inference workflows and save asynchronous transaction logs back to PostgreSQL.
* [ ] **Phase 4: Presentation & UI Layer (Streamlit)**
  * Construct clean interactive input controllers (sliders, conditional fields).
  * Request calculations from the backend API and render dynamic Plotly Gauge gauges tracking real-time risk classification boundaries.

---

5. ---

## 🛠️ Teknolojik Yığın (Tech Stack)

* **Backend Motoru:** Python, FastAPI
* **Arayüz / Dashboard:** Streamlit, Plotly (Dinamik Hız ve Risk Grafikleri)
* **Veri Tabanı Yönetimi:** PostgreSQL (psycopg2 / SQLAlchemy)
* **İstatistiksel Modelleme & ML:** Scikit-learn, Pandas, NumPy
* **Veri Sentezi:** Faker

---

## 🔬 İstatistiki ve Makine Öğrenmesi Mimarisi

Çekirdek karar motoru, ham sezgisel kurallar yerine derin istatistiksel geçerliliği sağlamak amacıyla **iki aşamalı bir boru hattı** şeklinde çalışır:

### Aşama A: K-Means Kümeleme (Risk Segmentasyonu)
* **Amaç:** Mevcut müşterileri finansal davranışlarına göre gruplandırmak ve yeni başvuranları otomatik olarak ampirik bir "Risk Kümesine" atamak.
* **Kullanılan Değişkenler (Features):** `annual_income` (Yıllık Gelir), `total_debt` (Toplam Borç), `credit_count` (Aktif Kredi/Kart Sayısı), `past_due_days` (Geciken Ödeme Gün Sayısı).
* **Çıktı:** 3 Farklı Davranışsal Segment:
  * `Küme 0`: Düşük Risk (Yeşil)
  * `Küme 1`: Orta Risk (Sarı)
  * `Küme 2`: Yüksek Risk (Kırmızı)
* **İstatistiki Detay:** Gelir (binler mertebesinde) ve kredi kartı sayısı (tek haneli) gibi değişkenler arasındaki boyut farklarını yönetmek için veriler `StandardScaler` ile standartlaştırılmıştır. Optimum küme sayısı ($K=3$), **Dirsek (Elbow) Yöntemi** kullanılarak seçilmiştir.

### Aşama B: Lojistik Regresyon (Onay / Red Olasılığı)
* **Amaç:** Bir kredi başvurusunun güvenle onaylanıp onaylanmayacağına dair kesin matematiksel olasılığı hesaplamak.
* **Özellik Mühendisliği (Feature Engineering):** Aşama A'dan elde edilen `risk_cluster` tahmini, sınıflandırıcı için oldukça güçlü bir girdi değişkeni olarak modele dahil edilir.
* **Matematiksel Formülasyon:**
  $$P(\text{Onay}) = \frac{1}{1 + e^{-(\beta_0 + \beta_1 \cdot \text{Gelir} + \beta_2 \cdot \text{Borç} + \beta_3 \cdot \text{RiskKümesi})}}$$
* **Karar Sınırı (Decision Boundary):** 
  * Eğer $P(\text{Onay}) \ge 0.50 \rightarrow$ **ONAYLANDI**
  * Eğer $P(\text{Onay}) < 0.50 \rightarrow$ **REDDEDİLDİ**

---

## 🗄️ Veri Tabanı Tasarımı (PostgreSQL Şeması)

Veri tabanı mimarisi, hem temel müşteri finansal profillerinin kalıcılığını hem de model değerlendirmelerinin denetim günlüklerini (logs) garanti altına alır.

### 1. `customers` Tablosu
Müşterilerin birincil demografik ve yapısal finansal metriklerini saklar.

| Kolon Adı | Veri Tipi | Açıklama |
| :--- | :--- | :--- |
| `id` | SERIAL (PK) | Benzersiz Müşteri ID |
| `first_name` | VARCHAR(50) | Müşterinin Adı |
| `last_name` | VARCHAR(50) | Müşterinin Soyadı |
| `annual_income` | NUMERIC | Toplam Yıllık Gelir |
| `total_debt` | NUMERIC | Toplam Aktif Borç miktarı |
| `past_due_days` | INT | Geçmiş Ödemelerdeki Maksimum Gecikme Gün Sayısı |
| `credit_count` | INT | Aktif Kredi / Kredi Kartı Sayısı |

### 2. `credit_applications` Tablosu
Model çıkarım verilerini, çıktılarını ve denetim takibi için gerekli meta verileri kaydeder.

| Kolon Adı | Veri Tipi | Açıklama |
| :--- | :--- | :--- |
| `application_id` | SERIAL (PK) | Benzersiz Başvuru/Değerlendirme ID |
| `customer_id` | INT (FK) | `customers.id` tablosuna referans |
| `risk_cluster` | INT | K-Means ile Atanan Küme Etiketi (0, 1 veya 2) |
| `approval_probability` | NUMERIC | Lojistik Regresyon Kesin Olasılık Çıktısı (0.0 - 1.0) |
| `status` | VARCHAR(10) | Nihai Sistem Kararı (`ONAY` / `RED`) |
| `created_at` | TIMESTAMP | Başvurunun Yapıldığı Tarih ve Saat |

---

## 🗺️ Uygulama Adımları ve Yol Haritası

* [ ] **Aşama 1: Sentetik Veri Boru Hattı ve ETL** 
  * Python `Faker` ve `NumPy` kullanarak istatistiksel olarak gerçekçi, birbiriyle korelasyonlu 1.000 kişilik yapay veri seti üretmek.
  * PostgreSQL bağlantısını kurmak ve otomatik veri yükleme (data injection) betiklerini yazmak.
* [ ] **Aşama 2: Model Eğitimi ve Doğrulama**
  * İlişkisel veri tabanındaki verileri analitik ortama (Jupyter Notebook) çekmek.
  * K-Means ve Lojistik Regresyon modellerini eğitmek; Karmaşıklık Matrisi (Confusion Matrix) ve ROC-AUC eğrileri ile modelleri doğrulamak.
  * Canlı sistemde kullanmak üzere modelleri `joblib` ile `.pkl` formatında kaydetmek.
* [ ] **Aşama 3: Üretim API Katmanı (FastAPI)**
  * JSON formatında veri kabul eden güvenli bir `/predict` POST uç noktası (endpoint) tasarlamak.
  * Arka planda model çıkarım süreçlerini çalıştırmak ve işlem günlüklerini asenkron olarak PostgreSQL'e kaydetmek.
* [ ] **Aşama 4: Sunum ve Kullanıcı Arayüzü Katmanı (Streamlit)**
  * Slider ve koşullu alanlardan oluşan temiz ve işlevsel veri giriş kontrolleri inşa etmek.
  * Backend API'sine istek atarak dönen sonuçları gerçek zamanlı risk sınırlarını izleyen dinamik Plotly grafiklerinde göstermek.

---

