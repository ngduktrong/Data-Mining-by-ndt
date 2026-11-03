# Kết quả Liqi v1 — validation

Đã fit 462 đội hình từ 231 ván train; đánh giá 280 trường hợp từ 28 ván, 7 series validation. P1 chỉ dùng 4 đồng đội, che tướng thứ năm. Test cuối chưa chạy.

| Phương pháp | NDCG@5 | Hit Rate@5 | NDCG@10 | Hit Rate@10 | Coverage@5 |
|---|---:|---:|---:|---:|---:|
| popularity | 0.093562 | 13.93% | 0.143259 | 29.29% | 8.43% |
| item_item_count | 0.205040 | 29.29% | 0.252597 | 44.29% | 38.55% |
| item_item_cosine | 0.234796 | 32.14% | 0.277623 | 45.71% | 72.29% |

Cosine được chọn theo NDCG@5 cao nhất. Tìm được 90/280 target trong Top-5. Chênh lệch Hit Rate@5 so với popularity: 18.21 điểm phần trăm.
Có 3 trường hợp target chưa thấy trong train; vẫn tính trong mẫu số. Tỉ lệ fallback request@5: 0.00%. Tỉ lệ trả đủ 5: 100.00%.

Đây là kết quả khôi phục đội hình; không phải tỉ lệ thắng, không đo ban/counter-pick. Chỉ 7 series validation nên chưa kết luận cải thiện tổng quát hay có ý nghĩa thống kê. Chưa thử shrinkage M3.

## Kiểm chứng phần mềm
7 bài kiểm tra tự động passed: số đếm/cosine, đầu vào sai, loại tướng và danh sách ngắn/rỗng, fallback và tướng mới, lưu/nạp lại, công thức metric và target mới, từ chối fit holdout. Demo handoff chạy độc lập với model.json.

## Bước tiếp theo
Đọc bảng kết quả và các dự đoán, kiểm tra mô tả giới hạn. Khi chốt M0–M2, chạy final-test theo README để đánh giá mô hình đã khóa. M3/counter/ban là vòng nghiên cứu bổ sung, không nên chỉnh theo test đã xem.