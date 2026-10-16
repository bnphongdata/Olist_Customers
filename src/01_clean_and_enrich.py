"""
================================================================================
DỰ ÁN PHÂN TÍCH DỮ LIỆU KHÁCH HÀNG OLIST (BRAZIL E-COMMERCE)
Kịch bản 01: Làm sạch dữ liệu, bổ sung thông tin địa lý & dựng mô hình Star Schema
Tác giả: Phong Bùi (Lead Data Analyst)
Ngôn ngữ: Python 3.14 (Pandas, SQLite3)
================================================================================
"""

import os
import sqlite3
import pandas as pd

# Đường dẫn thư mục làm việc
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW_DATA_PATH = os.path.join(BASE_DIR, "data", "raw", "olist_customers_dataset.csv")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
SQLITE_DB_PATH = os.path.join(BASE_DIR, "data", "olist_analytics.db")

# Bảng tra cứu 27 Bang của Brazil theo 5 Đại vùng kinh tế (IBGE)
# Người Brazil chia đất nước thành 5 vùng rất đặc thù về kinh tế và địa lý:
# - Sudeste (Đông Nam): Giàu nhất, công nghiệp phát triển, tập trung São Paulo, Rio.
# - Sul (Nam): Khí hậu ôn đới, nông nghiệp công nghệ cao, thu nhập khá.
# - Nordeste (Đông Bắc): Dân đông, bãi biển đẹp nhưng kinh tế còn nhiều khó khăn.
# - Centro-Oeste (Trung Tây): Vựa đậu nành, chăn nuôi và có thủ đô Brasília.
# - Norte (Bắc): Rừng Amazon bạt ngàn, diện tích rộng mênh mông nhưng dân thưa, đường sá khó đi.
BRAZIL_STATE_MAPPING = {
    # Vùng Đông Nam (Sudeste) - Đầu tàu kinh tế gánh cả nước
    "SP": {"name": "São Paulo", "region": "Sudeste", "region_vn": "Đông Nam"},
    "RJ": {"name": "Rio de Janeiro", "region": "Sudeste", "region_vn": "Đông Nam"},
    "MG": {"name": "Minas Gerais", "region": "Sudeste", "region_vn": "Đông Nam"},
    "ES": {"name": "Espírito Santo", "region": "Sudeste", "region_vn": "Đông Nam"},
    
    # Vùng Nam (Sul) - Khu vực văn minh, phát triển đồng đều
    "PR": {"name": "Paraná", "region": "Sul", "region_vn": "Nam"},
    "RS": {"name": "Rio Grande do Sul", "region": "Sul", "region_vn": "Nam"},
    "SC": {"name": "Santa Catarina", "region": "Sul", "region_vn": "Nam"},
    
    # Vùng Đông Bắc (Nordeste) - Thị trường tiêu dùng đầy tiềm năng nhưng còn nghèo
    "BA": {"name": "Bahia", "region": "Nordeste", "region_vn": "Đông Bắc"},
    "PE": {"name": "Pernambuco", "region": "Nordeste", "region_vn": "Đông Bắc"},
    "CE": {"name": "Ceará", "region": "Nordeste", "region_vn": "Đông Bắc"},
    "MA": {"name": "Maranhão", "region": "Nordeste", "region_vn": "Đông Bắc"},
    "PB": {"name": "Paraíba", "region": "Nordeste", "region_vn": "Đông Bắc"},
    "RN": {"name": "Rio Grande do Norte", "region": "Nordeste", "region_vn": "Đông Bắc"},
    "AL": {"name": "Alagoas", "region": "Nordeste", "region_vn": "Đông Bắc"},
    "PI": {"name": "Piauí", "region": "Nordeste", "region_vn": "Đông Bắc"},
    "SE": {"name": "Sergipe", "region": "Nordeste", "region_vn": "Đông Bắc"},
    
    # Vùng Trung Tây (Centro-Oeste) - Trung tâm chính trị và thủ phủ nông nghiệp
    "DF": {"name": "Distrito Federal (Brasília)", "region": "Centro-Oeste", "region_vn": "Trung Tây"},
    "GO": {"name": "Goiás", "region": "Centro-Oeste", "region_vn": "Trung Tây"},
    "MT": {"name": "Mato Grosso", "region": "Centro-Oeste", "region_vn": "Trung Tây"},
    "MS": {"name": "Mato Grosso do Sul", "region": "Centro-Oeste", "region_vn": "Trung Tây"},
    
    # Vùng Bắc (Norte) - Lưu vực sông Amazon, thách thức cực lớn cho khâu giao vận
    "PA": {"name": "Pará", "region": "Norte", "region_vn": "Bắc"},
    "AM": {"name": "Amazonas", "region": "Norte", "region_vn": "Bắc"},
    "RO": {"name": "Rondônia", "region": "Norte", "region_vn": "Bắc"},
    "TO": {"name": "Tocantins", "region": "Norte", "region_vn": "Bắc"},
    "AC": {"name": "Acre", "region": "Norte", "region_vn": "Bắc"},
    "AP": {"name": "Amapá", "region": "Norte", "region_vn": "Bắc"},
    "RR": {"name": "Roraima", "region": "Norte", "region_vn": "Bắc"}
}


