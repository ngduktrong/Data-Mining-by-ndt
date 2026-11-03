# Bàn giao phát triển cho An — test cuối chưa chạy
Python >= 3.10; chỉ thư viện chuẩn. Chạy `python example_usage.py`. Thư mục này chạy độc lập, không cần CSV, src hoặc notebook.

Nạp model.json một lần bằng load_model; gọi recommend(model, own_picks, enemy_picks, banned, k=5). Tất cả đầu vào tướng là danh sách ID trong model.hero_names. Lỗi đầu vào phát sinh ValueError; An quyết định phản hồi trên web.

Đầu ra: recommendations gồm rank, hero_id, hero_name, score, source, popularity_count, evidence; thêm returned_count, unseen_context_heroes, model_version, limitations.

score là tổng trọng số quan hệ; với popularity_fallback score bằng 0 và popularity_count dùng xếp thứ tự dự phòng. Không phải xác suất thắng.

Chỉ hỗ trợ pick bổ sung đội hình; enemy_picks dùng lọc, chưa học counter-pick; chưa có mô hình ban. Chưa kiểm soát luật giải/patch/global ban giữa các ván. Validation dùng 4 đồng đội để khôi phục tướng thứ năm, không chứng minh hiệu quả ở mọi lượt draft.

model_metadata ghi test pending. Sau final-test, pipeline bổ sung test_metrics và cập nhật metadata. Không coi bản này là đã đánh giá cuối.
