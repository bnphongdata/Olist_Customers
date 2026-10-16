"""
================================================================================
DỰ ÁN PHÂN TÍCH DỮ LIỆU KHÁCH HÀNG OLIST (BRAZIL E-COMMERCE)
Kịch bản 01: Làm sạch (Data Cleaning), Chuẩn hóa & Làm giàu dữ liệu (Data Enrichment)
Vai trò: Chuyên viên Phân tích Dữ liệu (Lead Data Analyst)
Ngôn ngữ: Python 3.14 (Pandas, SQLite3)
================================================================================
"""

import os
import sqlite3
import pandas as pd

# Đường dẫn thư mục
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW_DATA_PATH = os.path.join(BASE_DIR, "data", "raw", "olist_customers_dataset.csv")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
SQLITE_DB_PATH = os.path.join(BASE_DIR, "data", "olist_analytics.db")

# Bảng tra cứu 27 Bang của Brazil, Tên đầy đủ và Phân vùng kinh tế (Macro-Regions)
# Nguồn chuẩn: Viện Địa lý và Thống kê Brazil (IBGE)
BRAZIL_STATE_MAPPING = {
    # Vùng Đông Nam (Sudeste) - Trung tâm kinh tế tài chính
    "SP": {"name": "São Paulo", "region": "Sudeste", "region_vn": "Đông Nam"},
    "RJ": {"name": "Rio de Janeiro", "region": "Sudeste", "region_vn": "Đông Nam"},
    "MG": {"name": "Minas Gerais", "region": "Sudeste", "region_vn": "Đông Nam"},
    "ES": {"name": "Espírito Santo", "region": "Sudeste", "region_vn": "Đông Nam"},
    
    # Vùng Nam (Sul) - Khu vực phát triển cao, công nông nghiệp hiện đại
    "PR": {"name": "Paraná", "region": "Sul", "region_vn": "Nam"},
    "RS": {"name": "Rio Grande do Sul", "region": "Sul", "region_vn": "Nam"},
    "SC": {"name": "Santa Catarina", "region": "Sul", "region_vn": "Nam"},
    
    # Vùng Đông Bắc (Nordeste) - Thị trường tiềm năng, dân số đông
    "BA": {"name": "Bahia", "region": "Nordeste", "region_vn": "Đông Bắc"},
    "PE": {"name": "Pernambuco", "region": "Nordeste", "region_vn": "Đông Bắc"},
    "CE": {"name": "Ceará", "region": "Nordeste", "region_vn": "Đông Bắc"},
    "MA": {"name": "Maranhão", "region": "Nordeste", "region_vn": "Đông Bắc"},
    "PB": {"name": "Paraíba", "region": "Nordeste", "region_vn": "Đông Bắc"},
    "RN": {"name": "Rio Grande do Norte", "region": "Nordeste", "region_vn": "Đông Bắc"},
    "AL": {"name": "Alagoas", "region": "Nordeste", "region_vn": "Đông Bắc"},
    "PI": {"name": "Piauí", "region": "Nordeste", "region_vn": "Đông Bắc"},
    "SE": {"name": "Sergipe", "region": "Nordeste", "region_vn": "Đông Bắc"},
    
    # Vùng Trung Tây (Centro-Oeste) - Trung tâm chính trị & nông nghiệp
    "DF": {"name": "Distrito Federal (Brasília)", "region": "Centro-Oeste", "region_vn": "Trung Tây"},
    "GO": {"name": "Goiás", "region": "Centro-Oeste", "region_vn": "Trung Tây"},
    "MT": {"name": "Mato Grosso", "region": "Centro-Oeste", "region_vn": "Trung Tây"},
    "MS": {"name": "Mato Grosso do Sul", "region": "Centro-Oeste", "region_vn": "Trung Tây"},
    
    # Vùng Bắc (Norte) - Địa bàn rộng lớn, lưu vực sông Amazon, logistics phức tạp
    "PA": {"name": "Pará", "region": "Norte", "region_vn": "Bắc"},
    "AM": {"name": "Amazonas", "region": "Norte", "region_vn": "Bắc"},
    "RO": {"name": "Rondônia", "region": "Norte", "region_vn": "Bắc"},
    "TO": {"name": "Tocantins", "region": "Norte", "region_vn": "Bắc"},
    "AC": {"name": "Acre", "region": "Norte", "region_vn": "Bắc"},
    "AP": {"name": "Amapá", "region": "Norte", "region_vn": "Bắc"},
    "RR": {"name": "Roraima", "region": "Norte", "region_vn": "Bắc"}
}