def load_and_inspect_raw_data(file_path: str) -> pd.DataFrame:
    """
    Bước đầu tiên của người làm dữ liệu:
    Mở file ra ngó nghiêng xem dữ liệu sạch hay bẩn, có bị khuyết ô nào không.
    """
    print("=" * 70)
    print("BƯỚC 1: KHÁM SỨC KHỎE DỮ LIỆU BAN ĐẦU (DATA AUDIT)")
    print("=" * 70)
    
    # Lưu ý: Cột zip code bắt buộc phải đọc kiểu chuỗi (str)
    # Vì nếu để pandas tự nhận diện số nguyên, mã bưu điện ở São Paulo (như 01151) sẽ bị cụt mất số 0 đầu tiên.
    df = pd.read_csv(file_path, dtype={"customer_zip_code_prefix": str})
    print(f"-> Tổng cộng có: {len(df):,} dòng dữ liệu đơn hàng.")
    
    # Kiểm tra xem có dòng nào bị trống thông tin không
    missing = df.isnull().sum()
    if missing.sum() == 0:
        print("-> Tin vui: Bộ dữ liệu này rất sạch, không bị khuyết ô nào (0 Null/NaN)!")
    else:
        print("-> Cảnh báo các cột bị thiếu:", missing[missing > 0])
        
    # Phân biệt giữa "mã đơn" và "mã khách hàng thực tế"
    # Đây là cái bẫy kinh điển: nhiều người lầm tưởng customer_id là ID khách hàng,
    # nhưng thực chất mỗi đơn hàng Olist lại sinh ra 1 customer_id mới.
    # Người thật đằng sau bàn phím chính là customer_unique_id!
    unique_humans = df['customer_unique_id'].nunique()
    print(f"-> Số người thật (customer_unique_id): {unique_humans:,} người.")
    print(f"-> Số đơn hàng phát sinh (customer_id): {len(df):,} đơn.")
    print(f"-> Chênh lệch: {len(df) - unique_humans:,} đơn hàng đến từ những vị khách quay lại mua lần 2, lần 3...")
    
    return df


