"""
================================================================================
DỰ ÁN PHÂN TÍCH DỮ LIỆU KHÁCH HÀNG OLIST (BRAZIL E-COMMERCE)
Kịch bản 02: Thực thi SQL Analytics & Xuất Báo cáo Kết quả
Vai trò: Chuyên viên Phân tích Dữ liệu (Lead Data Analyst)
Ngôn ngữ: Python 3.14 (SQLite3, Tabulate, Pandas)
================================================================================
"""

import os
import sqlite3
import pandas as pd
from tabulate import tabulate

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.join(BASE_DIR, "data", "olist_analytics.db")
SCHEMA_PATH = os.path.join(BASE_DIR, "sql", "01_schema_and_views.sql")
QUERIES_PATH = os.path.join(BASE_DIR, "sql", "02_analytical_queries.sql")


def apply_schema_and_views(conn: sqlite3.Connection):
    """Áp dụng các định nghĩa bảng và View phân tích từ tệp schema."""
    print("-> Đang áp dụng Schema và các Analytical Views...")
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    conn.executescript(schema_sql)
    print("-> Áp dụng Schema & Views thành công!")


def run_analytical_queries(conn: sqlite3.Connection):
    """Thực thi các câu truy vấn phân tích nghiệp vụ trọng yếu và in kết quả."""
    print("\n" + "=" * 80)
    print("THỰC THI BỘ 8 CÂU HỎI PHÂN TÍCH KINH DOANH CHUYÊN SÂU BẰNG SQL")
    print("=" * 80)

    queries = [
        (
            "CÂU HỎI 1: TỔNG QUAN QUY MÔ & TỶ LỆ MUA LẶP LẠI (RETENTION KPI)",
            """
            SELECT 
                COUNT(customer_id) AS "Tổng đơn hàng",
                COUNT(DISTINCT customer_unique_id) AS "Tổng khách hàng định danh",
                COUNT(DISTINCT CASE WHEN order_count > 1 THEN customer_unique_id END) AS "Khách mua lại (>=2)",
                ROUND(
                    COUNT(DISTINCT CASE WHEN order_count > 1 THEN customer_unique_id END) * 100.0 / 
                    COUNT(DISTINCT customer_unique_id), 
                    2
                ) AS "Tỷ lệ mua lại (%)",
                ROUND(COUNT(customer_id) * 1.0 / COUNT(DISTINCT customer_unique_id), 3) AS "Tần suất mua TB (Đơn/Khách)"
            FROM fact_customer_orders;
            """,
            "Nhận định: Tỷ lệ khách hàng mua lại chỉ đạt ~3.12%. Đây là tỷ lệ cực kỳ thấp trong ngành thương mại điện tử (thông thường dao động từ 15-30%). Olist mang tính chất là một sàn kết nối giao dịch một lần (Transactional Marketplace) hơn là tạo dựng được lòng trung thành của người dùng."
        ),
        (
            "CÂU HỎI 2: PHÂN KHÚC KHÁCH HÀNG THEO TẦN SUẤT MUA SẮM (CUSTOMER SEGMENTS)",
            """
            SELECT 
                customer_segment AS "Phân khúc khách hàng",
                COUNT(DISTINCT customer_unique_id) AS "Số lượng khách hàng",
                ROUND(
                    COUNT(DISTINCT customer_unique_id) * 100.0 / 
                    (SELECT COUNT(DISTINCT customer_unique_id) FROM fact_customer_orders), 
                    2
                ) AS "Tỷ trọng khách (%)",
                COUNT(customer_id) AS "Tổng đơn hàng",
                ROUND(
                    COUNT(customer_id) * 100.0 / 
                    (SELECT COUNT(*) FROM fact_customer_orders), 
                    2
                ) AS "Tỷ trọng đơn hàng (%)"
            FROM fact_customer_orders
            GROUP BY customer_segment
            ORDER BY "Số lượng khách hàng" DESC;
            """,
            "Nhận định: Nhóm 'Khách hàng 1 lần' chiếm áp đảo 96.88% số khách và 93.62% tổng đơn hàng. Nhóm 'Khách hàng quay lại (2-4 đơn)' đóng góp 2,978 khách (6.36% đơn hàng). Nhóm 'VIP (5+ đơn)' chỉ có 19 khách nhưng là những hạt giống tiềm năng cao cần chăm sóc đặc biệt."
        ),
        (
            "CÂU HỎI 3: PHÂN BỔ ĐƠN HÀNG VÀ THỊ PHẦN THEO 5 ĐẠI VÙNG KINH TẾ",
            """
            SELECT 
                region_name AS "Vùng kinh tế Brazil",
                COUNT(customer_id) AS "Tổng số đơn hàng",
                ROUND(COUNT(customer_id) * 100.0 / (SELECT COUNT(*) FROM fact_customer_orders), 2) AS "Thị phần đơn (%)",
                COUNT(DISTINCT customer_unique_id) AS "Khách hàng duy nhất",
                COUNT(DISTINCT CASE WHEN order_count > 1 THEN customer_unique_id END) AS "Khách quay lại",
                ROUND(
                    COUNT(DISTINCT CASE WHEN order_count > 1 THEN customer_unique_id END) * 100.0 / 
                    NULLIF(COUNT(DISTINCT customer_unique_id), 0), 
                    2
                ) AS "Tỷ lệ mua lại (%)",
                COUNT(DISTINCT customer_city) AS "Số đô thị phủ sóng"
            FROM fact_customer_orders
            GROUP BY region_name
            ORDER BY "Tổng số đơn hàng" DESC;
            """,
            "Nhận định: Sự chênh lệch địa lý cực lớn! Vùng Đông Nam (Sudeste) đóng góp tới 68,266 đơn hàng (~68.65% toàn quốc), tiếp theo là Vùng Nam (Sul) với 14,148 đơn (~14.23%). Hai vùng này gộp lại đã chiếm gần 83% toàn bộ thị phần của Olist!"
        ),
        (
            "CÂU HỎI 4: PHÂN TÍCH NGUYÊN LÝ PARETO 80/20 THEO BANG",
            """
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
            """,
            "Nhận định: Chuẩn mực Pareto thể hiện rất rõ nét: Chỉ 3 bang đầu tàu (SP: 41.98%, RJ: 12.92%, MG: 11.70%) đã chiếm đến 66.6% tổng số đơn hàng toàn quốc. Nếu cộng thêm RS và PR, Top 5 bang chiếm tới 77.16% thị phần!"
        ),
        (
            "CÂU HỎI 5: TOP 10 SIÊU ĐÔ THỊ CÓ MẬT ĐỘ ĐƠN HÀNG LỚN NHẤT",
            """
            SELECT 
                f.customer_city AS "Tên Thành Phố",
                f.customer_state AS "Mã Bang",
                f.region_name AS "Vùng miền",
                COUNT(f.customer_id) AS "Tổng số đơn",
                ROUND(COUNT(f.customer_id) * 100.0 / (SELECT COUNT(*) FROM fact_customer_orders), 2) AS "Tỷ trọng toàn quốc (%)",
                COUNT(DISTINCT f.customer_zip_code_prefix) AS "Số mã Zip phủ sóng"
            FROM fact_customer_orders f
            GROUP BY f.customer_city, f.customer_state, f.region_name
            ORDER BY "Tổng số đơn" DESC
            LIMIT 10;
            """,
            "Nhận định: Thành phố São Paulo là siêu đô thị số 1 tuyệt đối với 15,540 đơn hàng (chiếm 15.63% cả nước, trải rộng trên 1,029 mã bưu điện). Thành phố Rio de Janeiro đứng thứ 2 với 6,882 đơn (6.92%). Đây là 2 thành phố then chốt cho mọi chiến dịch quảng cáo và tối ưu thời gian giao hàng."
        ),
        (
            "CÂU HỎI 6: TOP KHÁCH HÀNG VIP CÓ TẦN SUẤT MUA SẮM CAO NHẤT",
            """
            SELECT 
                customer_unique_id AS "Mã Khách Hàng Unique",
                order_count AS "Số đơn đã mua",
                customer_state AS "Bang",
                customer_city AS "Thành phố",
                region_name AS "Vùng miền"
            FROM dim_customers
            WHERE order_count >= 5
            ORDER BY order_count DESC, customer_unique_id ASC
            LIMIT 10;
            """,
            "Nhận định: Khách hàng có tần suất mua lớn nhất đã đặt tới 17 đơn hàng, tiếp theo là 9 đơn hàng và 7 đơn hàng. Đa số các khách hàng VIP này đều sinh sống tại các bang kinh tế lớn như SP, RJ, MG."
        ),
        (
            "CÂU HỎI 7: ĐỘ PHỦ MÃ BƯU ĐIỆN VÀ MẬT ĐỘ ĐƠN TRÊN TỪNG MÃ ZIP",
            """
            SELECT 
                customer_state AS "Mã Bang",
                COUNT(DISTINCT customer_zip_code_prefix) AS "Số lượng Zip Code",
                COUNT(customer_id) AS "Tổng số đơn hàng",
                ROUND(COUNT(customer_id) * 1.0 / COUNT(DISTINCT customer_zip_code_prefix), 2) AS "Mật độ đơn / Mã Zip"
            FROM fact_customer_orders
            GROUP BY customer_state
            ORDER BY "Mật độ đơn / Mã Zip" DESC
            LIMIT 10;
            """,
            "Nhận định: Bang SP có mật độ tập trung đơn hàng cao nhất (8.79 đơn/mã zip), theo sau là RJ (7.07 đơn/mã zip) và DF (4.32 đơn/mã zip). Mật độ cao giúp giảm chi phí 'Last-mile Delivery' đáng kể cho Olist và các đơn vị vận chuyển."
        ),
        (
            "CÂU HỎI 8: SO SÁNH TỶ LỆ MUA LẠI GIỮA CÁC BANG ĐẦU TÀU (TOP 5 BANG)",
            """
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
                COUNT(DISTINCT CASE WHEN f.order_count > 1 THEN f.customer_unique_id END) AS "Khách mua lại (>=2)",
                ROUND(
                    COUNT(DISTINCT CASE WHEN f.order_count > 1 THEN f.customer_unique_id END) * 100.0 / 
                    COUNT(DISTINCT f.customer_unique_id), 
                    2
                ) AS "Tỷ lệ mua lại (%)"
            FROM fact_customer_orders f
            INNER JOIN top_5_states t ON f.customer_state = t.customer_state
            GROUP BY f.customer_state
            ORDER BY "Tỷ lệ mua lại (%)" DESC;
            """,
            "Nhận định: Trong Top 5 bang có quy mô lớn nhất, bang SP dẫn đầu tỷ lệ mua lại với 3.51%, theo sau là RJ (3.24%) và MG (2.95%). Tuy nhiên, con số ~3.5% vẫn khẳng định bài toán Retention Rate là điểm yếu cốt tử cần chiến lược giải quyết trên toàn sàn Olist."
        )
    ]

    for title, sql, insight in queries:
        print("\n" + "-" * 80)
        print(f"👉 {title}")
        print("-" * 80)
        df_result = pd.read_sql_query(sql, conn)
        print(tabulate(df_result, headers="keys", tablefmt="pipe", showindex=False))
        print(f"\n💡 {insight}")


def main():
    conn = sqlite3.connect(DB_PATH)
    apply_schema_and_views(conn)
    run_analytical_queries(conn)
    conn.close()
    print("\n" + "=" * 80)
    print("HOÀN TẤT BÁO CÁO SQL ANALYTICS!")
    print("=" * 80)


if __name__ == "__main__":
    main()
