# Kiến trúc ngoại tuyến và bàn giao

Luồng chính: CSV → kiểm tra dữ liệu → train → so sánh trên validation → chốt cấu hình → test cuối → xuất gói bàn giao.

| Module | Trách nhiệm |
|---|---|
| data_loader.py | Đọc CSV UTF-8, giải mã hero_ids, chuyển kiểu rõ ràng |
| data_validation.py | Kiểm tra ID, 5 tướng khác nhau, trùng đội hình, phân chia theo series |
| train.py | Fit popularity và item-item chỉ từ train |
| recommender.py | Nạp mô hình, kiểm tra yêu cầu, lọc, tính điểm, xếp hạng, fallback |
| evaluate.py | Tạo trường hợp che tướng; tính Hit Rate@K, NDCG@K, coverage |
| export_model.py | Đóng gói mô hình, phiên bản, cấu hình, hàm suy luận cho An |

Không cần database cho bản đầu. JSON lưu mô hình, CSV/JSON lưu kết quả. Không có tiến trình phục vụ web trong phần Trọng.

Đầu vào hàm suy luận dự kiến: own_picks, enemy_picks, banned, k (mã tướng chuẩn).
Đầu ra: danh sách hero_id, hero_name, rank, score, source và model_version.

Ứng viên ban đầu: tướng đã có tương tác trong train; loại các tướng đã chọn/cấm. Ghi rõ giới hạn nếu chưa kiểm soát luật giải, phiên bản và hạn chế giữa các ván. Tướng chưa thấy trong train được báo cáo khi đánh giá, không loại âm thầm.
