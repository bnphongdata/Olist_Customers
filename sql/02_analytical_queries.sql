-- ==============================================================================
-- DỰ ÁN PHÂN TÍCH DỮ LIỆU KHÁCH HÀNG OLIST (BRAZIL)
-- Tệp: 02_analytical_queries.sql
-- Mục đích: Tập hợp các câu lệnh SQL phân tích chuyên sâu cho bài toán kinh doanh
-- Tác giả: Chuyên viên Phân tích Dữ liệu (Lead Data Analyst)
-- ==============================================================================

-- ==============================================================================
-- CÂU HỎI 1: TỔNG QUAN QUY MÔ & TỶ LỆ MUA LẶP LẠI (OVERALL SCALE & RETENTION RATE)
-- Ý nghĩa kinh doanh:
-- Đo lường chỉ số giữ chân khách hàng (Repeat Purchase Rate). Giúp doanh nghiệp
-- đánh giá xem sàn Olist đang phụ thuộc vào việc đốt tiền tìm khách mới (CAC) 
-- hay đã xây dựng được tệp khách hàng trung thành (Customer Lifetime Value - CLV).
-- ==============================================================================
SELECT 
    COUNT(customer_id) AS "Tổng số giao dịch (Đơn)",
    COUNT(DISTINCT customer_unique_id) AS "Tổng khách hàng định danh",
    COUNT(DISTINCT CASE WHEN order_count > 1 THEN customer_unique_id END) AS "Số khách hàng quay lại (>=2 lần)",
    ROUND(
        COUNT(DISTINCT CASE WHEN order_count > 1 THEN customer_unique_id END) * 100.0 / 
        COUNT(DISTINCT customer_unique_id), 
        2
    ) AS "Tỷ lệ mua lại (%)",
    ROUND(COUNT(customer_id) * 1.0 / COUNT(DISTINCT customer_unique_id), 3) AS "Tần suất mua TB (Đơn/Khách)"
FROM fact_customer_orders;


-- ==============================================================================
-- CÂU HỎI 2: PHÂN KHÚC KHÁCH HÀNG THEO TẦN SUẤT MUA SẮM (CUSTOMER SEGMENTATION)
-- Ý nghĩa kinh doanh:
-- Phân loại tệp khách hàng thành 3 nhóm: One-off (1 đơn), Repeat (2-4 đơn), VIP (>=5 đơn).
-- Từ đó xây dựng kịch bản marketing cá nhân hóa (Email Automation, Voucher cho lần mua thứ 2).
-- ==============================================================================
SELECT 
    customer_segment AS "Phân khúc khách hàng",
    COUNT(DISTINCT customer_unique_id) AS "Số lượng khách hàng",
    ROUND(
        COUNT(DISTINCT customer_unique_id) * 100.0 / 
        (SELECT COUNT(DISTINCT customer_unique_id) FROM fact_customer_orders), 
        2
    ) AS "Tỷ trọng khách hàng (%)",
    COUNT(customer_id) AS "Tổng số đơn hàng đóng góp",
    ROUND(
        COUNT(customer_id) * 100.0 / 
        (SELECT COUNT(*) FROM fact_customer_orders), 
        2
    ) AS "Tỷ trọng đơn hàng đóng góp (%)"
FROM fact_customer_orders
GROUP BY customer_segment
ORDER BY "Số lượng khách hàng" DESC;


-- ==============================================================================
-- CÂU HỎI 3: PHÂN BỔ ĐƠN HÀNG VÀ THỊ PHẦN THEO 5 ĐẠI VÙNG KINH TẾ BRAZIL
-- Ý nghĩa kinh doanh:
-- So sánh cơ cấu thị phần giữa 5 vùng kinh tế (Đông Nam, Nam, Đông Bắc, Trung Tây, Bắc).
-- Xác định đâu là thị trường cốt lõi (Core Market) và đâu là thị trường ngách (Frontier Market).
-- ==============================================================================
SELECT 
    region_name AS "Vùng kinh tế Brazil",
    COUNT(customer_id) AS "Tổng số đơn hàng",
    ROUND(COUNT(customer_id) * 100.0 / (SELECT COUNT(*) FROM fact_customer_orders), 2) AS "Thị phần đơn hàng (%)",
    COUNT(DISTINCT customer_unique_id) AS "Khách hàng duy nhất",
    COUNT(DISTINCT CASE WHEN order_count > 1 THEN customer_unique_id END) AS "Khách quay lại",
    ROUND(
        COUNT(DISTINCT CASE WHEN order_count > 1 THEN customer_unique_id END) * 100.0 / 
        NULLIF(COUNT(DISTINCT customer_unique_id), 0), 
        2
    ) AS "Tỷ lệ mua lại theo vùng (%)",
    COUNT(DISTINCT customer_city) AS "Số đô thị phủ sóng"
FROM fact_customer_orders
GROUP BY region_name
ORDER BY "Tổng số đơn hàng" DESC;


