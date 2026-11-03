# Liqi — Gói bàn giao pick/ban cho An

## Chạy ngay

Giải nén gói vào một thư mục riêng. Không chép đè dự án huấn luyện V1.
Mở terminal trong thư mục có demo.py và chạy:

```bat
python -m unittest test_handoff -v
python demo.py --request examples/pick_request.json
python demo.py --request examples/ban_request.json
python demo.py --heroes
```

Python >= 3.10, chỉ dùng thư viện chuẩn. Gói đã chứa model và cấu hình;
không cần data/raw, không train lại, không kết nối mạng.
Các request mẫu lấy ngữ cảnh từ train để kiểm tra kỹ thuật, không dùng làm bằng
chứng chất lượng. Các file response đi kèm là đầu ra tham chiếu tương ứng.

## An tích hợp

Chép nguyên thư mục liqi_draft vào dự án Python của An, ở vị trí import được.
Khởi tạo một lần khi ứng dụng khởi động; gọi recommend cho từng request:

```python
from liqi_draft import DraftRecommender

recommender = DraftRecommender()
result = recommender.recommend({
    'action': 'pick',
    'own_picks': [],
    'enemy_picks': [],
    'banned': [],
    'k': 5,
})
```

Đổi action thành 'ban' để gợi ý ban. Danh mục tên/ID:

```python
heroes = recommender.heroes()
```

An phụ trách API/web; gói này cung cấp hàm Python, chưa có HTTP server.
Nếu backend dùng ngôn ngữ khác, cần một lớp dịch vụ Python hoặc chuyển thuật toán
và đối chiếu lại đầu ra. Không thể import trực tiếp Python vào JavaScript phía trình duyệt.
Khi nhận ValueError do request, API có thể trả HTTP 400; lỗi thiếu/sai file lúc
khởi động phải được xử lý như lỗi triển khai, không trả nhầm là lỗi người dùng.
Không gửi traceback hoặc đường dẫn máy chủ về giao diện.

## Hợp đồng đầu vào

| Trường | Quy tắc |
|---|---|
| action | Bắt buộc: pick hoặc ban |
| own_picks | Mảng hero_id; mặc định [] |
| enemy_picks | Mảng hero_id; mặc định [] |
| banned | Mảng hero_id; mặc định [] |
| k | Số nguyên 1–100; mặc định 5 |

Pick nhận tối đa 4 own_picks, 5 enemy_picks. Ban nhận tối đa 5 pick mỗi đội.
Không cho phép null thay mảng, ID lạ, ID trùng trong mảng hoặc giữa các mảng.
Không nhận method/weight/alpha từ client: cấu hình serving đã cố định theo kết quả chọn.
heroes() trả pick_candidate/ban_candidate: có tên trong danh mục không đồng nghĩa
được gợi ý. Pick có 83 ứng viên train, ban có 63 ứng viên có ban trong train.
Nếu không còn ứng viên trả recommendations=[] và returned_count=0, không báo lỗi.
Nếu còn ít hơn K thì trả danh sách ngắn, không thêm tướng không có thống kê.

## Hợp đồng đầu ra

Hai action đều có schema_version, release_version, action, model_version, method,
score_type, recommendations, requested_k, returned_count, evaluation, capabilities,
limitations. Mỗi gợi ý có rank (bắt đầu 1), hero_id, hero_name, score, evidence.

Pick evidence gồm train_lineup_count và cosine với từng đồng đội. Ban evidence
có train_ban_count và train_games. Không dùng bằng chứng đối đầu để giải thích
cosine vì phương pháp đã chọn không cộng điểm đối thủ.

- Pick: method=cosine, score_type=mean_ally_cosine; trung bình tương đồng đồng đội.
- Ban: method=ban_popularity, score_type=observed_train_ban_game_frequency.
- Score không phải xác suất thắng; không hiển thị như tỷ lệ thắng trên web.
- Cả hai loại trừ tướng đã chọn/cấm. Không dùng đối thủ để tính điểm.
- Khi mọi điểm pick bằng 0, xếp bằng tần suất train rồi ID; cờ
  popularity_tiebreak_for_all_zero_scores ghi rõ trường hợp này.
