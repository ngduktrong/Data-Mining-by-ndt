# Liqi Recommender v1 — huấn luyện và validation đã chạy
Trọng phụ trách mô hình; An phụ trách web. Python >= 3.10, không Hadoop/Spark, không API/frontend, không cần cài thêm thư viện.

## Chạy trên Windows / VS Code
1. Giải nén ZIP, mở thư mục liqi_recommender_v1 bằng File → Open Folder.
2. Mở Terminal → New Terminal.
3. Kiểm tra `python --version`. Có thể dùng `py` thay `python` nếu máy dùng Windows launcher.
4. Chạy lần lượt:

```bash
python run.py check
python -m unittest discover -s tests -v
python run.py develop
python run.py demo
```

check: xác minh hash, đội hình, split train/validation và membership series từ metadata. develop: fit M0/M1/M2, đánh giá validation và chọn mô hình. Chạy lại cùng dữ liệu tái lập kết quả, ghi đè đầu ra phát triển. demo: ví dụ từ train, không chọn theo hit test. run.py tìm dữ liệu theo thư mục dự án.

## Trạng thái
Đã chạy ba phương pháp cố định: popularity, item_item_count, item_item_cosine. Chọn NDCG@5 → Hit Rate@5 → đơn giản hơn. Chưa thử M3; đây là kết quả trong ba phương pháp, không khẳng định tối ưu tuyệt đối.

P1: giữ 4 đồng đội, che 1. Ứng viên là tướng thấy trong train; target mới vẫn tính miss. K chính 5, phụ 10. Test chưa đánh giá. Nhiều ca cùng series không độc lập; không khẳng định ý nghĩa thống kê từ điểm trung bình.

CSV cần thiết đã đóng gói, đổi tên theo manifest nhưng giữ nguyên bytes. Không gộp snapshot. draft_actions được giữ để nghiên cứu sau, không dùng trong mô hình pick hiện tại. test.csv kèm cho bước cuối; develop không đọc payload test, chỉ xem metadata split series. Việc đóng gói bản sao không phải huấn luyện/đánh giá test.

## Xem kết quả
| Vị trí | Nội dung |
|---|---|
| reports/data_quality_report.json | Kiểm tra dữ liệu và phạm vi kiểm tra |
| reports/validation_comparison.csv | Bảng so sánh, mở bằng Excel |
| reports/validation_metrics.json | Metrics, target mới, fallback, coverage, theo series |
| reports/*_validation_predictions.json | Dự đoán từng trường hợp |
| reports/KET_QUA_V1.md | Diễn giải kết quả thực tế |
| artifacts/selected_model.json | Mô hình được chọn |
| artifacts/selection_lock.json | Hash code/config/model và quy tắc chọn |
| handoff/ | Mô hình và hàm suy luận độc lập để An thử tích hợp |

## Test cuối — chỉ chạy sau khi chốt
```bash
python run.py final-test --confirm-final-test
```
Lệnh kiểm tra code/config/model khớp selection_lock, xác minh test và đánh giá mô hình đã chọn. Chưa chạy lệnh này trong ZIP. Không thử các phương pháp khác để chọn lại theo test. Khi đã có test_metrics, develop và final-test từ chối chạy lại trong cùng vòng. Đây là bảo vệ quy trình, không phải bảo mật chống sửa file. Nếu cải tiến theo test, cần holdout mới để đánh giá độc lập.

## Mã nguồn
- src/data_loader.py: đọc CSV, kiểm tra hash, đội hình và split.
- src/train.py: fit popularity, đồng xuất hiện, cosine.
- src/recommender.py: lọc, xếp hạng, dự phòng và thông tin giải thích.
- src/evaluate.py: giao thức P1, metrics và dự đoán.
- run.py: điều phối và xuất gói handoff.
- configs/experiment.json: cấu hình những lựa chọn đã triển khai; giá trị ngoài phạm vi bị từ chối.
- docs/QUY_TAC.md: quy tắc người dùng cung cấp.

Bản này triển khai gợi ý pick ở mức bổ sung đội hình. Counter-pick và ban chưa triển khai, cần giao thức riêng. Chưa có thứ tự draft thật; thời gian chia tập là lịch dự kiến. Điểm không phải xác suất thắng.
