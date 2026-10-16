-- ==============================================================================
-- DỰ ÁN PHÂN TÍCH DỮ LIỆU KHÁCH HÀNG OLIST (BRAZIL)
-- Tệp: 01_schema_and_views.sql
-- Mục đích: Định nghĩa cấu trúc Schema, Ràng buộc Khóa & Các View phân tích
-- Tác giả: Chuyên viên Phân tích Dữ liệu (Lead Data Analyst)
-- ==============================================================================

-- 1. BẢNG CHIỀU ĐỊA LÝ (DIMENSION GEOGRAPHY)
-- Chứa thông tin chuẩn hóa về mã bưu điện, thành phố, bang và vùng miền Brazil
CREATE TABLE IF NOT EXISTS dim_geography (
    customer_zip_code_prefix VARCHAR(5) PRIMARY KEY,
    customer_city VARCHAR(100) NOT NULL,
    customer_state VARCHAR(2) NOT NULL,
    state_name VARCHAR(100) NOT NULL,
    region_code VARCHAR(50) NOT NULL,
    region_name VARCHAR(100) NOT NULL
);

-- 2. BẢNG CHIỀU KHÁCH HÀNG (DIMENSION CUSTOMERS)
-- Mỗi dòng đại diện cho một khách hàng con người duy nhất (customer_unique_id)
CREATE TABLE IF NOT EXISTS dim_customers (
    customer_unique_id VARCHAR(50) PRIMARY KEY,
    order_count INT NOT NULL DEFAULT 1,
    customer_segment VARCHAR(50) NOT NULL,
    customer_state VARCHAR(2) NOT NULL,
    customer_city VARCHAR(100) NOT NULL,
    region_name VARCHAR(100) NOT NULL
);

-- 3. BẢNG SỰ KIỆN GIAO DỊCH ĐƠN HÀNG (FACT CUSTOMER ORDERS)
-- Mỗi dòng đại diện cho một giao dịch/đơn hàng với mã định danh customer_id
CREATE TABLE IF NOT EXISTS fact_customer_orders (
    customer_id VARCHAR(50) PRIMARY KEY,
    customer_unique_id VARCHAR(50) NOT NULL,
    customer_zip_code_prefix VARCHAR(5) NOT NULL,
    customer_city VARCHAR(100) NOT NULL,
    customer_state VARCHAR(2) NOT NULL,
    region_name VARCHAR(100) NOT NULL,
    order_count INT NOT NULL,
    customer_segment VARCHAR(50) NOT NULL,
    FOREIGN KEY (customer_zip_code_prefix) REFERENCES dim_geography(customer_zip_code_prefix)
);

-- ------------------------------------------------------------------------------
-- TẠO CÁC CHỈ MỤC (INDEXES) TỐI ƯU HÓA HIỆU NĂNG TRUY VẤN
-- ------------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_fact_orders_cust_uniq ON fact_customer_orders(customer_unique_id);
CREATE INDEX IF NOT EXISTS idx_fact_orders_state ON fact_customer_orders(customer_state);
CREATE INDEX IF NOT EXISTS idx_fact_orders_city ON fact_customer_orders(customer_city);
CREATE INDEX IF NOT EXISTS idx_fact_orders_segment ON fact_customer_orders(customer_segment);

-- ------------------------------------------------------------------------------
-- VIEW 1: TỔNG QUAN TỶ LỆ GIỮ CHÂN VÀ MUA LẠI (CUSTOMER RETENTION OVERVIEW)
-- ------------------------------------------------------------------------------
CREATE VIEW IF NOT EXISTS vw_customer_retention_kpi AS
SELECT 
    COUNT(customer_id) AS total_orders,
    COUNT(DISTINCT customer_unique_id) AS total_unique_customers,
    COUNT(DISTINCT CASE WHEN order_count > 1 THEN customer_unique_id END) AS repeat_customers,
    ROUND(
        COUNT(DISTINCT CASE WHEN order_count > 1 THEN customer_unique_id END) * 100.0 / 
        COUNT(DISTINCT customer_unique_id), 
        2
    ) AS repeat_rate_percentage,
    ROUND(
        COUNT(customer_id) * 1.0 / COUNT(DISTINCT customer_unique_id), 
        3
    ) AS avg_orders_per_customer
FROM fact_customer_orders;

-- ------------------------------------------------------------------------------
-- VIEW 2: HIỆU SUẤT PHÂN BỔ THEO ĐẠI VÙNG KINH TẾ (REGIONAL PERFORMANCE)
-- ------------------------------------------------------------------------------
CREATE VIEW IF NOT EXISTS vw_regional_breakdown AS
SELECT 
    region_name,
    COUNT(customer_id) AS order_volume,
    ROUND(COUNT(customer_id) * 100.0 / (SELECT COUNT(*) FROM fact_customer_orders), 2) AS order_share_pct,
    COUNT(DISTINCT customer_unique_id) AS unique_customers,
    COUNT(DISTINCT CASE WHEN order_count > 1 THEN customer_unique_id END) AS repeat_customers,
    ROUND(
        COUNT(DISTINCT CASE WHEN order_count > 1 THEN customer_unique_id END) * 100.0 / 
        NULLIF(COUNT(DISTINCT customer_unique_id), 0), 
        2
    ) AS repeat_rate_pct,
    COUNT(DISTINCT customer_city) AS total_cities_served
FROM fact_customer_orders
GROUP BY region_name
ORDER BY order_volume DESC;

-- ------------------------------------------------------------------------------
-- VIEW 3: XẾP HẠNG PARETO THEO BANG (STATE PARETO ANALYSIS)
-- ------------------------------------------------------------------------------
CREATE VIEW IF NOT EXISTS vw_state_ranking AS
SELECT 
    customer_state,
    region_name,
    COUNT(customer_id) AS total_orders,
    COUNT(DISTINCT customer_unique_id) AS total_customers,
    ROUND(COUNT(customer_id) * 100.0 / (SELECT COUNT(*) FROM fact_customer_orders), 2) AS state_market_share_pct
FROM fact_customer_orders
GROUP BY customer_state, region_name
ORDER BY total_orders DESC;
