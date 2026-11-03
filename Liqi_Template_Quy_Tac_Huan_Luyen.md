# LIQI — TEMPLATE VÀ QUY TẮC HUẤN LUYỆN HỆ THỐNG CẤM/CHỌN TƯỚNG

Phiên bản tài liệu: 1.0 — 31/10/2026  
Phụ trách mô hình: Nguyễn Đức Trọng  
Phụ trách tích hợp web: An  
Công nghệ: Python; không Hadoop/Spark.  
Trạng thái: kế hoạch trước triển khai; chưa có kết quả huấn luyện trong tài liệu này.

> Mục tiêu là tìm phương án tốt nhất trong các phương án đã thử, theo một giao thức đánh giá cố định và có thể kiểm chứng. Không có quy tắc nào bảo đảm mô hình tối ưu tuyệt đối hoặc làm tăng tỉ lệ thắng ngoài thực tế.

## 1. Chốt bài toán trước khi viết code

### 1.1 Mẫu mô tả đề tài

**Tên phần việc:** Xây dựng và đánh giá mô hình hỗ trợ cấm/chọn tướng Liqi.

**Mục tiêu:** Nhận trạng thái đội hình, xác định tướng còn hợp lệ và xếp hạng Top-K ứng viên. Bản đầu đánh giá khả năng khôi phục tướng bị che trong đội hình lịch sử; các chức năng counter-pick và ban cần được đánh giá riêng theo dữ liệu có sẵn.

**Đầu vào dự kiến:** tướng đội mình đã chọn, tướng đối thủ đã lộ, tướng đã cấm, loại hành động cần gợi ý (pick/ban), K; thêm phiên bản, luật giải, giai đoạn draft và lịch sử ván trước khi có dữ liệu xác minh.

**Đầu ra:** danh sách ứng viên có thứ hạng, ID, tên, điểm, nguồn điểm, lý do và thông tin giới hạn. Điểm xếp hạng không mặc định là xác suất thắng.

**Phạm vi Trọng:** dữ liệu đầu vào mô hình, huấn luyện, đánh giá, hàm suy luận dùng lại và gói bàn giao. An xây dựng API, web và triển khai.

### 1.2 Ba mục tiêu cần tách riêng

| Mục tiêu | Bằng chứng cần có | Phạm vi bộ hiện tại |
|---|---|---|
| Gợi ý pick phối hợp | Tập tướng xuất hiện cùng đội hình | Có thể bắt đầu bằng popularity và item-item |
| Gợi ý counter-pick | Điểm thực sự phụ thuộc đối thủ; kiểm chứng giá trị tăng thêm | Có đội hình hai bên, nhưng chưa có thứ tự draft; chỉ nghiên cứu quan hệ đối đầu hoặc khôi phục có điều kiện |
| Gợi ý ban | Ngữ cảnh hợp lệ trước ban, nhãn ban hoặc giao thức đánh giá cụ thể | Có danh sách ban theo đội/ván; chưa biết thứ tự và trạng thái lúc ban |

Không dùng kết quả của nhiệm vụ pick để kết luận nhiệm vụ ban/counter đã hiệu quả. Nếu mới hoàn thành pick, ghi rõ trạng thái các chức năng còn lại khi bàn giao.

## 2. Cơ sở dữ liệu đã chốt

Snapshot: `035ce761e53a47dbfd18ca1d9fabe7ceb0ec79115271bccac303bed2a6c0195c`.

| Tập | Loạt trận | Ván | Đội hình |
|---|---:|---:|---:|
| Train | 60 | 231 | 462 |
| Validation | 7 | 28 | 56 |
| Test | 8 | 40 | 80 |

- Dữ liệu thuộc một giải; không xem là đại diện cho mọi mùa, mọi phiên bản hoặc người chơi xếp hạng.
- Thời gian chia tập dựa trên lịch series. Thời gian thi đấu thực tế chưa xác minh.
- Không có thứ tự draft đã xác minh. `source_slot`, h1–h5 và thứ tự dòng không phải thứ tự pick hay vai trò.
- Có tướng chưa xuất hiện trong train ở validation/test; test còn có patch mới so với train.
- `training_ready` trong manifest chỉ có phạm vi `post_draft_baseline_schedule_proxy`.
- `feature_schema.json` hiện là schema dự đoán thắng/thua sau draft của nhóm; phần recommender phải có mô tả đầu vào riêng.