def load_and_inspect_raw_data(file_path: str) -> pd.DataFrame:
    """Tải dữ liệu thô và thực hiện kiểm tra tính toàn vẹn ban đầu."""
    print("=" * 70)
    print("BƯỚC 1: ĐỌC VÀ KIỂM TRA DỮ LIỆU THÔ (RAW DATA AUDIT)")
    print("=" * 70)
    
    # Đọc dữ liệu với mã bưu điện định dạng chuỗi để tránh mất số 0 ở đầu
    df = pd.read_csv(file_path, dtype={"customer_zip_code_prefix": str})
    print(f"-> Tổng số dòng dữ liệu: {len(df):,}")
    print(f"-> Danh sách cột: {df.columns.tolist()}")
    
    # Kiểm tra giá trị thiếu (Missing values)
    missing = df.isnull().sum()
    print("\n[Kiểm tra giá trị khuyết thiếu (Null/NaN)]:")
    print(missing[missing > 0] if missing.sum() > 0 else "-> Không có dòng nào bị khuyết thiếu (Clean Data)!")
    
    # Kiểm tra trùng lặp ID đơn hàng
    dup_customers = df['customer_id'].duplicated().sum()
    print(f"-> Trùng lặp customer_id: {dup_customers} (Phải bằng 0 vì mỗi customer_id là 1 giao dịch đơn hàng)")
    
    # Đếm số lượng khách hàng định danh duy nhất (Unique Human Customers)
    unique_humans = df['customer_unique_id'].nunique()
    print(f"-> Tổng số khách hàng định danh (customer_unique_id): {unique_humans:,}")
    print(f"-> Chênh lệch số đơn hàng và số khách hàng: {len(df) - unique_humans:,} đơn hàng lặp lại")
    
    return df


def clean_and_enrich_data(df: pd.DataFrame) -> pd.DataFrame:
    """Thực hiện chuẩn hóa dữ liệu và làm giàu thêm thông tin kinh doanh."""
    print("\n" + "=" * 70)
    print("BƯỚC 2: TIỀN XỬ LÝ, CHUẨN HÓA VÀ LÀM GIÀU DỮ LIỆU")
    print("=" * 70)
    
    df_clean = df.copy()
    
    # 1. Chuẩn hóa chuỗi Zip Code (đảm bảo đủ 5 ký tự với padding số 0)
    df_clean['customer_zip_code_prefix'] = df_clean['customer_zip_code_prefix'].str.strip().str.zfill(5)
    
    # 2. Chuẩn hóa Tên thành phố: Cắt khoảng trắng thừa, chuyển dạng Title Case
    df_clean['customer_city'] = df_clean['customer_city'].str.strip().str.title()
    
    # 3. Chuẩn hóa Mã bang: Viết hoa
    df_clean['customer_state'] = df_clean['customer_state'].str.strip().str.upper()
    
    # 4. Làm giàu dữ liệu địa lý (State Name, Macro Region)
    print("-> Ánh xạ tên đầy đủ bang và vùng kinh tế Brazil...")
    df_clean['state_name'] = df_clean['customer_state'].map(lambda s: BRAZIL_STATE_MAPPING.get(s, {}).get("name", s))
    df_clean['region_code'] = df_clean['customer_state'].map(lambda s: BRAZIL_STATE_MAPPING.get(s, {}).get("region", "Khác"))
    df_clean['region_name'] = df_clean['customer_state'].map(
        lambda s: f"{BRAZIL_STATE_MAPPING.get(s, {}).get('region', 'Khác')} ({BRAZIL_STATE_MAPPING.get(s, {}).get('region_vn', 'Khác')})"
    )
    
    # 5. Phân tích hành vi & Tần suất mua hàng (Feature Engineering: Order Count per Customer)
    print("-> Tính toán số lần mua hàng trên mỗi khách hàng...")
    order_counts = df_clean.groupby('customer_unique_id')['customer_id'].transform('count')
    df_clean['order_count'] = order_counts
    
    # 6. Phân khúc khách hàng theo mức độ gắn bó (Customer Segmentation)
    def classify_customer(count: int) -> str:
        if count == 1:
            return "Khách hàng 1 lần (One-off)"
        elif count <= 4:
            return "Khách hàng quay lại (Repeat 2-4)"
        else:
            return "Khách hàng VIP (Loyal 5+)"
            
    df_clean['customer_segment'] = df_clean['order_count'].apply(classify_customer)
    
    # In phân phối phân khúc khách hàng
    print("\n[Phân bố khách hàng theo số lần mua]:")
    seg_summary = df_clean.groupby(['customer_segment', 'order_count'])['customer_unique_id'].nunique()
    print(seg_summary)
    
    return df_clean