-- ==============================================================================
-- CÂU HỎI 4: NGUYÊN LÝ PARETO 80/20 THEO BANG (STATE PARETO & CUMULATIVE SHARE)
-- Ý nghĩa kinh doanh:
-- Sử dụng Window Function để tính % thị phần tích lũy của từng bang.
-- Giúp chứng minh liệu quy luật Pareto 80/20 có xảy ra tại Olist hay không
-- (Liệu 20% số bang có tạo ra 80% sản lượng đơn hàng?).
-- ==============================================================================
WITH state_summary AS (
    SELECT 
        customer_state AS state_code,
        region_name,
        COUNT(customer_id) AS state_orders,
        ROUND(COUNT(customer_id) * 100.0 / (SELECT COUNT(*) FROM fact_customer_orders), 2) AS order_share_pct
    FROM fact_customer_orders
    GROUP BY customer_state, region_name
)
SELECT 
    state_code AS "Mã Bang",
    region_name AS "Vùng miền",
    state_orders AS "Số đơn hàng",
    order_share_pct AS "Thị phần bang (%)",
    ROUND(SUM(order_share_pct) OVER (ORDER BY state_orders DESC), 2) AS "Thị phần tích lũy (%)"
FROM state_summary
ORDER BY state_orders DESC
LIMIT 10;


-- ==============================================================================
-- CÂU HỎI 5: TOP 10 SIÊU ĐÔ THỊ CÓ MẬT ĐỘ ĐƠN HÀNG LỚN NHẤT (TOP 10 CITIES)
-- Ý nghĩa kinh doanh:
-- Xác định các thành phố đầu tàu cần ưu tiên kho trung chuyển (Fulfillment Hubs) 
-- và đàm phán hợp đồng vận chuyển hỏa tốc (Same-day/Next-day delivery).
-- ==============================================================================
SELECT 
    f.customer_city AS "Tên Thành Phố",
    f.customer_state AS "Mã Bang",
    f.region_name AS "Vùng miền",
    COUNT(f.customer_id) AS "Tổng số đơn",
    ROUND(COUNT(f.customer_id) * 100.0 / (SELECT COUNT(*) FROM fact_customer_orders), 2) AS "Tỷ trọng toàn quốc (%)",
    COUNT(DISTINCT f.customer_zip_code_prefix) AS "Số mã bưu điện phủ sóng"
FROM fact_customer_orders f
GROUP BY f.customer_city, f.customer_state, f.region_name
ORDER BY "Tổng số đơn" DESC
LIMIT 10;


-- ==============================================================================
-- CÂU HỎI 6: TOP KHÁCH HÀNG "SUPER VIP" CÓ TẦN SUẤT MUA SẮM CAO NHẤT
-- Ý nghĩa kinh doanh:
-- Khảo sát những khách hàng mua nhiều nhất để nghiên cứu hồ sơ (User Persona),
-- tìm hiểu xem họ là khách hàng mua buôn (B2B/Reseller) hay khách hàng cá nhân siêu trung thành.
-- ==============================================================================
SELECT 
    customer_unique_id AS "Mã Khách Hàng Unique",
    order_count AS "Số đơn đã mua",
    customer_state AS "Bang cư trú",
    customer_city AS "Thành phố",
    region_name AS "Vùng miền"
FROM dim_customers
WHERE order_count >= 5
ORDER BY order_count DESC, customer_unique_id ASC
LIMIT 10;


-- ==============================================================================
-- CÂU HỎI 7: ĐỘ PHỦ MÃ BƯU ĐIỆN VÀ MẬT ĐỘ ĐƠN TRÊN TỪNG MÃ ZIP
-- Ý nghĩa kinh doanh:
-- Đánh giá hiệu quả phân bổ tuyến giao vận (Logistics Route Density).
-- Những khu vực có số đơn/mã bưu điện cao là điểm vàng để mở PUDO (Pick-up/Drop-off points).
-- ==============================================================================
SELECT 
    customer_state AS "Mã Bang",
    COUNT(DISTINCT customer_zip_code_prefix) AS "Số lượng Zip Code",
    COUNT(customer_id) AS "Tổng số đơn hàng",
    ROUND(COUNT(customer_id) * 1.0 / COUNT(DISTINCT customer_zip_code_prefix), 2) AS "Mật độ đơn / Mã Zip"
FROM fact_customer_orders
GROUP BY customer_state
ORDER BY "Mật độ đơn / Mã Zip" DESC
LIMIT 10;


-- ==============================================================================
-- CÂU HỎI 8: SO SÁNH TỶ LỆ KHÁCH HÀNG TRUNG THÀNH GIỮA CÁC BANG LỚN (TOP 5 BANG)
-- Ý nghĩa kinh doanh:
-- Tìm hiểu xem bang nào có tỷ lệ khách hàng mua lại cao nhất trong top 5 bang đầu tàu,
-- từ đó đánh giá sự chênh lệch chất lượng trải nghiệm khách hàng (CX) giữa các địa phương.
-- ==============================================================================
WITH top_5_states AS (
    SELECT customer_state
    FROM fact_customer_orders
    GROUP BY customer_state
    ORDER BY COUNT(customer_id) DESC
    LIMIT 5
)
SELECT 
    f.customer_state AS "Mã Bang",
    COUNT(DISTINCT f.customer_unique_id) AS "Tổng khách hàng",
    COUNT(DISTINCT CASE WHEN f.order_count > 1 THEN f.customer_unique_id END) AS "Khách mua lại (>=2 lần)",
    ROUND(
        COUNT(DISTINCT CASE WHEN f.order_count > 1 THEN f.customer_unique_id END) * 100.0 / 
        COUNT(DISTINCT f.customer_unique_id), 
        2
    ) AS "Tỷ lệ mua lại (%)"
FROM fact_customer_orders f
INNER JOIN top_5_states t ON f.customer_state = t.customer_state
GROUP BY f.customer_state
ORDER BY "Tỷ lệ mua lại (%)" DESC;
