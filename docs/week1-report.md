## Báo cáo tiến độ Tuần 1

### 1. Mục tiêu
- Tìm hiểu các dịch vụ AWS chính sử dụng trong đề tài: API Gateway, Lambda, DynamoDB, SQS, S3, CloudWatch, IAM LabRole và VPC.
- Thiết kế kiến trúc tổng thể cho hệ thống thi trắc nghiệm serverless.
- Dựng các tài nguyên nền tảng trên AWS Learner Lab tại region `us-east-1`.
- Kiểm thử một luồng API thực tế từ API Gateway → Lambda → DynamoDB.
- Xây dựng naming convention và tag convention cho project.

### 2. Các dịch vụ đã tìm hiểu và triển khai
- **API Gateway:** tạo HTTP endpoint và route request tới Lambda.
- **AWS Lambda:** xử lý logic API và truy cập DynamoDB.
- **DynamoDB:** tạo các bảng `Users`, `Exams`, `Questions`, `Submissions`.
- **SQS:** tạo `quiz-grading-queue` để chuẩn bị cho luồng chấm điểm bất đồng bộ.
- **S3:** tạo report bucket để lưu file CSV kết quả ở các tuần sau.
- **CloudWatch:** kiểm tra log của Lambda để hỗ trợ debug.
- **IAM LabRole:** sử dụng role có sẵn trong Learner Lab cho Lambda.
- **VPC:** tạo VPC với public/private subnet, Internet Gateway, route table và S3 Gateway Endpoint.

### 3. Kiến trúc hệ thống
Luồng chính hiện tại:

`Client → API Gateway → Lambda → DynamoDB`

Luồng dự kiến cho chấm điểm:

`Lambda → SQS → Grading Lambda → DynamoDB`

S3 được sử dụng để lưu báo cáo CSV và CloudWatch dùng cho logging/monitoring.

### 4. Kết quả đã thực hiện
- `GET /health` chạy thành công, trả HTTP 200.
- `GET /exams/{examId}` chạy thành công, Lambda đọc dữ liệu từ DynamoDB và trả JSON.
- Lambda log xuất hiện trên CloudWatch.
- Đã tạo DynamoDB tables: `Users`, `Exams`, `Questions`, `Submissions`.
- Đã tạo S3 report bucket.
- Đã tạo SQS grading queue.
- Đã cấu hình VPC:
  - CIDR: `10.0.0.0/16`
  - Public subnet: `10.0.1.0/24`
  - Private subnet: `10.0.2.0/24`
  - Internet Gateway
  - Public/Private Route Table
  - S3 Gateway Endpoint
- Lambda hiện tại chưa đưa vào VPC để tránh phát sinh cấu hình mạng không cần thiết.

### 5. Naming và Tag Convention
Prefix resource: `quiz-`

Ví dụ:
- Lambda: `quiz-health-function`, `quiz-api-db`
- SQS: `quiz-grading-queue`
- API Gateway: `quiz-api`
- VPC: `quiz-vpc`

Tag:
- `Project = ServerlessQuiz`
- `Environment = Dev`
- `Team = Capstone`
- `ManageBy = Vchien`

### 6. Kế hoạch Tuần 2
- Hoàn thiện API cho Exam và Question.
- Bắt đầu xác thực JWT tự cài đặt.
- Thiết kế luồng start exam / submit exam.
- Đưa submission vào SQS.
- Triển khai grading Lambda.
- Tiếp tục sử dụng CloudWatch để debug và chuẩn bị test concurrency/throttling.