def build_star_schema(df_clean: pd.DataFrame):
    """
    Tách dữ liệu theo mô hình Star Schema chuẩn cho Business Intelligence (Power BI):
    - Fact_Customer_Orders: Bảng sự kiện chứa các giao dịch đơn hàng của khách
    - Dim_Geography: Bảng chiều địa lý (Zip code, City, State, Region)
    - Dim_Customers: Bảng chiều khách hàng (Unique ID, Tần suất mua, Phân khúc)
    """
    print("\n" + "=" * 70)
    print("BƯỚC 3: MÔ HÌNH HÓA DỮ LIỆU THEO CHUẨN STAR SCHEMA CHO POWER BI")
    print("=" * 70)
    
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    
    # 1. Bảng Dim_Geography (Chiều Địa lý - Không trùng lặp Zip code prefix + City + State)
    dim_geography = df_clean[[
        'customer_zip_code_prefix', 'customer_city', 'customer_state', 
        'state_name', 'region_code', 'region_name'
    ]].drop_duplicates(subset=['customer_zip_code_prefix']).reset_index(drop=True)
    
    # 2. Bảng Dim_Customers (Chiều Khách hàng duy nhất)
    # Lấy thông tin thuộc tính chính của mỗi customer_unique_id
    dim_customers = df_clean.groupby('customer_unique_id').agg({
        'order_count': 'first',
        'customer_segment': 'first',
        'customer_state': 'first',
        'customer_city': 'first',
        'region_name': 'first'
    }).reset_index()
    
    # 3. Bảng Fact_Customer_Orders (Bảng Fact giao dịch đơn hàng)
    fact_orders = df_clean[[
        'customer_id', 'customer_unique_id', 'customer_zip_code_prefix', 
        'customer_city', 'customer_state', 'region_name', 
        'order_count', 'customer_segment'
    ]].copy()
    
    # Lưu các file CSV đã làm sạch
    clean_csv_path = os.path.join(PROCESSED_DIR, "olist_customers_clean.csv")
    dim_geo_path = os.path.join(PROCESSED_DIR, "dim_geography.csv")
    dim_cust_path = os.path.join(PROCESSED_DIR, "dim_customers.csv")
    fact_orders_path = os.path.join(PROCESSED_DIR, "fact_customer_orders.csv")
    
    df_clean.to_csv(clean_csv_path, index=False, encoding='utf-8-sig')
    dim_geography.to_csv(dim_geo_path, index=False, encoding='utf-8-sig')
    dim_customers.to_csv(dim_cust_path, index=False, encoding='utf-8-sig')
    fact_orders.to_csv(fact_orders_path, index=False, encoding='utf-8-sig')
    
    print(f"-> Đã lưu bảng tổng hợp sạch: {clean_csv_path} ({len(df_clean):,} dòng)")
    print(f"-> Đã lưu Dim_Geography: {dim_geo_path} ({len(dim_geography):,} dòng)")
    print(f"-> Đã lưu Dim_Customers: {dim_cust_path} ({len(dim_customers):,} dòng)")
    print(f"-> Đã lưu Fact_Customer_Orders: {fact_orders_path} ({len(fact_orders):,} dòng)")
    
    return df_clean, dim_geography, dim_customers, fact_orders


def export_to_sqlite(df_clean: pd.DataFrame, dim_geography: pd.DataFrame, 
                     dim_customers: pd.DataFrame, fact_orders: pd.DataFrame):
    """Lưu trữ dữ liệu vào SQLite để thực thi các câu lệnh phân tích SQL."""
    print("\n" + "=" * 70)
    print("BƯỚC 4: LƯU TRỮ VÀO CƠ SỞ DỮ LIỆU SQLITE (olist_analytics.db)")
    print("=" * 70)
    
    conn = sqlite3.connect(SQLITE_DB_PATH)
    
    # Ghi dữ liệu vào các bảng SQLite
    df_clean.to_sql("olist_customers_clean", conn, if_exists="replace", index=False)
    dim_geography.to_sql("dim_geography", conn, if_exists="replace", index=False)
    dim_customers.to_sql("dim_customers", conn, if_exists="replace", index=False)
    fact_orders.to_sql("fact_customer_orders", conn, if_exists="replace", index=False)
    
    # Tạo Index để tăng tốc độ truy vấn SQL
    cursor = conn.cursor()
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fact_cust_id ON fact_customer_orders(customer_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fact_cust_uniq ON fact_customer_orders(customer_unique_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fact_zip ON fact_customer_orders(customer_zip_code_prefix);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_dim_geo_zip ON dim_geography(customer_zip_code_prefix);")
    conn.commit()
    conn.close()
    
    print(f"-> Đã tạo thành công cơ sở dữ liệu SQLite: {SQLITE_DB_PATH}")


def main():
    print("=== BẮT ĐẦU QUY TRÌNH DATA ENGINEERING & DATA CLEANING CHO OLIST ===")
    raw_df = load_and_inspect_raw_data(RAW_DATA_PATH)
    cleaned_df = clean_and_enrich_data(raw_df)
    df_clean, dim_geo, dim_cust, fact_orders = build_star_schema(cleaned_df)
    export_to_sqlite(df_clean, dim_geo, dim_cust, fact_orders)
    print("\n=== HOÀN TẤT THÀNH CÔNG QUY TRÌNH LÀM SẠCH VÀ LÀM GIÀU DỮ LIỆU! ===")


if __name__ == "__main__":
    main()