### File sử dụng

| File làm việc | Vai trò |
|---|---|
| association_train.csv | Fit popularity và đồng xuất hiện; không cộng thêm train.csv như mẫu mới |
| train.csv | Đội hình hai bên và kết quả nếu nghiên cứu đặc trưng đối đầu |
| validation.csv | So sánh cấu hình và chọn phương án |
| test.csv | Đánh giá cuối sau khi khóa lựa chọn |
| heroes.csv | Ánh xạ tên/ID; không dùng việc có tên trong danh mục để giả định đã có lịch sử học |
| draft_actions.csv | Phân tích pick/ban; chỉ phần train được dùng tính thống kê học |
| split_assignments.csv, split_manifest.json | Cố định membership và mốc chia tập |
| manifest.json | Xác định snapshot và tính toàn vẹn |

Các file gốc có hậu tố (1), (2), (3) phải được đối chiếu manifest trước khi đổi tên. Không gộp nhiều snapshot của cùng 299 ván.

## 3. Những quy tắc bắt buộc

1. **Chốt nhiệm vụ, dữ liệu, tập ứng viên và chỉ số trước thực nghiệm.** Mọi thay đổi giao thức tạo phiên bản mới, ghi rõ lý do.
2. **Fit từ train.** Thống kê phổ biến, đồng xuất hiện, chuẩn hóa, encoding và trọng số học đều chỉ dựa trên train. Không dùng thống kê toàn giải chứa holdout.
3. **Không chia ngẫu nhiên các đội hình/ca che tướng của cùng ván sang nhiều tập.** Giữ split theo series đã có.
4. **Giữ nguyên test cho đánh giá cuối.** Không chọn seed, tham số, trọng số hoặc phương pháp theo test. Xem test nhiều lần để cải tiến khiến test trở thành dữ liệu phát triển.
5. **Thông tin đầu vào phải khớp thời điểm sử dụng.** Không đưa đội thắng, thời lượng, vàng cuối trận hoặc lựa chọn tương lai vào ngữ cảnh draft.
6. **Định nghĩa tính hợp lệ trước khi đo.** ID hợp lệ, không trùng pick/ban, giới hạn số tướng và quy tắc giải phải được kiểm soát đúng phần đã xác minh.
7. **Không âm thầm bỏ trường hợp khó.** Báo cáo target chưa thấy trong train, không có ứng viên, mô hình không trả đủ K và dữ liệu thiếu.
8. **So sánh công bằng.** Cùng tập trường hợp, ứng viên, bộ lọc, K và công thức metric cho các mô hình.
9. **Tách điểm mô hình và điểm dự phòng.** Ghi source để biết gợi ý nào do item-item, gợi ý nào do popularity; đánh giá toàn bộ pipeline thực sự bàn giao.
10. **Mỗi thử nghiệm thay đổi một yếu tố chính.** Ghi cấu hình và lý do trước khi chạy; tránh thử hàng trăm cấu hình trên 28 ván validation.
11. **Tái lập được.** Cố định thứ tự phá hòa, seed nếu có ngẫu nhiên, phiên bản dữ liệu/code và môi trường.
12. **Chấp nhận kết quả không cải thiện.** Nếu mô hình phức tạp không hơn baseline, chọn baseline hoặc tiếp tục nghiên cứu có ghi nhận; không sửa dữ liệu đánh giá để nâng điểm.

## 4. Chuẩn bị và kiểm tra dữ liệu

### Checklist trước huấn luyện

- [ ] Snapshot khớp manifest; không trộn phiên bản.
- [ ] Mỗi đội hình có đúng 5 ID khác nhau và đều tra được danh mục.
- [ ] Không trùng khóa (game_id, team_id).
- [ ] Mỗi ván có hai đội hình và đối chiếu đúng đội A/B.
- [ ] Không giao nhau game_id hoặc series_id giữa các tập.
- [ ] Nhãn split giữa các bảng khớp nhau.
- [ ] Danh sách JSON được giải mã đúng; boolean đọc tường minh, không dùng bool('false').
- [ ] Có thống kê tần suất tướng và mức độ thưa từ train.
- [ ] Có số target ngoài danh mục train ở holdout, nhưng không học lại từ chúng.
- [ ] Lưu data_quality_report.json; lỗi được sửa có truy vết, không tự xóa cho đủ điều kiện.

