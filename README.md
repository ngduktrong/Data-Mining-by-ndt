# Liqi — Hệ thống gợi ý cấm/chọn tướng

Dự án môn **Khai phá dữ liệu**, xây dựng hệ thống trả về Top-K tướng dựa trên
các tướng đã chọn của đội mình, đối thủ và danh sách đã cấm.

**Phạm vi của Trọng:** xử lý dữ liệu, huấn luyện, đánh giá và đóng gói mô hình.
> Phiên bản hiện tại là baseline phục vụ học tập: pick dùng item-item cosine,
> ban dùng tần suất ban. Chưa chứng minh khả năng tối ưu chiến thuật hoặc tăng tỷ lệ thắng.
## 1. Chức năng

| Chức năng | Nội dung hiện có |
|---|---|
| Gợi ý pick | Xếp hạng theo cosine với các tướng đồng đội |
| Gợi ý ban | Xếp hạng theo tần suất ban trong tập train |
| Lọc ứng viên | Loại tướng đã chọn của hai đội và tướng đã cấm |
| Giải thích | Trả điểm, số lần xuất hiện và bằng chứng tương đồng |
| Thử nghiệm đối thủ | Đã thử cộng thống kê kết quả đối đầu có làm trơn; chưa cải thiện NDCG@5 trong các cấu hình đã thử |
| Web demo | Nhập đội hình, chọn Top-5/10, xem bằng chứng, tải JSON |

Đối thủ trong **cấu hình bàn giao** chỉ dùng để lọc ứng viên, không cộng điểm khắc chế.
Collaborative Filtering dạng item-item đã triển khai; Graph Neural Networks chưa triển khai.
Phần dự đoán kết quả trận và khai phá luật kết hợp của các thành viên khác không nằm trong gói này.

## 2. Yêu cầu môi trường

- Python **3.10 trở lên**.
- Windows CMD/PowerShell hoặc terminal tương đương.
- Trình duyệt để mở web demo.
- Các gói hiện tại dùng thư viện chuẩn Python, không cần `pip install`.

Kiểm tra Python:

```bat
python --version
```

Nếu máy chỉ nhận lệnh `py`, thay `python` bằng `py` trong các lệnh bên dưới.

## 3. Cấu trúc và vị trí chạy

README này dùng cho thư mục cha `liqi_recommender`. Các script bước 3–8 hiện vẫn
nằm trực tiếp trong `liqi_recommender_v1`; chưa di chuyển sang cấu trúc gom thư mục mới.

| Đường dẫn tương đối | Nội dung |
|---|---|
| `liqi_recommender_v1/` | Mã huấn luyện, kiểm tra và đánh giá |
| `liqi_recommender_v1/run.py` | Các lệnh V1: check, develop, demo, final-test |
| `liqi_recommender_v1/src/` | Mã lõi V1 |
| `liqi_recommender_v1/tests/` | Kiểm thử lõi V1 |
| `liqi_recommender_v1/data/raw/` | Dữ liệu chia tập, danh mục tướng, manifest |
| `liqi_recommender_v1/configs/` | Cấu hình V1 |
| `liqi_recommender_v1/artifacts/` | Mô hình và thông tin phiên bản |
| `liqi_recommender_v1/reports/` | Báo cáo kiểm tra và đánh giá |
| `liqi_recommender_v1/docs/` | Tài liệu huấn luyện |
| `liqi_recommender_v1/handoff/` | Gói bàn giao V1 do pipeline tạo |
| `Liqi_Buoc_09_Handoff/` hoặc `Liqi_Handoff/` | Gói pick/ban độc lập, chứa `demo.py` và `liqi_draft/` |
| `Liqi_Web_Demo/` | Gói web độc lập, chứa `app.py` và `static/` |

Tên thư mục bàn giao có thể đã được đổi trên máy bạn. Luôn chọn **thư mục chứa
đúng file cần chạy**: `run.py` cho huấn luyện, `demo.py` cho bàn giao, `app.py` cho web.
Các thư mục scaffold/crawler cũ ở thư mục cha không phải nơi chạy các lệnh dưới đây.

## 4. Chạy nhanh web demo

Gói `Liqi_Web_Demo.zip` đã chứa mô hình; không cần huấn luyện lại hoặc chép CSV từ V1.

1. Giải nén ZIP vào thư mục riêng.
2. Mở thư mục có `app.py`.
3. Nhấp đôi `START_WINDOWS.bat`, hoặc mở terminal tại đó và chạy:

```bat
python app.py
```

4. Giữ terminal mở, truy cập **http://127.0.0.1:8000**.
5. Bấm **Nạp ví dụ → Xem gợi ý**, hoặc tự chọn tướng.
6. Nhấn `Ctrl+C` trong terminal để dừng server.

