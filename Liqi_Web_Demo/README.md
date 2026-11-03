# Liqi — Web chạy thử trên máy

## Khởi động Windows

1. Giải nén ZIP vào thư mục riêng (không cần chép vào dự án V1).
2. Mở CMD tại thư mục có app.py.
3. Chạy:

```bat
python app.py
```

4. Giữ cửa sổ CMD mở, vào trình duyệt: http://127.0.0.1:8000
5. Dừng bằng Ctrl+C trong CMD.

Cần Python 3.10 trở lên; không cần pip install, Node.js hay kết nối mạng.
Nếu cổng 8000 đã dùng:

```bat
python app.py --port 8001
```

Mở http://127.0.0.1:8001. Không mở index.html trực tiếp bằng file://.
Có thể nhấp đôi START_WINDOWS.bat để chạy với cổng mặc định.

## Thử trên giao diện

- Chọn chế độ gợi ý chọn hoặc cấm.
- Chọn nơi thêm tướng: đội bạn, đối thủ, danh sách cấm.
- Tìm tên và bấm vào tướng. Bấm × trên thẻ để bỏ.
- Chọn Top-5 hoặc Top-10, bấm Xem gợi ý.
- Nạp ví dụ để điền nhanh một ngữ cảnh minh họa; Xóa tất cả để bắt đầu lại.
- Mở bằng chứng từng gợi ý pick hoặc tải JSON kết quả.

Mỗi lần đổi ngữ cảnh, kết quả cũ được xóa để tránh đọc nhầm. Gợi ý dùng ID tướng;
giao diện ánh xạ tên qua danh mục model. Không có ảnh tướng hoặc dịch vụ ngoài.

## Model và phạm vi

Gói chứa nguyên thư viện và model bước 9. Pick dùng cosine đã chọn trên validation;
ban dùng ban popularity. Không train lại và không đổi tham số trên web.
Điểm không phải xác suất thắng. Đối thủ chỉ lọc ứng viên, không cộng điểm khắc chế.
Các trường hợp ngữ cảnh ít tướng và ví dụ chỉ là demo, chưa có số đo chất lượng riêng.
Không kiểm tra vai trò, thứ tự lượt, patch, luật giải hoặc global ban.
Các điểm validation P2/B1 đo khôi phục từ ngữ cảnh cuối trận, chưa đánh giá draft theo lượt.
Không dùng kết quả demo để kết luận tăng tỷ lệ thắng.

Web chỉ lắng nghe 127.0.0.1 cho máy đang chạy; không phải bản triển khai production.
Không có đăng nhập, cơ sở dữ liệu hoặc lưu lịch sử; tải JSON bằng nút trên giao diện
nếu muốn lưu. Thư viện có kiểm tra hash khi nạp: giữ nguyên code/model; nếu mismatch,
giải nén lại gói gốc thay vì xóa kiểm tra.

## Kiểm thử

```bat
python -m unittest test_web -v
```

Kiểm thử HTTP chạy server tạm trên localhost: tải giao diện/danh mục, pick/ban trả
đúng model, lỗi request và chặn truy cập đường dẫn ngoài danh sách.
JavaScript đã kiểm tra cú pháp; chưa kiểm tra trực quan trên trình duyệt Windows.

## Cho An

API cục bộ:
- GET /api/heroes: danh mục.
- POST /api/recommend: JSON action, own_picks, enemy_picks, banned, k.

Hàm Python: from liqi_draft import DraftRecommender.
Có thể dùng bản này để thử giao diện trước khi An tích hợp vào backend chính.