## 5. Thiết kế mô hình theo từng mức

### M0 — Popularity baseline

`pop(h)` là số đội hình train chứa h. Lọc ứng viên rồi xếp theo pop giảm dần. Phá hòa bằng ID tăng dần. Baseline này là mốc đối chiếu bắt buộc cho pick.

### M1 — Item-item đồng xuất hiện

Với X[t,i] = 1 nếu đội hình t chứa i:

`C(i,j) = tổng_t X[t,i] * X[t,j]`, với i khác j; đặt đường chéo bằng 0.

Điểm ứng viên h với tập đồng đội S:

`score(h | S) = tổng_{i thuộc S} C(i,h)`.

Bản đầu dùng cả đội hình thắng và thua. Tướng được chọn là một tương tác quan sát; không coi chiến thắng là bằng chứng riêng về hiệu quả của từng cặp. Không cần giữ tối đa 50 láng giềng như Automotive vì danh mục hiện nhỏ.

### M2 — Item-item cosine

Thử chuẩn hóa để hạn chế ảnh hưởng của tướng phổ biến:

`sim(i,j) = C(i,j) / sqrt(pop(i) * pop(j))`.

Đặt sim = 0 nếu mẫu số bằng 0; score vẫn là tổng sim với đồng đội. Cosine chỉ là ứng viên cần kiểm chứng, không bảo đảm tốt hơn số đếm.

### M3 — Giảm ảnh hưởng cặp ít dữ liệu (tùy chọn)

`sim_shrunk(i,j) = sim(i,j) * C(i,j) / (C(i,j) + lambda)`.

Đề xuất trước thực nghiệm chỉ thử lambda trong {2, 5, 10}, sau M2. Không vừa thêm trọng số theo patch, nhãn thắng, luật kết hợp và giảm nhiễu trong cùng một thử nghiệm.

### Chính sách dự phòng chung

- Không có own_picks: popularity.
- Không đủ ứng viên có điểm dương: bổ sung popularity sau các ứng viên đã xếp.
- Không lặp lại hoặc đề xuất tướng bị loại; không cố tạo đủ K nếu thiếu ứng viên hợp lệ.
- Tướng đầu vào chưa thấy trong train nhưng có trong danh mục: nhận diện, loại khỏi ứng viên nếu đã chọn/cấm; không giả lập quan hệ chưa học. Báo context chưa có lịch sử khi cần.
- ID không thuộc danh mục: trả lỗi rõ ràng; không bỏ qua âm thầm.

### Mở rộng counter-pick

Điểm phải sử dụng đối thủ E, ví dụ về cấu trúc `score(h|S,E) = score_ally(h|S) + alpha * score_opponent(h|E)`; đây chưa phải công thức đã được chứng minh hiệu quả.

Chỉ học score_opponent từ train, nêu rõ là quan hệ đối đầu trong toàn đội hình, không mặc định là cùng đường hay khắc chế nhân quả. Nếu dùng kết quả thắng/thua để học quan hệ, cần giảm ảnh hưởng mẫu ít và ghi nhận nhiễu do đội/tuyển thủ, patch và các tướng còn lại.

So sánh có/không thành phần đối thủ trên cùng giao thức. Dùng đội hình đối thủ hoàn chỉnh trong đánh giá che tướng phải gắn nhãn post-draft; không diễn giải thành hiệu quả tại lượt draft sớm. Không lấy mô hình dự đoán đội hình đủ 10 tướng để chấm trực tiếp đội hình thiếu nếu chưa thiết kế và kiểm tra cách biểu diễn.

### Mở rộng gợi ý ban

Baseline ban: đếm tần suất ban trong phần train của draft_actions; lọc tướng không hợp lệ. Không coi tướng được ban là tướng chắc chắn mạnh nhất hoặc nên ban trong mọi tình huống.

Nếu chưa có thứ tự, có thể thiết kế một giao thức riêng khôi phục một ban bị che từ tập ban còn lại, ghi rõ thông tin nào được cung cấp và rằng đây là bài toán khôi phục tập ban. Không dùng toàn bộ pick cuối cùng rồi gọi đó là ngữ cảnh trước ban. Giao thức này chỉ đo khớp lựa chọn lịch sử, không đo mức tăng xác suất thắng do ban.

