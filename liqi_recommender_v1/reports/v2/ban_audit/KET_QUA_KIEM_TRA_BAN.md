# Bước 3 — Kiểm tra dữ liệu ban

Trạng thái: passed_with_warnings. Lỗi: 0; cảnh báo: 3.

| Tập | Ván | Lượt ban | Tướng bị ban | Phân bố số ban/ván |
|---|---:|---:|---:|---|
| train | 231 | 1845 | 63 | {8: 228, 7: 3} |
| validation | 28 | 224 | 47 | {8: 28} |

## Những điều cần giữ đúng
- Không có thứ tự ban được xác minh; số ban khác 4/đội chỉ được gắn cờ để xem nguồn, không tự sửa hoặc xóa.
- Bảng tần suất chỉ dùng train; đây là thống kê audit, chưa có mô hình ban hoặc kết quả đánh giá ban.
- Không mở test.csv. draft_actions.csv chứa các tập cùng file: script quét nhãn split và loại dòng test trước thống kê tướng. Không tuyên bố toàn bộ file test chưa từng được đọc ở mức bytes.
- V1 đã được đánh giá test trên máy người dùng. Không sửa code, mô hình hoặc kết quả V1 trong bước này.
- Xem ban_issues.csv và bans_by_team.csv để truy vết cảnh báo. Không coi mẫu ít ban là dữ liệu đầy đủ cho đến khi đối chiếu nguồn.
- Số ban validation có tướng chưa từng bị ban trong train: 2.

## Đề xuất công việc 4 (chưa thực hiện)
Chốt cách xử lý bản ghi cần xem lại; sau đó học baseline ban theo tần suất train. Thiết kế đánh giá khôi phục tập ban riêng, không dùng pick cuối trận làm thông tin biết trước ban.