Nếu cổng 8000 đang được dùng:

```bat
python app.py --port 8001
```

Sau đó mở http://127.0.0.1:8001. Không mở `static/index.html` trực tiếp bằng `file://`.
Web chỉ lắng nghe trên máy đang chạy, không phải bản triển khai public.

Kiểm thử web, chạy tại thư mục có `app.py`:

```bat
python -m unittest test_web -v
```

## 5. Dữ liệu sử dụng

Nguồn dữ liệu đã dùng trong snapshot huấn luyện là dữ liệu giải đấu được crawler
và chuẩn hóa từ Liquipedia. Garena/AOV Tracker và các nguồn giải khác thuộc định
hướng thu thập; không mặc định mọi nguồn đó đã được dùng trong model hiện tại.

| Tập | Số ván | Số series |
|---|---:|---:|
| Train | 231 | 60 |
| Validation | 28 | 7 |
| Test V1 | 40 | 8 |
| Tổng | 299 | 75 |

- Train có 462 đội hình, 83 tướng xuất hiện trong pick.
- Danh mục ánh xạ có 86 tên/ID; không phải toàn bộ tướng của trò chơi.
- Train có 1.845 ban quan sát được, thuộc 63 tướng.
- Ba ván train chỉ ghi nhận 7 ban: giữ dữ liệu quan sát, không tự thêm ban; chưa chốt nguyên nhân từ nguồn.
- Thứ tự và giai đoạn draft chưa được xác minh.
- Thời gian chia tập dựa vào lịch series, không phải thời điểm thực tế từng lượt.

Snapshot:

```text
035ce761e53a47dbfd18ca1d9fabe7ceb0ec79115271bccac303bed2a6c0195c
```

Các file chính trong `data/raw/`: `train.csv`, `validation.csv`, `test.csv`,
`heroes.csv`, `draft_actions.csv`, `association_train.csv`, `split_assignments.csv`,
`manifest.json` và `split_manifest.json`.
Không sửa dữ liệu hoặc bỏ kiểm tra hash để ép chạy khi snapshot không khớp.

## 6. Quy trình huấn luyện và đánh giá

### 6.1. Mở đúng thư mục

Ví dụ đường dẫn trên máy Trọng, dùng trong CMD:

```bat
cd /d "D:\Python của trọng\Khai Pha\liqi_recommender\liqi_recommender_v1"
dir run.py
```

Nếu dùng PowerShell, chuyển thư mục bằng:

```powershell
Set-Location "D:\Python của trọng\Khai Pha\liqi_recommender\liqi_recommender_v1"
```

Tất cả lệnh trong mục 6 chạy tại thư mục này. Các script bổ sung phải được chép
vào đây từ các gói bước 3–8. **Đối với bản đã hoàn tất của bạn, không cần chạy
lại train/develop để sử dụng web hoặc gói bàn giao.**

### 6.2. V1 — Pick dựa trên đồng đội

Quy trình trên một bản thực nghiệm mới, trước khi dùng test:

```bat
python run.py check
python -m unittest discover -s tests -v
python run.py develop
python run.py demo
```

`develop` fit trên train và so sánh popularity, item-item count, item-item cosine
trên validation. Chọn theo giao thức P1: che một tướng, cung cấp 4 đồng đội.

Lệnh đánh giá test sau khi đã chốt mô hình:

```bat
python run.py final-test --confirm-final-test
```

**Trọng đã chạy final-test V1.** Giữ nguyên kết quả và mô hình; không dùng test
để chọn lại cấu hình. Pipeline có cơ chế khóa sau test; không xóa khóa hoặc báo
cáo để chạy lại develop. Test V1 không phải holdout mới cho quá trình phát triển V2.

### 6.3. Baseline ban — Bước 3–5

```bat
python audit_bans.py
python -m unittest test_ban_baseline -v
python ban_baseline.py train
python ban_baseline.py demo
python -m unittest test_evaluate_bans -v
python evaluate_bans.py
```

Model: `artifacts/v2/ban_popularity/model.json`.
Báo cáo: `reports/v2/ban_audit/` và `reports/v2/ban_validation/`.
Lệnh train chạy lại ghi đè model ban tại đường dẫn mặc định.

B1: che một ban, dùng các ban còn lại của cả hai đội để lọc ứng viên, không truyền
pick cuối trận. 28 ván tạo 224 trường hợp. Target chưa có trong danh mục train vẫn
được giữ lại và tính miss. Đây là khôi phục tập ban, không phải dự đoán lượt kế tiếp.

### 6.4. Thử nghiệm đối thủ — Bước 6–8

