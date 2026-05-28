import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# ==========================================
# Premium Tasarım ve Stil Tanımlamaları (CSS)
# ==========================================
st.set_page_config(
    page_title="FinShield | Kredi Onay & ML Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Google Fonts (Outfit) ve Özel CSS Entegrasyonu
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
    
    * {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Ana Başlık ve Banner */
    .banner-container {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #311042 100%);
        padding: 2.5rem;
        border-radius: 16px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        margin-bottom: 2rem;
        border: 1px solid rgba(255, 255, 255, 0.08);
        position: relative;
        overflow: hidden;
    }
    .banner-container::after {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(99,102,241,0.05) 0%, transparent 60%);
        pointer-events: none;
    }
    .banner-title {
        color: #f8fafc;
        font-size: 2.2rem;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .banner-subtitle {
        color: #94a3b8;
        font-size: 1rem;
        margin-top: 0.5rem;
        font-weight: 300;
    }
    
    /* Kart Yapıları (Glassmorphism) */
    .metric-card {
        background: rgba(30, 41, 59, 0.45);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        margin-bottom: 1rem;
    }
    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 30px rgba(99, 102, 241, 0.15);
        border-color: rgba(99, 102, 241, 0.2);
    }
    .metric-label {
        color: #94a3b8;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.5rem;
    }
    .metric-value {
        color: #f8fafc;
        font-size: 1.8rem;
        font-weight: 700;
    }
    .metric-delta {
        font-size: 0.8rem;
        margin-top: 0.25rem;
        font-weight: 400;
    }
    .text-green { color: #10b981; }
    .text-red { color: #ef4444; }
    .text-blue { color: #3b82f6; }
    
    /* Başvuru Sonuç Kartı */
    .result-card-approved {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(16, 185, 129, 0.02) 100%);
        border: 2px solid #10b981;
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 0 8px 32px rgba(16, 185, 129, 0.15);
        margin-top: 1.5rem;
        animation: pulse 2s infinite alternate;
    }
    .result-card-rejected {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(239, 68, 68, 0.02) 100%);
        border: 2px solid #ef4444;
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 0 8px 32px rgba(239, 68, 68, 0.15);
        margin-top: 1.5rem;
    }
    
    /* Durum Rozetleri */
    .badge {
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
        text-align: center;
    }
    .badge-approved {
        background-color: rgba(16, 185, 129, 0.15);
        color: #10b981;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    .badge-rejected {
        background-color: rgba(239, 68, 68, 0.15);
        color: #ef4444;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }
    
    /* Form input alanlarını özelleştirme */
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>div {
        background-color: rgba(30, 41, 59, 0.6) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: #f8fafc !important;
        border-radius: 8px !important;
    }
    .stButton>button {
        background: linear-gradient(90deg, #6366f1 0%, #4f46e5 100%) !important;
        color: white !important;
        font-weight: 600 !important;
        padding: 0.6rem 2rem !important;
        border-radius: 8px !important;
        border: none !important;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3) !important;
        transition: all 0.3s ease !important;
        width: 100%;
    }
    .stButton>button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(99, 102, 241, 0.5) !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

API_URL = "http://127.0.0.1:8000"

# ==========================================
# API Haberleşme Fonksiyonları
# ==========================================
@st.cache_data(ttl=10)
def fetch_metrics():
    try:
        response = requests.get(f"{API_URL}/metrics")
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return None

@st.cache_data(ttl=10)
def fetch_applications():
    try:
        response = requests.get(f"{API_URL}/applications?limit=100")
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return []

def submit_prediction(payload):
    try:
        response = requests.post(f"{API_URL}/predict", json=payload)
        return response.json(), response.status_code
    except Exception as e:
        return {"detail": f"API sunucusuna bağlanılamadı: {e}"}, 500

# ==========================================
# Sidebar Arayüzü ve Menü Seçimleri
# ==========================================
with st.sidebar:
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 2rem;">
            <h1 style="color: #6366f1; font-weight: 800; font-size: 1.8rem; margin-bottom: 0;">🛡️ FinShield</h1>
            <p style="color: #64748b; font-size: 0.85rem; margin-top: 0.2rem;">Automated Credit Decisions</p>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    menu_selection = st.radio(
        "Menü",
        ["Dashboard", "Yeni Başvuru Sorgula"],
        index=0,
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.markdown("### Sistem Durumu")
    
    # API Sağlık Kontrolü
    api_online = False
    try:
        health_resp = requests.get(API_URL)
        if health_resp.status_code == 200:
            api_online = True
    except Exception:
        pass
        
    if api_online:
        st.markdown('<p class="badge badge-approved" style="width:100%;">🟢 API SUNUCUSU AKTİF</p>', unsafe_allow_html=True)
    else:
        st.markdown('<p class="badge badge-rejected" style="width:100%;">🔴 API SUNUCUSU KAPALI</p>', unsafe_allow_html=True)
        
    st.markdown(
        """
        <div style="font-size:0.8rem; color:#64748b; margin-top: 1rem;">
            <p><b>Model Versiyonu:</b> v1.0.0</p>
            <p><b>Algoritmalar:</b> K-Means, Logistic Regression</p>
            <p><b>Veri Tabanı:</b> PostgreSQL / SQLite</p>
        </div>
        """,
        unsafe_allow_html=True
    )

# ==========================================
# Ana Sayfa Banner Gösterimi
# ==========================================
st.markdown(
    """
    <div class="banner-container">
        <h1 class="banner-title">Uçtan Uca Kredi Skoru Hesaplama ve Otomatik Onay Sistemi</h1>
        <p class="banner-subtitle">Makine öğrenmesi ile anlık risk segmentasyonu (K-Means) ve otomatik onay mekanizması (Lojistik Regresyon).</p>
    </div>
    """,
    unsafe_allow_html=True
)

# ==========================================
# 1. Menü: Dashboard Ekranı
# ==========================================
if menu_selection == "Dashboard":
    metrics = fetch_metrics()
    applications = fetch_applications()
    
    if not metrics:
        st.info("📊 Gösterge paneli verilerini yüklemek için API sunucusunun çalışır durumda olduğundan emin olun.")
        st.markdown("API'yi yerel ortamınızda başlatmak için terminalde şu komutu çalıştırabilirsiniz:")
        st.code("uvicorn main:app --reload", language="bash")
    else:
        # Metrik Kartları
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">Toplam Başvuru</div>
                    <div class="metric-value">{metrics["total_applications"]}</div>
                    <div class="metric-delta text-blue">Aktif Müşteri Portföyü</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
        with col2:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">Ortalama Kredi Skoru</div>
                    <div class="metric-value">{metrics["average_credit_score"]}</div>
                    <div class="metric-delta text-green">FICO Benzeri Ortalama</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
        with col3:
            approval_rate_pct = metrics["approval_rate"] * 100
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">Sistem Onay Oranı</div>
                    <div class="metric-value">%{approval_rate_pct:.1f}</div>
                    <div class="metric-delta text-green">Otomatik Onaylanan</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
        with col4:
            high_risk_count = metrics["risk_segment_distribution"].get("High Risk", 0)
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">Yüksek Riskli Müşteri</div>
                    <div class="metric-value">{high_risk_count}</div>
                    <div class="metric-delta text-red">K-Means Segmentasyonu</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
        # Grafikler Bölümü
        st.markdown("### Risk Dağılımı ve Analitikler")
        gcol1, gcol2 = st.columns([1, 1])
        
        with gcol1:
            # Donut Chart - Risk Segmenti Dağılımı
            seg_dist = metrics["risk_segment_distribution"]
            if seg_dist:
                fig_donut = px.pie(
                    names=list(seg_dist.keys()),
                    values=list(seg_dist.values()),
                    hole=0.6,
                    color=list(seg_dist.keys()),
                    color_discrete_map={
                        "Low Risk": "#10b981",
                        "Medium Risk": "#f59e0b",
                        "High Risk": "#ef4444"
                    },
                    title="K-Means Risk Segmentasyonu Dağılımı"
                )
                fig_donut.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#94a3b8",
                    legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
                )
                st.plotly_chart(fig_donut, use_container_width=True)
            else:
                st.info("Kümeleri görselleştirmek için veri bulunamadı.")
                
        with gcol2:
            # Kredi Skoruna Göre Mevcut Borç / Yıllık Gelir Oranı Dağılımı
            if applications:
                df_apps = pd.DataFrame(applications)
                df_apps["dti"] = df_apps["existing_debts"] / df_apps["annual_income"]
                
                fig_scatter = px.scatter(
                    df_apps,
                    x="credit_score",
                    y="dti",
                    color="risk_segment",
                    color_discrete_map={
                        "Low Risk": "#10b981",
                        "Medium Risk": "#f59e0b",
                        "High Risk": "#ef4444"
                    },
                    labels={
                        "credit_score": "Kredi Skoru (FICO)",
                        "dti": "Borç / Gelir Oranı (DTI)",
                        "risk_segment": "Risk Segmenti"
                    },
                    title="Müşteri Finansal Profili: Kredi Skoru vs. Borç/Gelir Oranı"
                )
                fig_scatter.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#94a3b8",
                    xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                    yaxis=dict(gridcolor="rgba(255,255,255,0.05)")
                )
                st.plotly_chart(fig_scatter, use_container_width=True)
            else:
                st.info("Grafik için yeterli başvuru verisi bulunmamaktadır.")
                
        # Başvuru Amaçlarına Göre Onay Oranları
        if applications:
            df_apps = pd.DataFrame(applications)
            purpose_stats = df_apps.groupby(["loan_purpose", "approval_status"]).size().unstack(fill_value=0)
            if "APPROVED" not in purpose_stats:
                purpose_stats["APPROVED"] = 0
            if "REJECTED" not in purpose_stats:
                purpose_stats["REJECTED"] = 0
                
            fig_bar = go.Figure(data=[
                go.Bar(name='ONAYLANDI', x=purpose_stats.index, y=purpose_stats['APPROVED'], marker_color='#10b981'),
                go.Bar(name='REDDEDİLDİ', x=purpose_stats.index, y=purpose_stats['REJECTED'], marker_color='#ef4444')
            ])
            fig_bar.update_layout(
                barmode='group',
                title="Kredi Başvuru Amaçlarına Göre Karar Dağılımları",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#94a3b8",
                xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                yaxis=dict(gridcolor="rgba(255,255,255,0.05)")
            )
            st.plotly_chart(fig_bar, use_container_width=True)
            
        # Son Başvurular Listesi
        st.markdown("### Son Yapılan Kredi Başvuruları")
        if applications:
            df_table = pd.DataFrame(applications)
            # Zaman formatlama
            df_table["applied_at"] = pd.to_datetime(df_table["applied_at"]).dt.strftime('%d-%m-%Y %H:%M')
            
            # HTML Tablo ile Şık Tasarım
            html_table = """
            <table style="width:100%; border-collapse: collapse; text-align: left; background: rgba(30,41,59,0.3); border-radius: 8px; overflow: hidden;">
                <thead>
                    <tr style="background: rgba(99, 102, 241, 0.1); border-bottom: 2px solid rgba(255,255,255,0.05);">
                        <th style="padding: 12px; color: #94a3b8; font-weight:600;">Müşteri İsim</th>
                        <th style="padding: 12px; color: #94a3b8; font-weight:600;">Gelir (TL)</th>
                        <th style="padding: 12px; color: #94a3b8; font-weight:600;">Talep Edilen (TL)</th>
                        <th style="padding: 12px; color: #94a3b8; font-weight:600;">Kredi Skoru</th>
                        <th style="padding: 12px; color: #94a3b8; font-weight:600;">Risk Segmenti</th>
                        <th style="padding: 12px; color: #94a3b8; font-weight:600;">Karar</th>
                        <th style="padding: 12px; color: #94a3b8; font-weight:600;">Olasılık</th>
                        <th style="padding: 12px; color: #94a3b8; font-weight:600;">Başvuru Tarihi</th>
                    </tr>
                </thead>
                <tbody>
            """
            for _, r in df_table.head(15).iterrows():
                badge_class = "badge-approved" if r['approval_status'] == "APPROVED" else "badge-rejected"
                status_text = "ONAYLANDI" if r['approval_status'] == "APPROVED" else "REDDEDİLDİ"
                
                segment_colors = {"Low Risk": "#10b981", "Medium Risk": "#f59e0b", "High Risk": "#ef4444"}
                seg_color = segment_colors.get(r['risk_segment'], "#94a3b8")
                
                html_table += f"""
                    <tr style="border-bottom: 1px solid rgba(255,255,255,0.05); hover: background-color: rgba(255,255,255,0.02);">
                        <td style="padding: 12px; color: #f8fafc; font-weight:600;">{r['customer_name']}</td>
                        <td style="padding: 12px; color: #cbd5e1;">{r['annual_income']:,.0f} ₺</td>
                        <td style="padding: 12px; color: #cbd5e1;">{r['loan_amount']:,.0f} ₺</td>
                        <td style="padding: 12px; color: #cbd5e1; font-weight:700;">{r['credit_score']:.0f}</td>
                        <td style="padding: 12px; color: {seg_color}; font-weight:600;">{r['risk_segment']}</td>
                        <td style="padding: 12px;"><span class="badge {badge_class}">{status_text}</span></td>
                        <td style="padding: 12px; color: #cbd5e1; font-weight:600;">%{r['approval_probability']*100:.1f}</td>
                        <td style="padding: 12px; color: #64748b;">{r['applied_at']}</td>
                    </tr>
                """
            html_table += "</tbody></table>"
            st.markdown(html_table, unsafe_allow_html=True)
        else:
            st.info("Kayıtlı başvuru bulunmuyor.")

# ==========================================
# 2. Menü: Kredi Sorgulama Formu
# ==========================================
elif menu_selection == "Yeni Başvuru Sorgula":
    st.markdown("### Yeni Müşteri Kredi Risk ve Onay Sorgulama")
    st.write("Aşağıdaki formu doldurarak müşterinin finansal ve demografik bilgileri doğrultusunda ML kararını anında alabilirsiniz.")
    
    with st.form("credit_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 👤 Demografik & Kişisel Bilgiler")
            first_name = st.text_input("Adı", "Ahmet")
            last_name = st.text_input("Soyadı", "Demir")
            email = st.text_input("E-posta Adresi", "ahmet.demir@example.com")
            age = st.number_input("Yaş", min_value=18, max_value=100, value=35, step=1)
            housing_status = st.selectbox("Ev Sahipliği Durumu", ["MORTGAGE", "OWN", "RENT", "OTHER"], index=0)
            
        with col2:
            st.markdown("#### 💼 Finansal Durum & Talep")
            annual_income = st.number_input("Yıllık Gelir (₺)", min_value=0.0, value=550000.0, step=10000.0)
            employment_years = st.number_input("İş Tecrübesi (Yıl)", min_value=0, max_value=50, value=7, step=1)
            credit_history_length = st.number_input("Kredi Geçmişi Süresi (Yıl)", min_value=0, max_value=50, value=8, step=1)
            existing_debts = st.number_input("Mevcut Borç Bakiyesi (₺)", min_value=0.0, value=45000.0, step=5000.0)
            
            st.markdown("---")
            st.markdown("#### 🏦 Kredi Talebi")
            loan_amount = st.number_input("Talep Edilen Kredi Tutarı (₺)", min_value=1000.0, value=120000.0, step=5000.0)
            loan_purpose = st.selectbox("Kredi Kullanım Amacı", ["PERSONAL", "EDUCATION", "HOME_IMPROVEMENT", "DEBT_CONSOLIDATION", "CAR"], index=0)
            term_months = st.selectbox("Vade (Ay)", [12, 24, 36, 48, 60], index=2)
            interest_rate = st.number_input("Faiz Oranı (%)", min_value=0.1, value=2.45, step=0.05)
            
        submit_btn = st.form_submit_button("ONAY SÜRECİNİ BAŞLAT")
        
    if submit_btn:
        # Pydantic şemasına uygun payload hazırlama
        payload = {
            "customer": {
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "age": int(age),
                "annual_income": float(annual_income),
                "employment_years": int(employment_years),
                "housing_status": housing_status,
                "credit_history_length": int(credit_history_length),
                "existing_debts": float(existing_debts)
            },
            "application": {
                "loan_amount": float(loan_amount),
                "loan_purpose": loan_purpose,
                "interest_rate": float(interest_rate),
                "term_months": int(term_months)
            }
        }
        
        with st.spinner("⚡ FinShield Yapay Zekası Karar Sürecini Çalıştırıyor..."):
            result, status_code = submit_prediction(payload)
            
        if status_code == 200:
            st.toast("🎯 Kredi değerlendirmesi başarıyla tamamlandı!", icon="✅")
            
            # Sonuç Arayüzü Bölümü
            r_col1, r_col2 = st.columns([1, 1.2])
            
            with r_col1:
                st.markdown("#### 🎯 Kredi Skoru (FICO)")
                # Gauge Chart ile Kredi Skoru Görselleştirme
                score = result["credit_score"]
                
                fig_gauge = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = score,
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    title = {'text': "Kredi Değerlilik Puanı", 'font': {'size': 20, 'color': "#94a3b8"}},
                    gauge = {
                        'axis': {'range': [300, 850], 'tickwidth': 1, 'tickcolor': "#cbd5e1"},
                        'bar': {'color': "#6366f1"},
                        'bgcolor': "rgba(30, 41, 59, 0.4)",
                        'borderwidth': 2,
                        'bordercolor': "rgba(255,255,255,0.05)",
                        'steps': [
                            {'range': [300, 580], 'color': '#ef4444'},     # Kötü / Çok Riskli
                            {'range': [580, 680], 'color': '#f59e0b'},     # Orta / Makul Risk
                            {'range': [680, 850], 'color': '#10b981'}      # İyi / Düşük Risk
                        ],
                        'threshold': {
                            'line': {'color': "white", 'width': 4},
                            'thickness': 0.75,
                            'value': score
                        }
                    }
                ))
                fig_gauge.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    font={'color': "#f8fafc", 'family': "Outfit"},
                    margin=dict(l=20, r=20, t=50, b=20)
                )
                st.plotly_chart(fig_gauge, use_container_width=True)
                
            with r_col2:
                st.markdown("#### 🛡️ FinShield Yapay Zeka Kararı")
                
                is_approved = result["approval_status"] == "APPROVED"
                prob = result["approval_probability"]
                
                if is_approved:
                    st.markdown(
                        f"""
                        <div class="result-card-approved">
                            <h2 style="color: #10b981; margin: 0; font-weight: 800; font-size: 1.8rem;">👍 KREDİ ONAYLANDI</h2>
                            <p style="color: #cbd5e1; margin-top: 0.5rem; font-size: 1.05rem;">
                                Yapılan makine öğrenmesi değerlendirmesinde kredi başvurunuz <b>OTOMATİK ONAY</b> kriterlerini karşılamıştır.
                            </p>
                            <hr style="border-color: rgba(16, 185, 129, 0.2); margin: 1rem 0;">
                            <p style="color: #94a3b8; font-size: 0.9rem; margin-bottom: 0;">
                                <b>Risk Segmenti:</b> <span style="color: #10b981; font-weight:700;">{result["risk_segment"]}</span><br>
                                <b>Onay İhtimal Skoru:</b> <span style="color: #10b981; font-weight:700;">%{prob*100:.2f}</span><br>
                                <b>Sistem Kayıt ID:</b> #{result["application_id"]}
                            </p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f"""
                        <div class="result-card-rejected">
                            <h2 style="color: #ef4444; margin: 0; font-weight: 800; font-size: 1.8rem;">👎 KREDİ REDDEDİLDİ</h2>
                            <p style="color: #cbd5e1; margin-top: 0.5rem; font-size: 1.05rem;">
                                Yapılan değerlendirmede başvuru sahibinin borç/gelir rasyosu veya kredi skoru risk limitlerinin dışında kaldığı için <b>OTOMATİK RED</b> kararı üretilmiştir.
                            </p>
                            <hr style="border-color: rgba(239, 68, 68, 0.2); margin: 1rem 0;">
                            <p style="color: #94a3b8; font-size: 0.9rem; margin-bottom: 0;">
                                <b>Risk Segmenti:</b> <span style="color: #ef4444; font-weight:700;">{result["risk_segment"]}</span><br>
                                <b>Onay İhtimal Skoru:</b> <span style="color: #ef4444; font-weight:700;">%{prob*100:.2f}</span><br>
                                <b>Sistem Kayıt ID:</b> #{result["application_id"]}
                            </p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
        else:
            error_msg = result.get("detail", "Bilinmeyen bir hata oluştu.")
            st.error(f"❌ Kredi değerlendirmesi başarısız oldu: {error_msg}")
