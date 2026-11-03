# Bàn giao cho An — sau khi huấn luyện hoàn tất

Hiện chưa có mô hình trong thư mục này.

Gói bàn giao dự kiến gồm:
- model.json: popularity, quan hệ item-item, danh mục ứng viên và tên tướng.
- model_metadata.json: phương pháp, phiên bản dữ liệu, tập fit, tham số, quy tắc fallback và giới hạn.
- recommender.py: hàm load_model và recommend độc lập với web.
- requirements.txt: thư viện thực sự cần để suy luận.
- example_usage.py: cách gọi hàm với ID tướng có thật.
- validation_metrics.json và test_metrics.json: kết quả thực nghiệm đã chạy.

An nạp mô hình khi khởi động ứng dụng, gọi hàm recommend khi nhận trạng thái đội hình. Không huấn luyện lại trong mỗi yêu cầu. An tự triển khai API/UI.

Đầu vào dự kiến: own_picks, enemy_picks, banned, k. Điểm score là điểm xếp hạng, không phải xác suất thắng. source cho biết item_item hay popularity_fallback.