Đánh giá ban theo lượt thật cần dữ liệu thứ tự, giai đoạn, lượt của đội nào và luật hợp lệ. Chưa có các dữ liệu này thì bàn giao chức năng ban với nhãn baseline/thử nghiệm, không báo đã tối ưu theo ngữ cảnh.

## 6. Giao thức đánh giá pick đã đề xuất

### P1 — Leave-one-hero-out, chỉ dùng đồng đội

- Mỗi đội hình giữ lại 4 tướng và che 1; lần lượt che đủ 5.
- Ngữ cảnh chỉ gồm 4 tướng đồng đội. Không sử dụng đối thủ hoặc ban trong giao thức P1.
- Ứng viên: các tướng xuất hiện trong train, trừ 4 tướng đầu vào.
- Đáp án: tướng bị che, kể cả khi chưa xuất hiện trong train.
- Validation có 56 đội hình, tạo 280 trường hợp; test có 80 đội hình, tạo 400 trường hợp khi đến giai đoạn đánh giá cuối.
- Trường hợp target ngoài danh mục được tính miss trong chỉ số tổng thể; báo thêm tỉ lệ target có thể đề xuất. Có thể thêm chỉ số trên target đã thấy nhưng không thay thế chỉ số tổng thể.
- K chính: 5; K phụ: 10, phải áp dụng nhất quán và không chọn K sau khi xem test.
- Giao thức này đo bổ sung tướng thứ năm, không chứng minh chất lượng khi chỉ có 1–2 đồng đội. Có thể bổ sung giao thức ngữ cảnh nhỏ, cố định cách lấy mẫu và seed, báo riêng kết quả theo độ dài ngữ cảnh.

### Chỉ số

| Chỉ số | Công thức/ý nghĩa | Vai trò |
|---|---|---|
| Hit Rate@K | Trung bình I(target nằm trong Top-K) | Khả năng khôi phục |
| NDCG@K | Với một target: 1/log2(rank+1) nếu rank <= K; ngoài Top-K bằng 0 | Chỉ số chọn mô hình chính |
| Recall@K | Bằng Hit Rate@K khi chỉ có một target | Không coi là bằng chứng độc lập |
| Coverage | Số tướng khác nhau được đề xuất / số tướng trong danh mục train | Độ đa dạng toàn hệ thống |
| Target coverage | Tỉ lệ trường hợp có target nằm trong danh mục train | Giới hạn học từ dữ liệu |
| Fallback rate | Báo riêng % yêu cầu và % vị trí cần popularity bổ sung | Mức phụ thuộc dự phòng |
| Full-K rate | Tỉ lệ yêu cầu nhận đủ K | Tính đầy đủ |
| Invalid recommendation rate | Tỉ lệ gợi ý vi phạm bộ lọc đã định nghĩa | Phải bằng 0 cho các quy tắc đã triển khai |

Tính trung bình theo trường hợp trên tập cố định; không đổi cách lấy trung bình giữa mô hình. Báo kèm số ván/series gốc. Nếu tính khoảng tin cậy, bootstrap theo series và giữ toàn bộ ca thuộc series cùng nhau, không bootstrap 280 ca như các mẫu độc lập. Chỉ có 7 series validation nên khoảng tin cậy có thể rất không ổn định.

### P2 — Ngữ cảnh có đối thủ/ban (chỉ khi mở rộng)

Định nghĩa lại rõ trường đầu vào, bộ lọc và mục tiêu. Chạy cả baseline và mô hình mở rộng trên P2. Không so điểm M1 trên P1 với M2 trên P2 để kết luận thuật toán tốt hơn: bộ lọc và lượng thông tin khác nhau có thể làm bài toán dễ hơn.

## 7. Tiêu chí chọn mô hình và điều kiện dừng

1. Qua kiểm tra tính đúng: không rò rỉ dữ liệu, không vi phạm lọc ứng viên, không sai công thức metric.
2. Chọn NDCG@5 validation cao nhất trong tập thử nghiệm đã định trước.
3. Nếu NDCG@5 bằng nhau, đối chiếu Hit Rate@5; nếu tiếp tục bằng nhau, chọn mô hình đơn giản hơn.
4. Nếu tăng NDCG nhưng giảm Hit Rate/coverage hoặc tăng fallback mạnh, ghi nhận đánh đổi, không chỉ trích chỉ số tốt nhất.
5. Nếu mức tăng nhỏ hoặc dao động theo series, mô tả là chưa đủ bằng chứng cải thiện ổn định; không kết luận chắc chắn từ một số trung bình.
6. Khi đã hoàn thành ngân sách thử nghiệm và chọn cấu hình, khóa model/config/protocol rồi đánh giá test.
7. Test kém không cho phép quay lại chọn phương án theo test. Muốn phát triển vòng mới phải ghi rõ test đã bị sử dụng và cần holdout mới để xác nhận độc lập.

