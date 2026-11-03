<<<<<<< HEAD
# Liqi — Khung dự án huấn luyện Recommender System

Người phụ trách: Trọng. An phụ trách tích hợp và triển khai web.

## Trạng thái
Đây là KHUNG THƯ MỤC ban đầu, chưa triển khai thuật toán, chưa huấn luyện và chưa có kết quả thực nghiệm. Các file Python chứa mô tả nhiệm vụ và thông báo chưa triển khai. Không có API, frontend, Hadoop hoặc Spark. Dữ liệu gốc chưa đóng gói trong ZIP.

## Bắt đầu trên Windows
1. Giải nén ZIP, mở thư mục liqi_recommender bằng VS Code.
2. Chuẩn bị Python 3.10 trở lên. Khung hiện chỉ dùng thư viện chuẩn.
3. Sao chép dữ liệu theo bảng trong data/raw/README.md.
4. Đọc docs/01_kien_truc.md và docs/02_lo_trinh.md.
5. Triển khai lần lượt các module trong src; không chạy đánh giá test trước khi chốt mô hình.

## Các thư mục
| Thư mục | Công dụng |
|---|---|
| data/raw | CSV và manifest gốc thuộc cùng phiên bản |
| data/processed | Dữ liệu đã kiểm tra, chuẩn bị |
| configs | Cấu hình huấn luyện/đánh giá |
| notebooks | Notebook học và khám phá |
| src | Mã xử lý, huấn luyện, đánh giá, suy luận |
| artifacts | Mô hình đã học và metadata |
| reports | Chất lượng dữ liệu, metrics và phân tích |
| handoff | Gói bàn giao cho An sau khi hoàn thành |
| docs | Kiến trúc và lộ trình |
| tests | Kiểm tra logic quan trọng khi có code |

## Phạm vi bản đầu
Popularity và item-item dùng số đếm đồng xuất hiện; đánh giá che một tướng trong đội hình. Thông tin đối thủ ban đầu chỉ dùng lọc ứng viên, chưa phải counter-pick. Chưa có thứ tự draft được xác minh. Điểm xếp hạng không phải xác suất thắng.
=======
# Data-Mining-by-ndt
>>>>>>> 5b34ff96d3ff3dbd253af3bcd2ffe406fd86e1f4
