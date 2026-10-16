# DỰ ÁN PHÂN TÍCH DỮ LIỆU KHÁCH HÀNG OLIST (BRAZIL E-COMMERCE)

> **Tác giả**: Phong Bùi (Lead Data Analyst)  
> **Kho lưu trữ GitHub**: [https://github.com/bnphongdata/Olist_Customers.git](https://github.com/bnphongdata/Olist_Customers.git)  
> **Công nghệ thực chiến**: Python 3.14 (Pandas, SQLite3), SQL Analytics, Power BI Desktop (DAX & Star Schema Modeling)  

---

## 1. Lời mở đầu: Vì sao lại có dự án này?

Khi nhìn vào gần 100.000 đơn hàng của sàn thương mại điện tử Olist tại Brazil, phần lớn mọi người sẽ chỉ chú ý đến những con số hào nhoáng: bán được bao nhiêu đơn, doanh thu tăng trưởng thế nào. Nhưng đối với một người làm dữ liệu, câu hỏi quan trọng nhất luôn là:
- **Khách hàng thật sự là ai?**
- **Họ mua sắm xong có quay lại không, hay một đi không trở lại?**
- **Hàng hóa đang chảy về đâu trên đất nước Brazil rộng lớn?**

Dự án này được xây dựng để trả lời những câu hỏi hóc búa đó bằng số liệu thực tế, kết hợp giữa kỹ thuật làm sạch dữ liệu (Python), truy vấn kinh doanh (SQL) và trực quan hóa mô hình (Power BI).

---

## 2. Cấu Trúc Thư Mục Chuẩn Chỉnh

```
Olist_Customers/
├── data/
│   ├── raw/
│   │   └── olist_customers_dataset.csv     # Dữ liệu gốc ban đầu (99.441 dòng)
│   ├── processed/
│   │   ├── olist_customers_clean.csv       # Dữ liệu phẳng đã chuẩn hóa và làm giàu
│   │   ├── dim_geography.csv               # Bảng chiều địa lý (14.994 mã bưu điện)
│   │   ├── dim_customers.csv               # Bảng chiều khách hàng (96.096 người thật)
│   │   └── fact_customer_orders.csv        # Bảng sự kiện giao dịch đơn hàng (99.441 đơn)
│   └── olist_analytics.db                  # Database SQLite để truy vấn SQL tốc độ cao
├── sql/
│   ├── 01_schema_and_views.sql             # Tạo bảng, khóa chính/ngoại & các View phân tích
│   └── 02_analytical_queries.sql           # Bộ 8 câu truy vấn giải quyết bài toán kinh doanh
├── src/
│   ├── 01_clean_and_enrich.py              # Code Python làm sạch, đệm số 0 zip code & phân vùng IBGE
│   └── 02_run_sql_analytics.py             # Script tự động chạy SQL và in kết quả kèm góc nhìn Analyst
├── reports/
│   └── 01_data_storytelling_report.md      # Bài viết Storytelling hoàn chỉnh: "Đằng sau 100.000 đơn hàng"
├── powerbi/
│   └── dax_measures_dictionary.md          # Giải thích bản chất 11 thước đo DAX & cách xếp Dashboard
├── .gitignore                              # Bỏ qua file rác và database nhị phân
├── README.md                               # Bạn đang đọc tài liệu này
└── LICENSE                                 # Giấy phép MIT
```

---

## 3. Ba Phát Hiện "Đau Đầu" Nhất Từ Số Liệu

1. **"Tình một đêm" chiếm tới 96,88%**:
   - Cứ 100 khách ghé Olist mua hàng thì có gần 97 người không bao giờ quay lại.
   - Tỷ lệ khách mua lại (Retention Rate) chỉ đạt vỏn vẹn **3,12%**. Tần suất mua trung bình chỉ **1,03 đơn/khách**.
   - Olist đang bị căn bệnh "chiếc thùng thủng đáy": Đổ rất nhiều tiền quảng cáo để lôi khách mới về nhưng không giữ chân được họ.

2. **Cả sàn sống nhờ vùng Đông Nam (Sudeste)**:
   - 3 bang **São Paulo (SP)**, **Rio de Janeiro (RJ)** và **Minas Gerais (MG)** gánh tới **66,6%** đơn hàng toàn sàn.
   - Riêng bang São Paulo đã chiếm **41,98%**. Trong khi miền Bắc rừng rậm Amazon rộng lớn chỉ có **1,86%** đơn hàng vì tiền ship quá đắt đỏ và thời gian giao hàng quá lâu.

3. **Chỉ có đúng 19 khách hàng VIP**:
   - Toàn sàn chỉ có 19 người mua từ 5 đơn trở lên. Vị khách kỷ lục mua tới **17 đơn** tại São Paulo.
   - Điểm chung: Khách VIP đều ở những nơi hàng về nhanh nhất và cước rẻ nhất. Trải nghiệm giao nhận tốt chính là thứ nuôi dưỡng lòng trung thành.

---

## 4. Cách Chạy Thử Dự Án

### Cài thư viện:
```bash
pip install pandas tabulate
```

### Chạy làm sạch dữ liệu:
```bash
python src/01_clean_and_enrich.py
```

### Chạy phân tích SQL:
```bash
python src/02_run_sql_analytics.py
```
