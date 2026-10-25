# Tuần 3 – Nhật ký công việc (Worklog)

**Đề tài:** Nền tảng thi trắc nghiệm trực tuyến Serverless (Nhóm: Capstone)  
**Môi trường:** AWS Academy Learner Lab  
**Region:** `us-east-1`  

## 1. Mục tiêu tuần 3

Kế thừa kết quả Tuần 1 (thiết kế, AWS Learner Lab) và Tuần 2 (Exam API, Attempt API, DynamoDB, SQS, Grading Lambda), Tuần 3 tập trung vào:

- Triển khai `quiz-auth` với API Register/Login, băm mật khẩu và phát hành JWT tự cài đặt, không dùng Cognito.
- Tích hợp `quiz-jwt-authorizer` với API Gateway; kiểm tra token, hạn sử dụng và thông tin người dùng.
- Phân quyền Admin/Student trong Exam Lambda và Attempt Lambda; kiểm soát quyền sở hữu bài thi.
- Kiểm thử tiêu cực: Student không tạo đề/thêm câu hỏi; Admin không bắt đầu/nộp/xem bài thi; JWT hết hạn bị từ chối.
- Kiểm tra CloudWatch Logs/Metrics, tích hợp SQS/Grading và cập nhật GitHub, tài liệu, minh chứng.

## 2. Nhật ký công việc thực tế

| Sinh viên | Giờ thực tế | Công việc thực hiện | Minh chứng / Commit |
|---|---:|---|---|
| Lê Văn Chiến | 1 | Cấu hình DynamoDB `Users`, Auth Lambda, Register/Login; kiểm tra JWT và mật khẩu băm. | `04-login-student.png`, `05-login-admin.png`; `d4063af` |
| Lê Văn Chiến | 2 | Tạo và gắn Lambda Authorizer vào API Gateway, bảo vệ các route, tắt caching khi kiểm thử JWT hết hạn. | `01-api-routes-authorizer.png`; `d4063af` |
| Lê Văn Chiến | 1 | Sửa RBAC trong Exam Lambda; chặn Student tạo Exam và thêm Question. | `07-student-create-exam-403.png`, `08-student-add-question-403.png`; `c26ee23` |
| Lê Văn Chiến | 1 | Sửa RBAC trong Attempt Lambda; chặn Admin Start/Submit/Get Result, kiểm tra chủ sở hữu bài thi. | `10-admin-start-403.png`, `11-admin-submit-403.png`, `12-admin-result-403.png`; `c26ee23` |
| Lê Văn Chiến | 3 | Test cùng JWT khi còn hạn và sau khi hết hạn; khôi phục `JWT_TTL_SECONDS=3600` sau kiểm thử. | `14a-token-valid-before-expiry.png`, `14-expired-jwt-denied.png` |
| Lê Văn Chiến | 1 | Giám sát CloudWatch Metrics/Logs, kiểm tra luồng SQS/Grading và ghi kết quả thực tế. | `20-cloudwatch-metrics.png`; [ảnh log/result nếu có] |
| Lê Văn Chiến | 1 | Hoàn thiện sơ đồ Tuần 3, Postman Collection, báo cáo và commit GitHub. | `1e0c2b1`; `docs/week3/` |

## 3. Tổng hợp thời gian

| Thành viên | MSSV | Tổng giờ thực tế |
|---|---|---:|---|
| Lê Văn Chiến | 24110170 | 10 |


## 4. Các vấn đề kỹ thuật và cách xử lý

| Vấn đề gặp phải | Cách khắc phục/kiểm tra |
|---|---|
| Lambda `quiz-auth` báo `No module named 'lambda_function'` | Đồng bộ tên file `.py` và Runtime Handler, kiểm tra các file được đóng gói. |
| Lambda Login timeout 3 giây | Điều chỉnh Timeout để chẩn đoán, xem CloudWatch Logs và cấu hình truy cập DynamoDB. |
| Student vẫn tạo Exam/Question | Kiểm tra Bearer Token thực gửi trong Postman và bổ sung RBAC trong Exam Lambda. |
| Admin vẫn Start/Submit/Get Result | Bổ sung kiểm tra role trong Attempt Lambda, chỉ cho Student sử dụng các route này. |
| Get Result còn `SUBMITTED` ở một lần kiểm thử | Kiểm tra SQS trigger, Grading Lambda, CloudWatch Logs và DynamoDB; chỉ ghi `COMPLETED` khi có minh chứng. |
