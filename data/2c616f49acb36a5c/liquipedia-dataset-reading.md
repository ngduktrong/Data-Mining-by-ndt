# Hướng dẫn đọc bộ dữ liệu AoG Spring 2026

## 1. Bắt đầu từ đâu?

Bộ dữ liệu hiện tại nằm ở:

```text
raw/liquipedia/datasets/2c616f49acb36a5c/
```

Đây là giải **Arena of Glory 2026 Spring của Arena of Valor (AOV)**,
dù URL nguồn thuộc wiki `honorofkings`. Không trộn ID tướng với Honor of Kings.

Thư mục này gồm:

```text
2c616f49acb36a5c/
├── csv/             # 19 bảng CSV để đọc/phân tích
│   └── manifest.json
├── parsed.json      # Dữ liệu tổng hợp, mapping và provenance
├── tournament.json  # Metadata giải, đội và roster
└── quality.json     # Coverage, trạng thái chuẩn hóa và các blocker
```

**Cách đọc nhanh:** mở `csv/series.csv` để chọn trận, rồi mở `csv/games.csv`
để xem từng ván. Dùng Excel, LibreOffice hoặc Python; chọn UTF-8 và dấu phân cách
phẩy khi import CSV. Import cột ID/tên nguồn dưới dạng text để tránh phần mềm
bảng tính tự đổi giá trị hoặc diễn giải nội dung nguồn thành công thức.

Tên thư mục `2c616f49acb36a5c` là tiền tố hash của version, không phải mã giải.
Version khác có thể xuất hiện khi nguồn, mapping hoặc quy trình chuẩn hóa đổi.
Không mặc định chọn thư mục có tên lớn nhất; kiểm tra `manifest.json` và
`quality.json`. Hướng dẫn này dùng đúng snapshot nêu trên.

## 2. Mỗi file chứa gì?

| File trong `csv/` | Số dòng dữ liệu | Đơn vị và mục đích |
| --- | ---: | --- |
| `tournament.csv` | 1 | Metadata giải: tên, game, ngày bắt đầu/kết thúc, khu vực |
| `teams.csv` | 8 | Danh mục đội với `team_id` chuẩn |
| `heroes.csv` | 86 | Danh mục tướng: ID, tên chuẩn, alias và bằng chứng mapping |
| `players.csv` | 71 | Tham chiếu nguồn tuyển thủ/staff, không chỉ tuyển thủ thi đấu |
| `tournament_rosters.csv` | 72 | Một bản ghi roster/staff theo đội trong giải |
| `series.csv` | 75 | Một cặp đấu: giai đoạn, lịch, Bo, hai đội và điểm số |
| `games.csv` | 299 | Một ván: hai đội, side, picks, winner, thời lượng, patch |
| `draft_actions.csv` | 5.379 | Một pick/ban với slot nguồn; chưa xác minh thứ tự |
| `prediction_candidates.csv` | 299 | Một ván đủ ID đội/tướng và kết quả để làm candidate |
| `association_transactions.csv` | 598 | Một đội/ván; gồm đội thắng và đội thua |
| `hero_statistics.csv` | 243 | Một tướng/phạm vi thống kê, với counts và tỷ lệ đã chuẩn hóa |
| `stage_prizes.csv` | 14 | Một khoản thưởng đội/vòng bảng, số nguyên VND |
| `patch_notes.csv` | 1 | Ghi chú patch từ nguồn |
| `source_tables.csv` | 42.439 | Một ô bảng render từ API, giữ nội dung nguồn |
| `normalized_table_cells.csv` | 42.439 | Một ô bảng với text NFC, số/đơn vị và ID liên quan |
| `placeholders.csv` | 82 | Slot ván rỗng hoặc được đánh dấu skip; không phải ván đã đấu |
| `coverage.csv` | 8 | Coverage parser theo trang nguồn |
| `diagnostics.csv` | 0 | Cấu trúc chưa hỗ trợ hoặc vấn đề parser |
| `needs_review.csv` | 0 | Identity chưa giải quyết trong snapshot này |

`manifest.json` không phải CSV: chứa version, revision nguồn, số dòng và
SHA-256 của từng file. Số dòng trong bảng trên không tính dòng header.

## 3. Phân biệt cặp đấu và ván đấu

- **Series:** một cuộc đối đầu giữa hai đội, ví dụ trận Bo7 chung kết.
- **Game:** một ván trong series, ví dụ ván 1 hoặc ván 2.
- **Draft action:** một tướng được pick/ban trong một game.
- **Transaction:** tập tướng một đội đã pick trong một game, phục vụ mining.

