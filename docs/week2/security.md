# Tuần 2 – Đánh giá bảo mật hệ thống (Security Assessment)

## 1. Kiến trúc và phạm vi bảo vệ

Luồng xử lý: **Postman/Client → API Gateway (HTTPS) → Lambda → DynamoDB → SQS → Grading Lambda → DynamoDB**.

| Thành phần | Nội dung đánh giá |
|---|---|
| API Gateway | Giao tiếp HTTPS; cần bảo vệ route quản trị và các route liên quan đến người dùng ở Tuần 3 |
| Lambda | Kiểm tra dữ liệu request, trạng thái bài thi và hạn nộp |
| DynamoDB | Lưu đề thi, câu hỏi, lượt thi, điểm; không công bố dữ liệu nội bộ |
| SQS | Tách xử lý chấm điểm bất đồng bộ; cần tính đến xử lý message lặp |
| CloudWatch | Tra cứu lỗi và giám sát; tránh log dữ liệu nhạy cảm |
| IAM | Dùng `LabRole` có sẵn theo giới hạn AWS Learner Lab; không tạo IAM user/role mới |

## 2. Phòng tránh lộ đáp án

Đáp án đúng được dùng trong quá trình chấm điểm nội bộ. Response của API bắt đầu thi chỉ cung cấp câu hỏi và phương án lựa chọn. Điều này giúp tránh lộ trực tiếp đáp án qua API Start Exam; tuy nhiên vẫn cần phân quyền API và hạn chế người dùng đọc được dữ liệu lưu trong DynamoDB.

## 3. Kiểm tra giới hạn thời gian phía Backend

Khi bắt đầu thi, Lambda lưu thời điểm bắt đầu và thời hạn nộp. Khi Submit, hệ thống kiểm tra lại thời gian trên backend, thay vì tin vào đồng hồ hoặc dữ liệu do client gửi. Trường hợp quá hạn đã được kiểm thử và bị từ chối.

## 4. Nộp bài trùng và tính toàn vẹn điểm số

Với lượt thi đã `COMPLETED`, Postman hiện có thể nhận **HTTP `200 OK`** khi gọi lại Submit. Tuy nhiên, thử thay đổi `answers` rồi lấy kết quả cho thấy `correctCount`, `totalQuestions` và `score` **không đổi**. Đây là hành vi xử lý lặp an toàn ở mức kiểm thử tuần 2, **không phải** bằng chứng đã chặn mọi race condition khi có nhiều request đồng thời.

Hướng củng cố: dùng DynamoDB `ConditionExpression` để chỉ chuyển trạng thái `IN_PROGRESS → SUBMITTED` một lần; đảm bảo Grading Lambda xử lý lặp theo hướng **idempotent**, do SQS có thể gửi message nhiều lần.

## 5. Rủi ro và hạn chế còn tồn tại

| Rủi ro | Mức độ ưu tiên | Hướng xử lý |
|---|---|---|
| Chưa có JWT Authentication | Cao | Tự triển khai xác thực JWT ở Tuần 3, không dùng Cognito |
| Chưa có Admin/Student Authorization | Cao | Bảo vệ route tạo đề/thêm câu hỏi; chỉ thí sinh sở hữu lượt thi được nộp/xem điểm |
| `studentId` hiện là dữ liệu test do client cung cấp | Cao | Lấy danh tính từ JWT đã xác thực, không tin trực tiếp ID do client gửi |
| Có thể gửi request đồng thời (race condition) | Trung bình–Cao | Kiểm thử đồng thời và dùng conditional write/update |
| SQS có thể giao message ít nhất một lần | Trung bình | Idempotent grading, retry hợp lý; cân nhắc DLQ |
| Secrets/token/lỗi chứa dữ liệu nhạy cảm | Cao | Không commit secret; ẩn token và thông tin nhạy cảm trong log/ảnh công khai |
| Quyền của `LabRole` rộng theo môi trường học | Trung bình | Đánh giá quyền thực tế, tuân thủ giới hạn Lab; áp dụng least privilege khi triển khai ngoài Lab |
| Cấu hình S3, DynamoDB, SQS mã hóa/khóa truy cập | Cần xác minh | Chụp cấu hình thực tế, không đánh dấu đã triển khai khi chưa kiểm tra |

**Lưu ý:** Hệ thống hiện dùng để thực hành trong Learner Lab, chưa phù hợp mở truy cập công khai cho người dùng thật. HTTPS bảo vệ đường truyền nhưng không thay thế kiểm soát danh tính và quyền truy cập.

## 5. Kế hoạch bảo mật Tuần 3

1. Xây dựng `POST /auth/register` và `POST /auth/login` với mật khẩu được băm có salt; không lưu plaintext.
2. Tự tạo và xác minh JWT (chữ ký, thời hạn, issuer/audience phù hợp); bảo vệ JWT signing secret.
3. Phân quyền **Admin** (quản lý đề thi) và **Student** (thi/nộp/xem điểm).
4. Xác minh chủ sở hữu `submissionId` ở backend bằng thông tin đã được xác thực.
5. Bổ sung monitoring, cảnh báo, kiểm thử unauthorized/forbidden và thao tác đồng thời.
6. Rà soát S3 Block Public Access, quyền truy cập dữ liệu và encryption theo khả năng Learner Lab.

