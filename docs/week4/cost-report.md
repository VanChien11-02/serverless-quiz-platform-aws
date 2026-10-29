# Tuần 4 – Tổng kết chi phí và tối ưu tài nguyên

**Region:** `us-east-1`  
**Minh chứng:** `screenshots/week4/17-cost-report.png`  
**Tài liệu kế thừa:** `docs/week2/cost-estimation.md`.

## 1. Kết quả xem Billing and Cost Management

Ảnh console cho thấy trang Billing and Cost Management có biểu đồ chi phí theo tháng từ May đến Oct 2026, nhóm theo dịch vụ. Các nhãn số trên biểu đồ được làm tròn về `$0.00`; ảnh không cho thấy bảng số liệu chi tiết, bộ lọc theo tag `Project` hoặc một tổng chi phí cụ thể có thể quy cho hệ thống thi trắc nghiệm.

Do đó, kết luận đúng theo ảnh hiện có là **đã mở và kiểm tra trang chi phí, nhưng chưa xác minh được tổng chi phí thực tế của riêng project**. Không ghi `$0.00` là tổng chi phí thực nếu giao diện chỉ đang làm tròn số.

## 2. Số liệu sử dụng có thể xác nhận

| Dịch vụ | Số liệu có trong bộ minh chứng | Điều chưa thể kết luận |
|---|---|---|
| API Gateway / Locust | Snapshot Locust lần lượt 110, 700, 1,400 và 2,792 requests ở các mức 10/50/100/200 VU | Đây là tổng request của từng snapshot/test, không phải tổng request toàn kỳ AWS |
| Lambda | Account quota `ConcurrentExecutions=400`; `FunctionCount=12`; function `quiz-export-report` dùng unreserved concurrency | Không có tổng Invocations/Duration theo kỳ hoặc theo function |
| DynamoDB | Ảnh scan `Submissions` báo `Items returned (2)` | Không phải số tổng request read/write hoặc số bài thi toàn tải |
| SQS | Không có số liệu MessagesSent/Received/Deleted trong ảnh | Khối lượng SQS chưa xác minh |
| S3 | Object CSV có dung lượng `522.0 B` | Chỉ là kích thước object được chụp, không phải tổng dung lượng bucket |
| CloudWatch | Một điểm `ConcurrentExecutions=1`; một điểm `Throttles=0` trong khoảng thời gian đang xem | Không cùng cửa sổ thời gian với Locust; không thể dùng làm số đo dưới tải |

## 3. So sánh với dự toán Tuần 2

Báo cáo/dự toán Tuần 2 nêu khoảng `0.0069 USD` cho kịch bản giả định 200 lượt thi. Đây là **ước tính theo kịch bản**, không phải chi phí thực đã tính từ hóa đơn AWS.

| Khoản mục | Giá trị | Loại số liệu |
|---|---:|---|
| Kịch bản 200 lượt thi theo dự toán Tuần 2 | `~0.0069 USD` | Ước tính |
| Chi phí thực tế riêng của project trong Tuần 4 | `~0.01 USD` | Ước tính |