Các khóa nối:

```text
series.csv.series_id ───────────► games.csv.series_id
games.csv.game_id ──────────────► draft_actions.csv.game_id
games.csv.game_id ──────────────► association_transactions.csv.game_id
teams.csv.team_id ──────────────► team_a_id / team_b_id / team_id
heroes.csv.hero_id ─────────────► các cột pick-ID / draft_actions.hero_id
players.csv.player_id ──────────► tournament_rosters.csv.player_id
```

Không nối bằng tên viết tắt nếu đã có ID. Cùng một tướng có thể xuất hiện với
tên gốc `elandorr` hoặc `eland'orr`, nhưng cùng `hero_id` chuẩn.

Các giai đoạn **nằm chung CSV**, không có thư mục riêng từng vòng.
Lọc cột `stage`: `Group Stage 1`, `Group Stage 2`, `Playoffs`.

| Giai đoạn | Series | Ván đã đấu |
| --- | ---: | ---: |
| Group Stage 1 | 56 | 213 |
| Group Stage 2 | 15 | 63 |
| Playoffs | 4 | 23 |

## 4. Ví dụ: xem trận chung kết

Trong `series.csv`, lọc:

```text
round_name = Grand Finals
```

Bản ghi tương ứng:

```text
series_id: liquipedia:honorofkings:32208:AOG26S1POF:R3M1
team_a_name: Team Flash
team_b_name: Saigon Phantom
best_of: 7
scheduled_at: 2026-05-10T10:00:00+00:00
observed_score_a: 4
observed_score_b: 2
```

Lịch trên tương ứng **17:00 ngày 10/05/2026, giờ Việt Nam**.
Team Flash thắng **4–2**, tổng hợp từ các winner của 6 ván đã thu thập.
Các cột `source_score_*` trống vì nguồn không cung cấp điểm số tại field đó;
không nhầm chúng với điểm số tổng hợp `observed_score_*`.

Trong `games.csv` và `draft_actions.csv`, lọc cùng `series_id` để xem chi tiết:

| Ván | Đội thắng | Thời lượng |
| --- | --- | --- |
| 1 | Saigon Phantom | 19:30 |
| 2 | Team Flash | 30:54 |
| 3 | Team Flash | 19:15 |
| 4 | Saigon Phantom | 10:50 |
| 5 | Team Flash | 21:22 |
| 6 | Team Flash | 10:35 |

Trong `games.csv`:

- `winner_team_number=1`: đội A; `=2`: đội B. **Không phải** xanh/đỏ.
- `team_a_side`, `team_b_side`: side của từng đội trong chính ván đó.
- `duration_seconds`: thời lượng tính bằng giây.
- `t1h1`–`t1h5`: năm tên tướng gốc của đội A.
- `t2h1`–`t2h5`: năm tên tướng gốc của đội B.
- Cột tương ứng có hậu tố `_hero_id` và `_hero_name`: ID và tên chuẩn.
- Slot `h1`–`h5` **không chứng minh role, người chơi hoặc thứ tự pick**.

### Đọc bằng Python, không cần cài thư viện thêm

Chạy từ thư mục gốc repository:

```python
import csv
from pathlib import Path

root = Path("raw/liquipedia/datasets/2c616f49acb36a5c/csv")

def read_csv(name):
    with (root / name).open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))

final = next(
    row for row in read_csv("series.csv")
    if row["round_name"] == "Grand Finals"
)
print(final["team_a_name"], "vs", final["team_b_name"])

games = sorted(
    (row for row in read_csv("games.csv")
     if row["series_id"] == final["series_id"]),
    key=lambda row: int(row["game_number"]),
)

for game in games:
    winner = (
        game["team_a_name"] if game["winner_team_number"] == "1"
        else game["team_b_name"]
    )
    minutes, seconds = divmod(int(game["duration_seconds"]), 60)
    picks_a = [game[f"t1h{i}_hero_name"] for i in range(1, 6)]
    picks_b = [game[f"t2h{i}_hero_name"] for i in range(1, 6)]
    print(game["game_number"], winner, f"{minutes}:{seconds:02d}")
    print("  Team Flash:", picks_a)
    print("  Saigon Phantom:", picks_b)

actions = [
    row for row in read_csv("draft_actions.csv")
    if row["series_id"] == final["series_id"]
]
print("Số pick/ban đã lưu:", len(actions))
```

## 5. Quy ước giá trị và các lưu ý quan trọng

### Null, JSON và kiểu dữ liệu