```bat
python audit_opponents.py
python -m unittest test_opponent_pick -v
python opponent_pick.py train
python opponent_pick.py demo --request example_opponent_request.json
python -m unittest test_evaluate_opponent_pick -v
python evaluate_opponent_pick.py
```

Model: `artifacts/v2/opponent_pick/model.json`.
Báo cáo: `reports/v2/opponent_audit/` và `reports/v2/pick_validation/`.
Lệnh train chạy lại ghi đè model thử nghiệm tại đường dẫn mặc định.

P2: che một pick, cung cấp 4 đồng đội và 5 đối thủ từ đội hình cuối trận, không
truyền bans hoặc kết quả thắng/thua validation vào suy luận. 28 ván tạo 280 mask.
Thông tin đối thủ có thể xuất hiện sau target trong draft thật, nên đây là bài
khôi phục đội hình với ngữ cảnh cuối trận.

So sánh 8 cấu hình: popularity, cosine và 6 combined với weight thuộc
`[0.1, 0.25, 0.5]`, alpha thuộc `[10, 30]`. Chọn NDCG@5, rồi Hit@5, rồi quy tắc
ưu tiên đơn giản khi hòa. Kết quả lưu trong `selected_config.json`.

**Demo mặc định bước 7 dùng combined; gói bàn giao bước 9 dùng cosine đã chọn.**
File cấu hình chọn không tự thay đổi mặc định của `opponent_pick.py`.

## 7. Thuật toán và ý nghĩa điểm

### Pick cosine

Với tướng h và đồng đội a:

```text
cosine(h,a) = số đội hình chứa cả h,a / sqrt(số đội hình chứa h × số đội hình chứa a)
score_pick(h) = trung bình cosine(h,a) trên các đồng đội đã nhập
```

V1 dùng tổng cosine; bản thử nghiệm V2 và bàn giao dùng trung bình. Với cùng số
đồng đội và cùng quy tắc lọc/hòa điểm, tổng và trung bình cho cùng thứ tự, nhưng
khác giá trị score. Chưa xét vai trò hoặc đường đi.

### Ban popularity

```text
score_ban(h) = số ván train quan sát thấy ban h / tổng số ván train
```

Chỉ gợi ý tướng có ban trong train. Điểm là tần suất quan sát, không phải tỷ lệ thắng.

### Thành phần đối thủ đã thử

```text
pair(h,e) = (wins(h,e) − 0.5 × games(h,e)) / (games(h,e) + alpha)
score_combined(h) = mean_ally_cosine(h) + weight × mean_pair_signal(h)
```

`wins` là số ván đội chứa h thắng khi h và e ở hai đội đối lập. Cặp chưa gặp nhận
0. Làm trơn kéo điểm cặp ít mẫu về 0. Kết quả còn phụ thuộc các thành viên khác,
đội tuyển/người chơi, patch và bên bản đồ: không coi đây là quan hệ khắc chế nhân quả.
Thành phần này không được bật trong cấu hình bàn giao hiện tại.

## 8. Kết quả đã ghi nhận

| Mô hình | Tập / giao thức | Hit@5 | NDCG@5 |
|---|---|---:|---:|
| V1 popularity | Validation P1 | 0.139286 | 0.093562 |
| V1 item-item count | Validation P1 | 0.292857 | 0.205040 |
| V1 item-item cosine | Validation P1 | 0.321429 | 0.234796 |
| V1 cosine đã chọn | Test P1 | 0.355000 | 0.244002 |
| Ban popularity | Validation B1 | 0.459821 | 0.315016 |
| Popularity với bộ lọc đối thủ | Validation P2 | 0.171429 | 0.109902 |
| **Cosine được chọn để bàn giao** | **Validation P2** | **0.339286** | **0.246162** |
| Combined tốt nhất theo NDCG@5 (w=0.1, alpha=30) | Validation P2 | 0.335714 | 0.243936 |

- Test P1: 142/400 hits Top-5; chỉ model đã chọn được đánh giá, không có so sánh baseline trên test.
- Ban B1: 103/224 hits Top-5, 138/224 hits Top-10, 2 unseen target cases.
- Cosine P2: 95/280 hits Top-5; 3 unseen target cases.
- Cả 6 combined thấp hơn cosine về NDCG@5 trong lần thử P2 này.
- Không so trực tiếp P1, P2 và B1 để kết luận mô hình nào tốt hơn: target/ngữ cảnh khác nhau.
- Các mask trong cùng ván/series tương quan; không xem chúng là quan sát độc lập.