- Ngữ cảnh chứa tướng có tên nhưng chưa học được đóng góp 0 và vẫn lọc ứng viên.

## Phạm vi chất lượng

| Thành phần | Tập/giao thức | Hit@5 | NDCG@5 |
|---|---|---:|---:|
| Pick cosine | Validation P2: 280 mask, 28 ván, 7 series | 0.339286 | 0.246162 |
| Ban popularity | Validation B1: 224 mask, 28 ván, 7 series | 0.459821 | 0.315016 |

P2 dùng 4 đồng đội và 5 đối thủ cuối trận, không bans. B1 dùng các ban còn lại của
cả hai đội, không picks. Đây là khôi phục tập/đội hình; không phải mô phỏng đúng
thứ tự draft. Chất lượng ở ngữ cảnh ít tướng hơn hoặc ngữ cảnh live khác chưa đo.
Không so hai hàng chỉ số với nhau để nói ban tốt hơn pick.
Pick được chọn trên chính validation này trong 8 cấu hình: score chọn không phải
ước lượng trên test độc lập. Sáu cấu hình combined không cải thiện NDCG@5; giữ
code/thống kê đối thủ cho truy vết nhưng wrapper không bật combined.

Gói dùng artifact từ lần chạy tham chiếu có chỉ số khớp output người dùng gửi.
Đã đối chiếu wrapper với 280 dự đoán pick và 224 dự đoán ban đã lưu: thứ hạng
khớp toàn bộ. Đây là kiểm tra đóng gói, không phải đánh giá chất lượng mới.
Model fit chỉ train. metadata evaluated=false trong model là trạng thái lúc fit;
file báo cáo/selected_config lưu đánh giá riêng theo hash, không sửa model.
Test V1 theo P1 trước đây không phải kết quả test cho gói V2 này.

## Kiểm tra toàn vẹn

liqi_draft/release_manifest.json ghi SHA256 code, model và selected_config.
Khởi tạo kiểm tra các hash, cấu hình chọn khớp model và code suy luận.
Hash phát hiện thay đổi file vô ý, không phải chữ ký bảo mật.
Không chỉnh file hoặc bỏ kiểm tra hash để ép chạy nếu báo mismatch; giải nén lại
gói gốc, hoặc đóng gói và kiểm chứng phiên bản mới sau khi sửa có chủ đích.
Giữ nguyên byte file Python khi di chuyển để tránh thay đổi CRLF/LF gây mismatch.

## Những gì An cần xử lý ở ứng dụng

Chỉ gửi thông tin đã biết tại lượt thực tế. Tầng luật của ứng dụng phải xác định
lượt hợp lệ, patch, vai trò, luật giải/global ban và tướng bị khóa trước khi gọi
model; có thể đưa tướng bị khóa vào banned để lọc nhưng phải quản lý nguồn trạng
thái ở ứng dụng. Gói không kiểm tra các luật này và không tự chuyển lượt.
Không gắn nhãn 'khắc chế tốt nhất' hoặc 'tối ưu tỷ lệ thắng' cho kết quả.

## Tiến độ bàn giao

Bước 9: gói thư viện và tài liệu tích hợp hoàn tất, có model, cấu hình, ví dụ,
báo cáo và kiểm thử. Chưa gửi cho An hoặc triển khai web tự động.
Bước 10: còn đánh giá độc lập V2 trên holdout mới và hoàn thiện báo cáo cuối.
Cần dữ liệu chưa dùng phát triển, tách theo series; muốn đánh giá draft theo lượt
cần thứ tự/phase được xác minh. Không tái dùng test V1 để tối ưu V2.
Ba ván train có ban chưa đủ 8 vẫn giữ nguyên dữ liệu quan sát và cảnh báo nguồn.
