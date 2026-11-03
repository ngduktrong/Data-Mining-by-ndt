# Lộ trình thực hiện

1. Đọc và kiểm tra dữ liệu: báo cáo số ván, đội hình, tướng; không giao nhau game/series giữa các tập.
2. Fit Popularity: đếm số đội hình train chứa tướng.
3. Fit Item-item: đếm số đội hình chứa từng cặp tướng khác nhau; cộng điểm từ đội hình đầu vào.
4. Tạo hàm recommend dùng chung cho đánh giá và bàn giao; kiểm tra ID, trùng/mâu thuẫn, đội đủ 5 tướng, k hợp lệ.
5. Validation: mỗi đội hình che lần lượt một tướng, giữ bốn tướng làm ngữ cảnh. So sánh trên cùng trường hợp và ứng viên. Đếm cả target ngoài danh mục train. Ưu tiên NDCG@5, đối chiếu Hit Rate@5.
6. Chốt mô hình và cấu hình trước khi đánh giá test; không điều chỉnh dựa trên kết quả test. Bản đầu giữ mô hình fit train, chưa refit train+validation.
7. Xuất mô hình, kết quả và hướng dẫn cho An.

Lịch dự kiến series là đại diện thời gian, chưa phải thời gian thi đấu thực tế. Nhiều trường hợp che tướng từ cùng ván không phải các mẫu độc lập. Không dùng thống kê toàn giải làm đặc trưng học. Bộ dữ liệu chưa có thứ tự draft, vì vậy không gọi đánh giá che tướng là đánh giá lượt chọn tiếp theo thực tế.
