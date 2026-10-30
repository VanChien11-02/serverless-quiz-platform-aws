# Tuần 4 – AWS Learner Lab Cleanup Report

**Project:** Serverless Quiz Platform  
**Region:** `us-east-1`  
**Environment:** AWS Learner Lab

## 1. Mục tiêu cleanup

Sau khi hoàn thành triển khai, kiểm thử và quay video demo hệ thống thi trắc nghiệm Serverless, tiến hành kiểm tra và dọn dẹp các tài nguyên AWS nhằm:

- Tránh phát sinh chi phí không cần thiết sau khi kết thúc đồ án.
- Giải phóng các tài nguyên không còn sử dụng.
- Đảm bảo các tài nguyên dùng chung của AWS Learner Lab không bị ảnh hưởng.
- Lưu giữ đầy đủ mã nguồn, kết quả kiểm thử và minh chứng phục vụ báo cáo.

Chỉ thực hiện xóa các tài nguyên thuộc phạm vi dự án. Không xóa `LabRole`, `LabInstanceProfile` hoặc các tài nguyên dùng chung do AWS Learner Lab quản lý.

## 2. Minh chứng kiểm tra tài nguyên AWS sau cleanup

Đã bổ sung ảnh chụp AWS Console để ghi nhận trạng thái các nhóm tài nguyên thuộc dự án trong Region `us-east-1`.

| Dịch vụ | Nội dung kiểm tra | Minh chứng |
|---|---|---|
| AWS Lambda | Danh sách và trạng thái các Lambda Function thuộc dự án | [lambda.png](../../screenshots/week4/cleanup/lambda.png) |
| Amazon DynamoDB | Các bảng Exams, Questions, Submissions, Users | [dynamoDB.png](../../screenshots/week4/cleanup/dynamoDB.png) |
| Amazon SQS | Queue xử lý chấm điểm tự động | [sqs.png](../../screenshots/week4/cleanup/sqs.png) |
| Amazon S3 | Bucket lưu trữ báo cáo CSV và website | [s3.png](../../screenshots/week4/cleanup/s3.png) |

## 3. Các công việc đã thực hiện

### 3.1. Lưu trữ dữ liệu và minh chứng

- [x] Lưu mã nguồn dự án lên GitHub.
- [x] Lưu Postman Collection và các request kiểm thử.
- [x] Lưu kết quả kiểm thử Locust ở các mức 10, 50, 100 và 200 Virtual Users.
- [x] Lưu CSV/HTML report và các biểu đồ kết quả kiểm thử.
- [x] Lưu ảnh minh chứng Lambda Export và kết quả phân quyền Admin/Student.
- [x] Lưu ảnh CSV trên S3 và nội dung báo cáo.
- [x] Lưu ảnh DynamoDB, Lambda Concurrency, CloudWatch và Billing.

### 3.2. Kiểm tra và dọn dẹp tài nguyên

- [x] Dừng Locust sau khi hoàn thành kiểm thử tải và lưu kết quả.
- [x] Kiểm tra cấu hình Reserved Concurrency và SQS Maximum Concurrency.
- [x] Kiểm tra tag `Enviroment`, `Team`, `Project` và `ManagerBy` trên các tài nguyên thuộc dự án.
- [x] Sao lưu mã nguồn, Postman Collection, báo cáo kiểm thử và ảnh minh chứng trước khi xóa dữ liệu.
- [x] Kiểm tra và xử lý các tài khoản test, submission test và object CSV không còn cần thiết.
- [x] Kiểm tra các Lambda Function, bảng DynamoDB, SQS Queue và S3 Bucket thuộc phạm vi dự án.
- [x] Chụp ảnh AWS Console sau khi kiểm tra cleanup và lưu tại `screenshots/week4/cleanup/`.

## 4. Nguyên tắc quản lý tài nguyên

Trong quá trình cleanup, tuân thủ các nguyên tắc:

1. Chỉ xóa tài nguyên do dự án tạo ra.
2. Không xóa IAM LabRole và LabInstanceProfile.
3. Không xóa tài nguyên dùng chung của AWS Learner Lab.
4. Lưu lại mã nguồn, dữ liệu và kết quả kiểm thử trước khi xóa.
5. Kiểm tra Region `us-east-1` để tránh ảnh hưởng đến tài nguyên ngoài phạm vi dự án.
6. Ưu tiên giải phóng các tài nguyên có khả năng tiếp tục phát sinh chi phí.

## 5. Kết luận

Đã bổ sung minh chứng kiểm tra tài nguyên AWS sau cleanup cho bốn dịch vụ chính: Lambda, DynamoDB, SQS và S3.

Các kết quả kiểm thử, mã nguồn, Postman Collection, CSV report và tài liệu dự án được lưu trữ trên GitHub để phục vụ việc đối chiếu và đánh giá đồ án.

Việc cleanup được thực hiện nhằm hạn chế chi phí phát sinh và đảm bảo không ảnh hưởng đến các tài nguyên dùng chung của AWS Learner Lab.