Ngân sách ban đầu: M0, M1, M2; thêm tối đa 3 cấu hình M3 nếu cần. Hoàn thiện pick rồi thiết kế thử nghiệm counter/ban riêng. Không có ngưỡng NDCG phổ quát để bảo đảm chất lượng; tiêu chí phải dựa trên baseline, dữ liệu và mục tiêu thực tế.

Bản đầu giữ fit=train cho cả validation và test. Nếu về sau refit train+validation, phải quyết định trước test và lưu model_version mới; không so lẫn mô hình fit khác nhau mà không ghi rõ.

## 8. Template ghi nhận từng thí nghiệm

Sao chép phần này cho mỗi lần chạy.

### Experiment ID: [điền]

| Trường | Nội dung cần điền |
|---|---|
| Ngày, người thực hiện | [...] |
| Giả thuyết | Thay đổi nào được kỳ vọng cải thiện điều gì? |
| Dataset version | [...] |
| Code version/hash | [...] |
| Tập fit | Train; tên file + hash |
| Nhiệm vụ | Pick phối hợp / counter / ban |
| Giao thức | P1 hoặc giao thức mới có mô tả |
| Phương pháp, tham số | [...] |
| Candidate policy | [...] |
| Bộ lọc, fallback, phá hòa | [...] |
| K và seed | [...] |
| Khác biệt so với đối chứng | Một yếu tố chính |
| Tiêu chí chọn | NDCG@5, tiêu chí phụ đã chốt |
| Trạng thái | Chưa chạy / lỗi / hoàn tất |

| Mô hình | NDCG@5 | Hit Rate@5 | NDCG@10 | Coverage | Fallback request % | Số ca |
|---|---:|---:|---:|---:|---:|---:|
| Baseline | Chưa chạy | Chưa chạy | Chưa chạy | Chưa chạy | Chưa chạy | Chưa chạy |
| Ứng viên | Chưa chạy | Chưa chạy | Chưa chạy | Chưa chạy | Chưa chạy | Chưa chạy |

**Nhận xét:** [...]  
**Lỗi/giới hạn:** [...]  
**Quyết định:** giữ / loại / cần kiểm tra; lý do [...]  
**Đường dẫn cấu hình, metrics, dự đoán:** [...]

Không điền 0 thay cho kết quả chưa chạy. Không chọn một ví dụ trúng để đại diện cho chất lượng cả mô hình.

## 9. Template phân tích lỗi

| Nhóm lỗi | Câu hỏi kiểm tra | Hướng xử lý hợp lệ |
|---|---|---|
| Tướng phổ biến chiếm đầu bảng | Raw count có bị popularity chi phối? | Thử cosine, giữ cùng giao thức |
| Cặp hiếm có điểm cao | Quan hệ dựa trên quá ít đội hình? | Shrinkage hoặc ngưỡng hỗ trợ định trước |
| Target mới | Tướng không có lịch sử train? | Báo target coverage; nghiên cứu nội dung khi có dữ liệu |
| Không có quan hệ | Ngữ cảnh mới hoặc quá thưa? | Fallback rõ ràng; theo dõi tỉ lệ |
| Thiếu vai trò | Có bảng role tướng đã xác minh chưa? | Bổ sung dữ liệu vai trò; không suy từ source_slot |
| Khác patch | Quan hệ thay đổi theo giai đoạn? | Phân tích theo patch; thử trọng số thời gian trong vòng phát triển có kiểm soát |
| Ban/counter không tốt | Mục tiêu học có thực sự dùng thông tin tương ứng? | Định nghĩa nhiệm vụ và giao thức riêng |

## 10. Quy tắc bàn giao cho An

Hàm đề xuất: `load_model(path)` và `recommend(model, own_picks, enemy_picks, banned, k=5)`; nếu thêm mode ban thì quy định rõ mode/model riêng. Hàm chạy độc lập với notebook, không phụ thuộc dữ liệu train trên máy phục vụ.

