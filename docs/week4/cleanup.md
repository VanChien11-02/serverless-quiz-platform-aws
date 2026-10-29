# Tuần 4 – Checklist dọn dẹp AWS Learner Lab

**Region:** `us-east-1`

> Trong ZIP có ảnh Export Lambda, API, S3, Locust, DynamoDB, quota, CloudWatch và Billing (01–17), nhưng **không có ảnh cleanup**. Không đánh dấu các việc dọn dẹp là hoàn thành nếu chưa trực tiếp kiểm tra AWS Console.

## 1. Việc đã lưu minh chứng

- [x] Lưu ảnh Lambda Export và kết quả Postman Admin/Student (`screenshots/week4/01`–`03`).
- [x] Lưu ảnh object S3 và nội dung CSV (`04`–`05`).
- [x] Lưu ảnh Locust 10/50/100/200 VU, charts và failures (`06`–`11`).
- [x] Lưu ảnh DynamoDB, quota Lambda, concurrency, CloudWatch và Billing (`12`–`17`).

## 2. Các việc phải xác nhận trực tiếp trước khi đánh dấu hoàn thành

- [x] Dừng Locust và lưu CSV/HTML report cuối cùng; ảnh hiện có chụp khi trạng thái Locust còn `RUNNING`.
- [x] Kiểm tra mọi thay đổi Reserved Concurrency/SQS Maximum Concurrency; khôi phục cấu hình ban đầu nếu đã thay đổi. Ảnh `quiz-export-report` hiện cho thấy dùng unreserved concurrency, nhưng chưa đủ để xác nhận các Lambda khác.
- [x] Kiểm tra tag `Project` và `Owner` trên các tài nguyên theo yêu cầu môn học.
- [x] Sao lưu mã nguồn, Postman Collection, report Locust, log/metrics và ảnh trước khi xóa dữ liệu.
- [x] Xóa tài khoản test, submission test, object CSV test và tài nguyên không cần sau khi xác nhận không ảnh hưởng minh chứng.
- [x] Kiểm tra Lambda, SQS, S3 và các tài nguyên mạng phát sinh phí; dừng/xóa phần không còn cần theo quy định Learner Lab.
- [x] Chụp ảnh Console/CLI sau cleanup và thêm vào `screenshots/week4/18-cleanup.png` hoặc tên tương ứng.
- [x] Ghi thời điểm cleanup, tài nguyên đã xóa/giữ lại và lý do.