def clean_and_enrich_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Chuẩn hóa câu chữ, sửa lỗi format và đắp thêm thông tin kinh doanh hữu ích.
    """
    print("\n" + "=" * 70)
    print("BƯỚC 2: TẮM RỬA DỮ LIỆU & BỔ SUNG GÓC NHÌN KINH DOANH")
    print("=" * 70)
    
    df_clean = df.copy()
    
    # 1. Chắc chắn mã bưu điện phải đủ 5 ký tự (thiếu số 0 ở đầu thì đệm vào ngay)
    df_clean['customer_zip_code_prefix'] = df_clean['customer_zip_code_prefix'].str.strip().str.zfill(5)
    
    # 2. Tên thành phố gõ lộn xộn chữ hoa chữ thường thì đưa về chuẩn Title Case (Ví dụ: Sao Paulo)
    df_clean['customer_city'] = df_clean['customer_city'].str.strip().str.title()
    
    # 3. Mã bang thì viết hoa toàn bộ (SP, RJ, MG...)
    df_clean['customer_state'] = df_clean['customer_state'].str.strip().str.upper()
    
    # 4. Gắn thêm tên bang đầy đủ và vùng kinh tế để sau này lên Dashboard nhìn phát biết ngay
    print("-> Đang gán tên bang đầy đủ và phân vùng kinh tế Brazil...")
    df_clean['state_name'] = df_clean['customer_state'].map(lambda s: BRAZIL_STATE_MAPPING.get(s, {}).get("name", s))
    df_clean['region_code'] = df_clean['customer_state'].map(lambda s: BRAZIL_STATE_MAPPING.get(s, {}).get("region", "Khác"))
    df_clean['region_name'] = df_clean['customer_state'].map(
        lambda s: f"{BRAZIL_STATE_MAPPING.get(s, {}).get('region', 'Khác')} ({BRAZIL_STATE_MAPPING.get(s, {}).get('region_vn', 'Khác')})"
    )
    
    # 5. Đếm xem mỗi khách đã mua bao nhiêu lần trong đời
    print("-> Đếm số lần 'chốt đơn' của từng khách hàng...")
    order_counts = df_clean.groupby('customer_unique_id')['customer_id'].transform('count')
    df_clean['order_count'] = order_counts
    
    # 6. Gắn nhãn phân khúc khách hàng theo thói quen mua sắm:
    # - Mua đúng 1 lần: Nhóm vãng lai (chiếm đa số)
    # - Mua 2-4 lần: Nhóm khách quen
    # - Mua từ 5 lần trở lên: Nhóm khách VIP / Khách ruột
    def classify_customer(count: int) -> str:
        if count == 1:
            return "Khách hàng 1 lần (One-off)"
        elif count <= 4:
            return "Khách hàng quay lại (Repeat 2-4)"
        else:
            return "Khách hàng VIP (Loyal 5+)"
            
    df_clean['customer_segment'] = df_clean['order_count'].apply(classify_customer)
    
    print("\n[Thống kê nhanh số lượng khách theo phân khúc]:")
    summary = df_clean.groupby('customer_segment')['customer_unique_id'].nunique()
    for seg, cnt in summary.items():
        print(f"  * {seg}: {cnt:,} khách ({cnt / len(df_clean['customer_unique_id'].unique()) * 100:.2f}%)")
    
    return df_clean


def build_star_schema(df_clean: pd.DataFrame):
    """
    Tách dữ liệu ra thành Fact và Dim (Mô hình Star Schema).
    Tại sao phải làm thế này?
    Vì khi đưa dữ liệu vào Power BI, nếu cứ để một bảng phẳng khổng lồ thì file sẽ rất nặng,
    chạy chậm và viết DAX cực kỳ rối rắm. Tách ra bảng Dimension (chứa thông tin miêu tả)
    và bảng Fact (chứa các sự kiện giao dịch) là chuẩn mực vàng của dân làm BI.
    """
    print("\n" + "=" * 70)
    print("BƯỚC 3: TÁCH BẢNG THEO MÔ HÌNH STAR SCHEMA CHUẨN CHO POWER BI")
    print("=" * 70)
    
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    
    # 1. Bảng Dim_Geography: Chứa danh sách các mã bưu điện, thành phố, bang (không trùng lặp mã zip)
    dim_geography = df_clean[[
        'customer_zip_code_prefix', 'customer_city', 'customer_state', 
        'state_name', 'region_code', 'region_name'
    ]].drop_duplicates(subset=['customer_zip_code_prefix']).reset_index(drop=True)
    
    # 2. Bảng Dim_Customers: Mỗi người 1 dòng duy nhất, ghi nhận số lần mua và phân khúc
    dim_customers = df_clean.groupby('customer_unique_id').agg({
        'order_count': 'first',
        'customer_segment': 'first',
        'customer_state': 'first',
        'customer_city': 'first',
        'region_name': 'first'
    }).reset_index()
    
    # 3. Bảng Fact_Customer_Orders: Chứa toàn bộ các giao dịch đơn hàng thực tế
    fact_orders = df_clean[[
        'customer_id', 'customer_unique_id', 'customer_zip_code_prefix', 
        'customer_city', 'customer_state', 'region_name', 
        'order_count', 'customer_segment'
    ]].copy()
    
    # Xuất ra các file CSV đã làm sạch để nạp vào Power BI
    clean_csv_path = os.path.join(PROCESSED_DIR, "olist_customers_clean.csv")
    dim_geo_path = os.path.join(PROCESSED_DIR, "dim_geography.csv")
    dim_cust_path = os.path.join(PROCESSED_DIR, "dim_customers.csv")
    fact_orders_path = os.path.join(PROCESSED_DIR, "fact_customer_orders.csv")
    
    df_clean.to_csv(clean_csv_path, index=False, encoding='utf-8-sig')
    dim_geography.to_csv(dim_geo_path, index=False, encoding='utf-8-sig')
    dim_customers.to_csv(dim_cust_path, index=False, encoding='utf-8-sig')
    fact_orders.to_csv(fact_orders_path, index=False, encoding='utf-8-sig')
    
    print(f"-> Đã lưu bảng dữ liệu tổng hợp: {clean_csv_path}")
    print(f"-> Đã tạo bảng Dim_Geography: {dim_geo_path} ({len(dim_geography):,} mã bưu điện)")
    print(f"-> Đã tạo bảng Dim_Customers: {dim_cust_path} ({len(dim_customers):,} khách hàng duy nhất)")
    print(f"-> Đã tạo bảng Fact_Customer_Orders: {fact_orders_path} ({len(fact_orders):,} giao dịch)")
    
    return df_clean, dim_geography, dim_customers, fact_orders


def export_to_sqlite(df_clean: pd.DataFrame, dim_geography: pd.DataFrame, 
                     dim_customers: pd.DataFrame, fact_orders: pd.DataFrame):
    """
    Nạp dữ liệu vào cơ sở dữ liệu SQLite cục bộ để viết các câu lệnh SQL phân tích.
    """
    print("\n" + "=" * 70)
    print("BƯỚC 4: LƯU VÀO DATABASE SQLITE ĐỂ CHUẨN BỊ BẮN CÂU TRUY VẤN SQL")
    print("=" * 70)
    
    conn = sqlite3.connect(SQLITE_DB_PATH)
    
    df_clean.to_sql("olist_customers_clean", conn, if_exists="replace", index=False)
    dim_geography.to_sql("dim_geography", conn, if_exists="replace", index=False)
    dim_customers.to_sql("dim_customers", conn, if_exists="replace", index=False)
    fact_orders.to_sql("fact_customer_orders", conn, if_exists="replace", index=False)
    
    # Tạo Index để khi chạy các câu lệnh JOIN hay GROUP BY trong SQL không bị giật lag
    cursor = conn.cursor()
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fact_cust_id ON fact_customer_orders(customer_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fact_cust_uniq ON fact_customer_orders(customer_unique_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fact_zip ON fact_customer_orders(customer_zip_code_prefix);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_dim_geo_zip ON dim_geography(customer_zip_code_prefix);")
    conn.commit()
    conn.close()
    
    print(f"-> Đã tạo Database SQLite tại: {SQLITE_DB_PATH}")


def main():
    print(">>> BẮT ĐẦU QUY TRÌNH XỬ LÝ DỮ LIỆU KHÁCH HÀNG OLIST <<<")
    raw_df = load_and_inspect_raw_data(RAW_DATA_PATH)
    cleaned_df = clean_and_enrich_data(raw_df)
    df_clean, dim_geo, dim_cust, fact_orders = build_star_schema(cleaned_df)
    export_to_sqlite(df_clean, dim_geo, dim_cust, fact_orders)
    print("\n>>> XONG! DỮ LIỆU ĐÃ SẠCH SẼ, NGON LÀNH VÀ SẴN SÀNG CHO PHÂN TÍCH! <<<")


if __name__ == "__main__":
    main()
