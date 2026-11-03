---
categories:
  - "[[Reference Guides]]"
subjects:
  - "[[{{Subject}}]]"
type: reference-guide
status: in-progress
created: 2026-08-19
---
#  Liqi

document for liqi

---

## Data

### Crawler
A. Dữ liệu Meta & Chỉ số Tướng (Trang chủ Garena & AOV Tracker)
B. Dữ liệu Giải đấu Chuyên nghiệp (ĐTDV, AIC, AWC)

note: chi tiết ở [[Liqi-crawling]]
## Features

| **Các Features**                                              | **Thuật toán gợi ý**                           | **Mục tiêu đầu ra**                                                                                                          |
| ------------------------------------------------------------- | ---------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| **Dự đoán kết quả trận đấu (Match Outcome Prediction)**       | XGBoost, LightGBM, Random Forest               | Dự đoán đội thắng dựa trên đội hình pick tướng (Team Composition), tương khắc chất tướng và chênh lệch tài nguyên ban đầu.   |
| **Phân tích tập phổ biến & Luật kết hợp (Association Rules)** | Apriori, FP-Growth                             | Khai phá các combo tướng đi chung có tỉ lệ thắng cao (ví dụ: Aya + Taara, Rouie + Eland'orr) hoặc chuỗi lên trang bị tối ưu. |
| **Hệ thống gợi ý Cấm/Chọn (Drafting Recommender System)**     | Collaborative Filtering, Graph Neural Networks | Gợi ý lượt pick/counter-pick tiếp theo tối ưu cho đội dựa trên các lượt pick trước đó của đối thủ.                           |
|                                                               |                                                |                                                                                                                              |

## References
- [[Data Mining prj]]

## Phase

### 1. Crawling
- [[Liqi-crawling]]
### 2. Features
1.  Match prediction - An
2. Association Rule - Đại 
3. Recommender system - Trọng 
### 3. Web app