### Đầu ra cần có

- model.json: tham số đã học, danh mục ứng viên, quan hệ và popularity.
- model_metadata.json: snapshot, tập fit, model version, cấu hình, ngày tạo, metric, giới hạn.
- recommender.py: nạp mô hình, kiểm tra đầu vào, lọc, chấm điểm và xếp hạng.
- requirements.txt: dependency và phiên bản thực tế đã kiểm tra.
- example_usage.py: ví dụ ID có thật, kết quả tái lập được.
- validation_metrics.json và test_metrics.json: kết quả đã chạy, không tạo số giả.
- README_handoff.md: cách gọi, cấu trúc phản hồi, lỗi đầu vào, fallback và các chức năng chưa hỗ trợ.

### Checklist nghiệm thu

- [ ] Đã chọn mô hình theo validation; test không tham gia lựa chọn.
- [ ] Mô hình lưu/nạp lại trả đúng cùng thứ tự và điểm.
- [ ] Không đề xuất tướng đã pick/ban; không trùng kết quả.
- [ ] Kiểm tra danh sách mâu thuẫn, ID sai, own_picks đã đủ 5 và k không hợp lệ.
- [ ] Khi ít hơn K ứng viên, trả số thực tế cùng thông tin rõ ràng.
- [ ] Ghi rõ cách xử lý tướng chưa thấy trong train.
- [ ] Bộ lọc luật giải/patch được xác minh đến đâu, ghi đến đó.
- [ ] Kết quả chạy độc lập notebook; không cần đọc train.csv khi gợi ý.
- [ ] An biết điểm không phải xác suất thắng và hệ thống chưa chứng minh tối ưu draft.
- [ ] Trạng thái pick/counter/ban được ghi riêng: hoàn tất / baseline / chưa hỗ trợ.

## 11. Mẫu cấu hình khởi đầu

```json
{
  "experiment_id": "pick_p1_v1",
  "task": "lineup_completion",
  "fit_split": "train",
  "evaluation_split": "validation",
  "protocol": "leave_one_hero_out_ally_only",
  "candidate_policy": "train_seen_heroes",
  "include_unseen_targets_in_overall_metrics": true,
  "methods": ["popularity", "item_item_count", "item_item_cosine"],
  "primary_k": 5,
  "secondary_k": 10,
  "selection_metric": "ndcg_at_5",
  "fallback": "train_popularity",
  "random_seed": 42,
  "refit_train_validation": false,
  "test_evaluation_enabled": false
}
```

Đây là cấu hình thiết kế; cần nối với code thực tế, không mặc định file cấu hình tự ngăn rò rỉ dữ liệu.

## 12. Mẫu kết luận báo cáo

“Trên tập validation gồm [số] ván thuộc [số] loạt trận, phương pháp [tên] đạt NDCG@5 là [giá trị], so với [giá trị] của baseline. Các phương pháp dùng cùng giao thức [tên], tập ứng viên và bộ lọc. Sau khi cố định cấu hình, kết quả trên test là [giá trị]. Phép đánh giá đo khả năng khôi phục tướng bị che trong đội hình lịch sử. Do chưa có thứ tự draft được xác minh, kết quả chưa chứng minh lựa chọn tối ưu ở từng lượt cấm/chọn hoặc mức tăng tỉ lệ thắng khi triển khai.”

## 13. Thứ tự thực hiện

1. Chốt P1, snapshot, candidate policy, K và ngân sách thử nghiệm.
2. Viết data_loader và data_validation; lưu báo cáo.
3. Huấn luyện M0 và M1; viết hàm suy luận dùng chung.
4. Đánh giá validation; phân tích lỗi và thử M2/M3 trong ngân sách.
5. Khóa phương án; đánh giá test cuối.
6. Đóng gói bàn giao cho An.
7. Thiết kế vòng nghiên cứu riêng cho counter-pick và ban khi có đủ dữ liệu/giao thức phù hợp.

Nguồn nội bộ: README.md, split_manifest.json, feature_schema.json và manifest của snapshot 035ce761… đã cung cấp; báo cáo Automotive được dùng làm nền tảng quy trình baseline → item-item → validation → test → bàn giao. Các mô hình mở rộng và tiêu chí trong tài liệu là đề xuất trước thực nghiệm, không phải kết quả đã xác nhận.
