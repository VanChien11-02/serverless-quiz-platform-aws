# Tuần 2 – Ước tính chi phí vận hành (Cost Estimation)

> **Trạng thái:** Dự toán theo giả định, **chưa phải chi phí thực tế** và **chưa phải kết quả kiểm thử tải**.

## 1. Phạm vi ước tính

Luồng đã triển khai: **API Gateway → AWS Lambda → DynamoDB → Amazon SQS → Grading Lambda → DynamoDB**. CloudWatch Logs hỗ trợ tìm lỗi. S3 là tài nguyên đã xây dựng ở giai đoạn nền tảng; việc xuất CSV lên S3 là chức năng dự kiến phát triển ở giai đoạn sau, nên chi phí S3 dưới đây chỉ là phần minh họa nếu sử dụng lưu báo cáo.

Dự toán sử dụng **API Gateway HTTP API**, **Lambda x86**, **DynamoDB Standard On-demand**, **SQS Standard** và giá tham khảo tại `us-east-1`. Nếu tài nguyên thực tế dùng REST API, Provisioned capacity, bộ nhớ Lambda khác hoặc cấu hình khác, cần tính lại.

## 2. Giả định một đợt sử dụng (200 lượt thi)

| Thông số | Giả định | Ghi chú |
|---|---:|---|
| Lượt thi | 200 | Kịch bản tính chi phí, **không khẳng định 200 người đồng thời** |
| API requests | 2.000 | Trung bình 10 requests/lượt thi |
| Lambda invocations | 2.200 | 2.000 xử lý API + 200 lượt chấm điểm |
| Memory Lambda | 128 MB (0,125 GB) | Giá trị giả định để tính mẫu |
| Duration Lambda bình quân | 0,3 giây/invocation | Chưa lấy từ CloudWatch metric thực tế |
| DynamoDB read request units | 5.000 RRU | Giả định tổng số đơn vị đọc |
| DynamoDB write request units | 1.500 WRU | Giả định tổng số đơn vị ghi |
| SQS API requests | 600 | Giả định send/receive/delete cho 200 bài |
| CloudWatch Logs ingestion | 0,002 GB | Khoảng 2 MB log phát sinh |
| S3 Standard storage | 0,01 GB-tháng | Khoảng 10 MB dữ liệu/báo cáo giả định |
| S3 PUT / GET | 10 PUT / 10 GET | Chưa tính xuất CSV thực tế |

**Giả định tính giá:** Chưa trừ Free Tier hoặc credits của Learner Lab; không tính phí cố định, KMS tùy chọn, data transfer ra Internet, retries, lưu trữ DynamoDB phát sinh, CloudWatch custom metrics/alarms và các chi phí ngoài phạm vi này. Khối lượng rất nhỏ nên con số thường chỉ ở mức phần nghìn USD. Đơn giá AWS có thể thay đổi; cần xác nhận lại trong [AWS Pricing Calculator](https://calculator.aws/) khi nộp báo cáo.

## 3. Công thức và bảng ước tính

**AWS Lambda**

- Số GB-giây = `2.200 × 0,125 GB × 0,3 giây = 82,5 GB-s`.
- Phí thực thi = `82,5 × 0,0000166667 = 0,001375 USD`.
- Phí lượt gọi = `2.200 / 1.000.000 × 0,20 = 0,000440 USD`.
- **Tổng Lambda ≈ 0,001815 USD**.

**DynamoDB**

- Read = `5.000 / 1.000.000 × 0,125 = 0,000625 USD`.
- Write = `1.500 / 1.000.000 × 0,625 = 0,0009375 USD`.

| Dịch vụ | Giả định tính giá | Chi phí mẫu (USD) |
|---|---|---:|
| API Gateway – HTTP API | 2.000 × 1,00 USD/triệu requests | 0,0020000 |
| AWS Lambda | 2.200 requests + 82,5 GB-s | 0,0018150 |
| DynamoDB On-demand | 5.000 RRU + 1.500 WRU | 0,0015625 |
| SQS Standard | 600 × 0,40 USD/triệu requests | 0,0002400 |
| CloudWatch Logs | 0,002 GB × 0,50 USD/GB ingestion | 0,0010000 |
| S3 Standard (minh họa) | 0,01 GB-tháng + 10 PUT + 10 GET | 0,0002840 |
| **Tổng ước tính trong phạm vi giả định** | **Chưa trừ Free Tier** | **≈ 0,0069015 USD** |

**Kết luận:** Khoảng **0,0069 USD cho một đợt 200 lượt thi giả định** đối với riêng các hạng mục nêu trong bảng. Không nên diễn giải đây là giá vận hành trọn gói hoặc mức chi phí đã được AWS ghi nhận. Giá có thể cao hơn khi tăng số câu hỏi, lượng ghi log, lưu trữ, truyền dữ liệu, xử lý lỗi hoặc khi dùng API Gateway REST API.

## 4. Đánh giá và biện pháp tối ưu

1. **Lambda:** Bắt đầu với 128 MB và đo Duration/Errors/Throttles trên CloudWatch trước khi thay đổi memory; tránh gọi API dư thừa.
2. **DynamoDB:** Dùng `Query`/`GetItem` phù hợp với khóa; hạn chế `Scan` toàn bảng; theo dõi read/write capacity đã dùng.
3. **SQS:** Dùng xử lý bất đồng bộ; hạn chế message trùng, xử lý theo hướng idempotent; kiểm tra retry và dead-letter queue khi triển khai nâng cao.
4. **CloudWatch:** Chỉ log dữ liệu kỹ thuật cần thiết, không log token/mật khẩu/đáp án nhạy cảm; cấu hình retention phù hợp.
5. **S3:** Chỉ lưu file cần thiết; không public bucket; dọn tệp thử nghiệm theo quy định Learner Lab.
6. **Learner Lab:** Dừng/xóa tài nguyên phát sinh phí khi kết thúc buổi thực hành, gắn tag `Project` , `Enviroment`, `Team` và `ManageBy` , theo dõi ngân sách của Lab.