- Ô trống biểu diễn null/chưa biết, không mặc định bằng 0.
- `0` là giá trị thật, ví dụ khoản thưởng `0₫`.
- Boolean được ghi `true`/`false`.
- List/dict nằm trong ô dưới dạng JSON, ví dụ `hero_ids`, `aliases`, `errors`.
  Python có thể dùng `json.loads(row["hero_ids"])` để đọc list.
- `csv.DictReader` trả về chuỗi; tự chuyển số bằng `int`/`Decimal` khi cần.
  Không dùng `bool("false")` vì Python coi chuỗi không rỗng là true.

### Thống kê và tiền thưởng

- Tỷ lệ trong `hero_statistics.csv` dùng ratio: `52.29%` → `0.5229`.
- `page_title` xác định phạm vi thống kê: tổng giải, Group Stage 1, hoặc
  **Group Stage 2 + Playoffs**. Không cộng ba phạm vi vào nhau: chúng chồng lặp.
- Số picks trong 243 dòng thống kê đã được đối chiếu với các ván thu thập.
- `stage_prizes.csv` là thưởng vòng bảng, không phải toàn bộ thưởng thứ hạng
  chung cuộc. `amount` là số nguyên, `currency=VND`; giữ cả `raw_amount`.
- `normalized_table_cells.csv` vẫn là dữ liệu cấp ô, không phải mọi bảng đã
  được chuyển thành schema thống kê chuyên biệt. Các cột `parent_*` giữ quan hệ
  bảng lồng; `row_index`/`column_index` là tọa độ vật lý, chưa mở rộng spans.

### Identity, roster và thời gian

- `players.csv` gồm cả staff. 72 dòng roster trỏ đến 71 ID tham chiếu nguồn.
- 14 tham chiếu person là redlink: `source_page_exists=false`,
  `identity_status=source_redlink`. ID không chứng minh có trang biography hoặc
  nhân thân đã được xác minh độc lập.
- Roster của giải **không phải lineup từng ván**; `lineup_verified=false`.
- `scheduled_at` là lịch series, không phải thời điểm bắt đầu từng game.
  `played_at` còn thiếu; không dùng lịch series để giả làm timestamp ván.
- `sequence_number`/`phase` còn null; thứ tự dòng CSV không phải thứ tự draft.
- 86 ván có patch nguồn-backed; patch còn thiếu ở các ván khác phải giữ null.

### Sẵn sàng ML đến mức nào?

Hai bảng candidate/transaction đã có canonical IDs và kết quả.
Nhưng `quality.json` vẫn có `training_ready=false` vì:

```text
missing_played_at_for_temporal_split
temporal_split_not_implemented
```

Không dùng `prediction_ready` cấp game để kết luận toàn dataset đã sẵn sàng
training. Nếu chia tập sau này, giữ các ván cùng series trong cùng tập và tránh
đưa thống kê tổng giải chứa kết quả tương lai vào feature dự đoán.
Draft Recommender chưa có dataset thứ tự đã xác minh.

## 6. Truy ngược về dữ liệu nguồn

Các cột provenance thường có:

```text
page_title, source_url, revision_id, content_hash,
locator, template_hash, parser_version
```

- `revision_id`: revision của trang đã lấy.
- `locator`: vị trí template/field hoặc ô bảng trong trang.
- `content_hash`: tìm wikitext gốc tại
  `raw/liquipedia/blobs/<content_hash>.wikitext`.
- Bảng render còn có `rendered_at`, `rendered_hash`, `response_path`;
  `response_path` tính tương đối từ `raw/liquipedia/`.
- Nội dung template được transclude có thể phản ánh trạng thái tại lúc fetch,
  không mặc định là nội dung lịch sử của mọi trang phụ theo revision trang cha.

Phần dữ liệu nguồn ngoài thư mục dataset:

```text
raw/liquipedia/
├── blobs/             # Wikitext gốc, deduplicate bằng checksum
├── runs/<uuid>/       # run.json và responses API từng lần crawl
├── reviewed/          # Mapping identity và bằng chứng nguồn
├── policy/            # Bằng chứng điều khoản/API/robots
├── probes/            # Các request kiểm tra ban đầu
├── html-probes/       # Bằng chứng kiểm tra truy cập HTML
└── curl-comparisons/  # Request curl chẩn đoán
```

Raw, mapping và CSV chuẩn hóa được giữ riêng. Các file probe/chẩn đoán không
tự động trở thành đầu vào dataset: danh sách archive được chọn nằm trong
`contracts/liquipedia/aog-2026-spring.dataset.json`.

Chi tiết crawl, replay và build lại dataset:
[Liquipedia MVP runbook](liquipedia-mvp.md).