Hit@K là tỷ lệ target xuất hiện trong Top-K. Với một target đúng, NDCG của một
trường hợp bằng `1/log2(rank+1)` nếu rank ≤ K, còn lại bằng 0; sau đó lấy trung bình.
Catalog coverage là tỷ lệ tướng ứng viên được gợi ý ít nhất một lần.
Các kiểm thử phần mềm đạt không đồng nghĩa chất lượng khuyến nghị đã được chứng minh.

## 9. Gói bàn giao và tích hợp

Mở terminal tại **thư mục có demo.py**, chẳng hạn:

```bat
cd /d "D:\Python của trọng\Khai Pha\liqi_recommender\Liqi_Handoff"
```

Nếu tên vẫn là `Liqi_Buoc_09_Handoff`, thay đúng tên trong lệnh trên.

```bat
python -m unittest test_handoff -v
python demo.py --request examples/pick_request.json
python demo.py --request examples/ban_request.json
python demo.py --heroes
```

Gói chứa code, model, cấu hình chọn, báo cáo và ví dụ. Không cần data/raw.
Thứ hạng qua hàm bàn giao đã được đối chiếu với 280 dự đoán pick và 224 dự đoán ban
validation đã lưu: khớp toàn bộ. Đây là kiểm tra đóng gói, không phải đánh giá mới.

An chép nguyên `liqi_draft/` vào dự án Python và khởi tạo một lần:

```python
from liqi_draft import DraftRecommender

recommender = DraftRecommender()
result = recommender.recommend({
    'action': 'pick',  # hoặc 'ban'
    'own_picks': [],
    'enemy_picks': [],
    'banned': [],
    'k': 5,
})
```

Lấy tên/ID bằng `recommender.heroes()`.

| Trường request | Quy tắc |
|---|---|
| action | Bắt buộc: pick hoặc ban |
| own_picks | Mảng hero_id; pick tối đa 4, ban tối đa 5 |
| enemy_picks | Mảng hero_id; tối đa 5 |
| banned | Mảng hero_id đã cấm/không khả dụng |
| k | Số nguyên 1–100; mặc định 5 |

Không dùng tên tướng thay ID, không truyền ID trùng/xung đột hoặc null thay mảng.
Không đủ ứng viên thì trả ít hơn K; hết ứng viên trả danh sách rỗng.
Client không được chọn lại method/weight/alpha qua hàm bàn giao.

Output có version, action, method, score_type, recommendations, số lượng, bằng
chứng, phạm vi đánh giá và giới hạn. Mỗi gợi ý có rank, hero_id, hero_name, score,
evidence. API/web chính thức cần xử lý lỗi đầu vào và kiểm tra luật draft riêng.

## 10. Lỗi thường gặp

| Hiện tượng | Cách xử lý |
|---|---|
| `can't open file ... demo.py` | Chuyển vào thư mục có demo.py; mở README không làm terminal tự chuyển thư mục |
| `can't open file ... app.py` | Mở thư mục web đã giải nén, không chạy từ thư mục bàn giao |
| `No module named test_...` | Chạy tại đúng thư mục và kiểm tra file test đã được chép vào |
| Không vào được localhost | Giữ server đang chạy; kiểm tra dòng lỗi trong CMD và đúng cổng |
| Cổng 8000 bị chiếm | Chạy `python app.py --port 8001`, mở đúng cổng 8001 |
| Hash/checksum mismatch | Đối chiếu snapshot hoặc giải nén lại bản gốc; không bỏ kiểm tra hash |
| Gợi ý ít hơn K | Kiểm tra số ứng viên còn lại sau khi loại tướng đã chọn/cấm |
| Mọi điểm pick bằng 0 | Ngữ cảnh không tạo được điểm; hệ thống dùng tần suất để xử lý hòa |

Lưu ý: chỉnh code hoặc đổi xuống dòng LF/CRLF trong gói bàn giao có thể làm hash
khác. Việc tái cấu trúc code cần cập nhật quy trình đóng gói và kiểm chứng, không
chỉ kéo file sang thư mục khác.

## 11. Giới hạn và công việc còn lại

- Chưa có đánh giá độc lập V2 trên holdout mới; test V1 đã sử dụng.
- Chưa xác minh thứ tự draft, nên chưa đánh giá dự đoán lượt cấm/chọn thực tế.
- Chưa đánh giá riêng các ngữ cảnh ít đồng đội/đối thủ trên web.
- Chưa kiểm soát vai trò, patch, bên bản đồ, luật giải hoặc global ban.
- Ba ván có ban cần đối chiếu nguồn vẫn còn cảnh báo.
- Cần dữ liệu mới tách series, giữ model/cấu hình cố định để đánh giá độc lập V2.

Web hiện phục vụ chạy thử. Đầu ra là danh sách tham khảo từ dữ liệu lịch sử,
không phải cam kết đội hình tối ưu hay dự đoán xác suất chiến thắng.
