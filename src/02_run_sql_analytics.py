"""
================================================================================
DỰ ÁN PHÂN TÍCH DỮ LIỆU KHÁCH HÀNG OLIST (BRAZIL E-COMMERCE)
Kịch bản 02: Thực thi SQL Analytics & Bóc tách sự thật từ các con số
Tác giả: Phong Bùi (Lead Data Analyst)
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


def apply_schema_and_views(conn: sqlite3.Connection):
    """Cập nhật các View phân tích vào database nếu chưa có."""
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    conn.executescript(schema_sql)


def run_analytical_queries(conn: sqlite3.Connection):
    """
    Thực thi 8 câu truy vấn và đưa ra lời bình luận thẳng thắn dưới góc độ kinh doanh.
    """
    print("\n" + "=" * 80)
    print("BỘ 8 CÂU HỎI PHÂN TÍCH THỰC CHIẾN TỪ DỮ LIỆU KHÁCH HÀNG OLIST")
    print("=" * 80)

    queries = [
        (
            "CÂU 1: CỨ 100 KHÁCH GHÉ MUA THÌ CÓ MẤY NGƯỜI CHỊU QUAY LẠI?",
            """
            SELECT 
                COUNT(customer_id) AS "Tổng số đơn",
                COUNT(DISTINCT customer_unique_id) AS "Tổng số khách",
                COUNT(DISTINCT CASE WHEN order_count > 1 THEN customer_unique_id END) AS "Khách có quay lại (>=2)",
                ROUND(
                    COUNT(DISTINCT CASE WHEN order_count > 1 THEN customer_unique_id END) * 100.0 / 
                    COUNT(DISTINCT customer_unique_id), 
                    2
                ) AS "Tỷ lệ quay lại (%)",
                ROUND(COUNT(customer_id) * 1.0 / COUNT(DISTINCT customer_unique_id), 3) AS "Bình quân Đơn / Khách"
            FROM fact_customer_orders;
            """,
            "Góc nhìn của tôi: Con số 3.12% này thực sự là một hồi chuông cảnh báo. Bình quân mỗi khách ghé sàn chỉ mua 1.03 đơn rồi 'bốc hơi'. Olist đang hoạt động như một cái phễu hứng khách vãng lai nhiều hơn là một thương hiệu xây dựng được lòng tin và sự trung thành của người tiêu dùng."
        ),
        (
            "CÂU 2: AI ĐANG THỰC SỰ GIỮ NỒI CƠM CHO OLIST?",
            """
            SELECT 
                customer_segment AS "Nhóm khách hàng",
                COUNT(DISTINCT customer_unique_id) AS "Số lượng khách (người)",
                ROUND(
                    COUNT(DISTINCT customer_unique_id) * 100.0 / 
                    (SELECT COUNT(DISTINCT customer_unique_id) FROM fact_customer_orders), 
                    2
                ) AS "Tỷ trọng khách (%)",
                COUNT(customer_id) AS "Số đơn hàng",
                ROUND(
                    COUNT(customer_id) * 100.0 / 
                    (SELECT COUNT(*) FROM fact_customer_orders), 
                    2
                ) AS "Tỷ trọng đơn hàng (%)"
            FROM fact_customer_orders
            GROUP BY customer_segment
            ORDER BY "Số lượng khách (người)" DESC;
            """,
            "Góc nhìn của tôi: 96.88% khách hàng chỉ xuất hiện đúng 1 lần trong đời trên Olist. Nhóm khách quen (2-4 đơn) chỉ đóng góp hơn 6% lượng đơn. Nhóm VIP (từ 5 đơn trở lên) vỏn vẹn đúng 19 người! Doanh thu của Olist gần như phụ thuộc 100% vào việc liên tục tìm kiếm khách mới."
        ),
        (
            "CÂU 3: NGƯỜI DÂN Ở VÙNG MIỀN NÀO ĐANG ĐẶT HÀNG NHIỀU NHẤT?",
            """
            SELECT 
                region_name AS "Vùng kinh tế Brazil",
                COUNT(customer_id) AS "Số đơn hàng",
                ROUND(COUNT(customer_id) * 100.0 / (SELECT COUNT(*) FROM fact_customer_orders), 2) AS "Thị phần đơn (%)",
                COUNT(DISTINCT customer_unique_id) AS "Số khách hàng",
                COUNT(DISTINCT CASE WHEN order_count > 1 THEN customer_unique_id END) AS "Khách quay lại",
                ROUND(
                    COUNT(DISTINCT CASE WHEN order_count > 1 THEN customer_unique_id END) * 100.0 / 
                    NULLIF(COUNT(DISTINCT customer_unique_id), 0), 
                    2
                ) AS "Tỷ lệ quay lại (%)",
                COUNT(DISTINCT customer_city) AS "Số đô thị có đơn"
            FROM fact_customer_orders
            GROUP BY region_name
            ORDER BY "Số đơn hàng" DESC;
            """,
            "Góc nhìn của tôi: Một sự lệch pha không thể chối cãi: Vùng Đông Nam (Sudeste) một mình gánh tới 68.65% sản lượng đơn toàn sàn, cộng thêm vùng Nam là chiếm gần 83%. Trong khi đó, vùng Bắc bạt ngàn chỉ đóng góp 1.86%. Lý do lớn nhất không phải người miền Bắc không có tiền, mà là tiền ship đắt gấp đôi và thời gian đợi hàng cả nửa tháng trời!"
        ),
        (
            "CÂU 4: NGUYÊN LÝ 80/20 THỂ HIỆN RA SAO TRÊN CÁC BANG?",
            """
            WITH bang_tong_hop AS (
                SELECT 
                    customer_state AS ma_bang,
                    region_name AS vung_mien,
                    COUNT(customer_id) AS so_don_bang,
                    ROUND(COUNT(customer_id) * 100.0 / (SELECT COUNT(*) FROM fact_customer_orders), 2) AS ty_trong_pct
                FROM fact_customer_orders
                GROUP BY customer_state, region_name
            )
            SELECT 
                ma_bang AS "Mã Bang",
                vung_mien AS "Vùng miền",
                so_don_bang AS "Số đơn hàng",
                ty_trong_pct AS "Thị phần bang (%)",
                ROUND(SUM(ty_trong_pct) OVER (ORDER BY so_don_bang DESC), 2) AS "Thị phần tích lũy (%)"
            FROM bang_tong_hop
            ORDER BY so_don_bang DESC
            LIMIT 10;
            """,
            "Góc nhìn của tôi: Chỉ riêng 3 bang SP (São Paulo), RJ (Rio) và MG (Minas Gerais) đã nuốt trọn 66.6% đơn hàng. Nếu tính thêm Top 5 bang lớn nhất thì con số đã lên tới 77.17%. Olist chỉ cần giữ vững được 5 bang này là đã nắm chắc trong tay gần 4/5 'nồi cơm' của cả công ty."
        ),
        (
            "CÂU 5: TOP 10 THÀNH PHỐ ĐẦU TÀU TIÊU THỤ HÀNG HÓA",
            """
            SELECT 
                f.customer_city AS "Thành phố",
                f.customer_state AS "Bang",
                f.region_name AS "Vùng miền",
                COUNT(f.customer_id) AS "Số đơn hàng",
                ROUND(COUNT(f.customer_id) * 100.0 / (SELECT COUNT(*) FROM fact_customer_orders), 2) AS "Tỷ trọng toàn quốc (%)",
                COUNT(DISTINCT f.customer_zip_code_prefix) AS "Số mã Zip phủ sóng"
            FROM fact_customer_orders f
            GROUP BY f.customer_city, f.customer_state, f.region_name
            ORDER BY "Số đơn hàng" DESC
            LIMIT 10;
            """,
            "Góc nhìn của tôi: Thủ phủ tài chính São Paulo là ông vua không ngai với hơn 15.500 đơn (chiếm 15.63% cả nước). Đứng thứ hai là Rio de Janeiro với gần 6.900 đơn. Đây là 2 địa bàn vàng mà Olist bắt buộc phải đàm phán hợp đồng độc quyền với các đơn vị giao vận để cung cấp dịch vụ giao hàng 24h."
        ),
        (
            "CÂU 6: DANH TÍNH NHỮNG VỊ KHÁCH 'CHỊU CHI' NHẤT TOÀN SÀN",
            """
            SELECT 
                customer_unique_id AS "Mã khách hàng bí danh",
                order_count AS "Số đơn đã chốt",
                customer_state AS "Bang",
                customer_city AS "Thành phố",
                region_name AS "Vùng miền"
            FROM dim_customers
            WHERE order_count >= 5
            ORDER BY order_count DESC, customer_unique_id ASC
            LIMIT 10;
            """,
            "Góc nhìn của tôi: Quán quân mua sắm là một khách hàng tại thành phố São Paulo với 17 lần chốt đơn! Vị khách thứ hai ở thành phố biển Praia Grande với 9 lần. Hãy nhìn địa chỉ của họ: Đều ở São Paulo, Rio, Minas Gerais - những nơi hàng về nhanh nhất, phí ship rẻ nhất. Trải nghiệm giao nhận tốt chính là thứ nuôi dưỡng lòng trung thành!"
        ),
        (
            "CÂU 7: ĐỘ DÀY ĐẶC CỦA ĐƠN HÀNG TRÊN TỪNG MÃ BƯU ĐIỆN",
            """
            SELECT 
                customer_state AS "Mã Bang",
                COUNT(DISTINCT customer_zip_code_prefix) AS "Số mã Zip",
                COUNT(customer_id) AS "Tổng số đơn hàng",
                ROUND(COUNT(customer_id) * 1.0 / COUNT(DISTINCT customer_zip_code_prefix), 2) AS "Bình quân Đơn / Mã Zip"
            FROM fact_customer_orders
            GROUP BY customer_state
            ORDER BY "Bình quân Đơn / Mã Zip" DESC
            LIMIT 10;
            """,
            "Góc nhìn của tôi: Bang Rio de Janeiro và São Paulo có mật độ đơn gom cực dày (hơn 10 đơn và 7.5 đơn trên mỗi mã bưu điện). Với mật độ này, shipper chỉ cần đứng ở 1 ngã tư là giao được cả chục đơn, chi phí giao vận chặng cuối (Last-mile cost) giảm xuống mức tối thiểu, biên lợi nhuận của đơn hàng sẽ là cao nhất."
        ),
        (
            "CÂU 8: SO KÈ TỶ LỆ KHÁCH QUEN Ở TOP 5 BANG LỚN NHẤT",
            """
            WITH top_5_bang AS (
                SELECT customer_state
                FROM fact_customer_orders
                GROUP BY customer_state
                ORDER BY COUNT(customer_id) DESC
                LIMIT 5
            )
            SELECT 
                f.customer_state AS "Mã Bang",
                COUNT(DISTINCT f.customer_unique_id) AS "Tổng số khách",
                COUNT(DISTINCT CASE WHEN f.order_count > 1 THEN f.customer_unique_id END) AS "Khách có quay lại (>=2)",
                ROUND(
                    COUNT(DISTINCT CASE WHEN f.order_count > 1 THEN f.customer_unique_id END) * 100.0 / 
                    COUNT(DISTINCT f.customer_unique_id), 
                    2
                ) AS "Tỷ lệ mua lại (%)"
            FROM fact_customer_orders f
            INNER JOIN top_5_bang t ON f.customer_state = t.customer_state
            GROUP BY f.customer_state
            ORDER BY "Tỷ lệ mua lại (%)" DESC;
            """,
            "Góc nhìn của tôi: Kể cả ở Rio de Janeiro (nơi dẫn đầu) thì tỷ lệ mua lại cũng chỉ ngấp nghé 3.46%, São Paulo 3.26%, Minas Gerais 3.09%. Tức là ngay tại 'sân nhà' có điều kiện giao nhận tốt nhất, khách hàng cũng chưa thực sự gắn bó với Olist. Đây là bài toán sống còn mà Ban Giám Đốc phải tìm lời giải trong năm tới."
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
    print("HOÀN TẤT PHÂN TÍCH! SỐ LIỆU ĐÃ BIẾT KỂ CHUYỆN!")
    print("=" * 80)


if __name__ == "__main__":
    main()
