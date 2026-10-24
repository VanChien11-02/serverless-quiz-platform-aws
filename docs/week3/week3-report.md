# Tuần 3 – Tích hợp, bảo mật và giám sát hệ thống (Integration, Security & Monitoring)

**Đề tài:** Nền tảng thi trắc nghiệm trực tuyến Serverless trên AWS  
**Môi trường:** AWS Academy Learner Lab  
**Region:** `us-east-1` (N. Virginia)   
**Trạng thái:** Đã triển khai các thay đổi JWT/RBAC theo quá trình thực hành

## 1. Các chức năng đã triển khai (Completed Features)

Trong Tuần 2, hệ thống đã có các chức năng quản lý đề thi, bắt đầu làm bài, giới hạn thời gian, nộp bài, SQS chấm điểm bất đồng bộ và xem kết quả. Tuần 3 tập trung tích hợp lớp xác thực, phân quyền và giám sát trên kiến trúc đã có, không xây lại các chức năng lõi.

Các phần việc chính:

- **Xác thực JWT tự cài đặt (JWT Authentication):** Bổ sung `POST /auth/register`, `POST /auth/login`, lưu mật khẩu dạng PBKDF2-HMAC-SHA256 với salt; sinh JWT HS256 chứa `sub`, `role`, `iat`, `exp`, `iss`, `aud`; không sử dụng Amazon Cognito.
- **JWT Lambda Authorizer:** Xác minh token ở API Gateway, đọc Bearer token từ `Authorization` header; yêu cầu chữ ký, thời hạn, issuer/audience hợp lệ trước khi chuyển request vào Lambda nghiệp vụ.
- **Phân quyền Admin/Student (RBAC):** Admin quản lý đề thi/câu hỏi; Student bắt đầu bài thi, nộp bài, xem điểm. Lambda backend kiểm tra vai trò từ `requestContext.authorizer.lambda`, không tin role do client đưa trong JSON.
- **Bảo vệ dữ liệu bài thi:** Gắn `studentId` từ danh tính JWT; kiểm tra người nộp và người xem kết quả chính là chủ sở hữu `submissionId`.
- **Tăng cường bảo vệ dữ liệu:** Không trả `correctAnswer` trong nội dung Start Exam; không cho người dùng tự đăng ký quyền Admin; giữ cơ chế kiểm tra thời hạn nộp và nộp lại an toàn.
- **Giám sát:** Sử dụng CloudWatch Logs để gỡ lỗi Lambda; rà soát các metric Invocations, Errors, Duration, Throttles và API Gateway 4xx/5xx. Cảnh báo (Alarm) chỉ được đánh dấu hoàn thành khi có ảnh cấu hình thực tế.
- **Kiểm thử tích hợp:** Kiểm thử xác thực, vai trò và các trường hợp tiêu cực bằng Postman, đặc biệt test **token hết hạn** theo góp ý GVHD.

**Điểm kế thừa từ Tuần 2:** DynamoDB `Exams`, `Questions`, `Submissions`, SQS grading queue và Grading Lambda được giữ để duy trì luồng xử lý chấm điểm bất đồng bộ.

## 2. Cơ sở dữ liệu và cơ chế xác thực

### 2.1. DynamoDB

| Table | Partition key | Sort key | Vai trò trong Tuần 3 |
|---|---|---|---|
| `Users` | `userId` | — | Lưu tài khoản, role, salt và password hash |
| `Exams` | `examId` | — | Lưu đề do Admin tạo |
| `Questions` | `examId` | `questionId` | Lưu câu hỏi và đáp án đúng nội bộ |
| `Submissions` | `submissionId` | — | Lưu lượt thi, chủ sở hữu, đáp án, trạng thái và điểm |

Đối với `Users`, các trường chính gồm `userId`, `role`, `passwordSalt`, `passwordHash`, `passwordIterations`; tài khoản Admin được thêm thủ công bằng script seed và **không** được tạo thông qua API đăng ký công khai.

### 2.2. Cơ chế JWT

1. Student đăng ký qua `POST /auth/register`, tài khoản mặc định mang `role=Student`.
2. Client gọi `POST /auth/login`; Auth Lambda đọc `Users` và so sánh password hash theo cơ chế constant-time comparison.
3. Khi thông tin hợp lệ, Auth Lambda trả JWT HS256 với thời hạn cấu hình bằng `JWT_TTL_SECONDS` (ví dụ 3.600 giây).
4. API Gateway gọi `quiz-jwt-authorizer` cho các route được bảo vệ; authorizer xác minh signature, `exp`, `iss` và `aud`.
5. JWT Authorizer truyền `userId` và `role` vào context; các Lambda nghiệp vụ quyết định quyền trên từng route.

**Cấu hình chính cần đối chiếu trên AWS:**

| Tài nguyên | Cấu hình |
|---|---|
| Auth Lambda | `quiz-auth`, môi trường `USERS_TABLE=Users`, `JWT_SECRET`, `JWT_TTL_SECONDS` |
| JWT Authorizer Lambda | `quiz-jwt-authorizer`, dùng cùng `JWT_SECRET` |
| API Gateway HTTP API | Lambda Authorizer payload format `2.0`, response mode `Simple` |
| Identity source | `$request.header.Authorization` |
| Authorizer caching | Tắt trong giai đoạn kiểm thử token hết hạn |
| IAM | Sử dụng `LabRole` của Learner Lab; không tạo IAM user/role mới |

**Bảo mật thông tin:** Tuyệt đối không đưa `JWT_SECRET`, password, access token, `admin-item.json` hoặc password hash/salt lên GitHub và ảnh minh chứng công khai.

## 3. Các API và phân quyền đã tích hợp

Hai route `/auth/register` và `/auth/login` để `Authorization=NONE`; các route nghiệp vụ được bảo vệ bằng Lambda Authorizer. Tùy cách triển khai thực tế, có thể có Exam API và Attempt API riêng hoặc đã hợp nhất; cần kiểm tra Integration/Authorizer ở **từng route**.

| Method | Endpoint | Admin | Student |
|---|---|---|---|
| POST | `/auth/register` | Công khai (chỉ tạo Student) | Công khai (chỉ tạo Student) |
| POST | `/auth/login` | Công khai | Công khai |
| GET | `/exams` | Cho phép | Cho phép |
| GET | `/exams/{id}` | Cho phép | Cho phép |
| POST | `/exams` | Cho phép (`201` nếu hợp lệ) | Từ chối (`403`) |
| POST | `/exams/{id}/questions` | Cho phép (`201` nếu hợp lệ) | Từ chối (`403`) |
| POST | `/exams/{id}/start` | Từ chối (`403`) | Cho phép (`201` nếu hợp lệ) |
| POST | `/submissions/{id}/submit` | Từ chối (`403`) | Cho phép (`202` nếu hợp lệ) |
| GET | `/submissions/{id}/result` | Từ chối (`403`) | Cho phép đối với bài của mình (`200`) |

**Lưu ý:** `id` trong route Submit/Result là `submissionId`. Với Student khác chủ bài thi, backend phải trả `403`. Status HTTP có thể khác nếu dữ liệu đầu vào sai, bài hết hạn hoặc tài nguyên không tồn tại; bảng trên mô tả tình huống hợp lệ phục vụ test RBAC.

## 4. Quy trình hoạt động tích hợp (System Workflow)

**Luồng đăng nhập:**

`Postman/Client → API Gateway /auth/login → Auth Lambda → DynamoDB Users → JWT`

**Luồng gọi API được bảo vệ:**

`Client gửi Bearer JWT → API Gateway → JWT Authorizer → Lambda nghiệp vụ kiểm tra role/userId → DynamoDB`

**Luồng bài thi kế thừa Tuần 2:**

1. Admin đăng nhập, sử dụng token Admin để tạo đề và thêm câu hỏi.
2. Student đăng nhập bằng tài khoản riêng, xem danh sách đề và bắt đầu lượt thi.
3. Attempt Lambda lưu `studentId` lấy từ JWT, đồng thời xáo trộn thứ tự câu hỏi và không trả đáp án đúng.
4. Student gửi bài trước khi hết hạn; Lambda kiểm tra chủ sở hữu và lưu trạng thái `SUBMITTED`.
5. Lambda gửi message chứa `submissionId` tới SQS; Grading Lambda xử lý bất đồng bộ.
6. Grading Lambda tính điểm, cập nhật `score`, `correctCount`, `totalQuestions`, `gradedAt` và `status=COMPLETED`.
7. Student đã xác thực gọi Get Result, chỉ đọc được lượt thi thuộc tài khoản mình.
8. CloudWatch hỗ trợ xem log, metric, lỗi xác thực và lỗi Lambda.


## 5. Kết quả kiểm thử (Testing Results)

Bộ Postman dùng để kiểm thử: `postman/week3-jwt-rbac.postman_collection.json`. Chi tiết và ảnh cần đính kèm được quản lý tại [week3-test-results.md](week3-test-results.md).

**Sự cố thực hành và cách xử lý:**

| Sự cố | Nguyên nhân/hướng khắc phục |
|---|---|
| `Runtime.ImportModuleError: No module named 'lambda_function'` ở Auth Lambda | Tên file triển khai và Handler không khớp; thống nhất Handler với `lambda_function.py` hoặc `quiz_auth_handler.py` |
| `Sandbox.Timedout` sau 3 giây | Tăng Timeout để xác định nguyên nhân; kiểm tra kết nối DynamoDB/VPC và số liệu Duration; không xem tăng Timeout là đã sửa tận gốc nếu còn lỗi mạng |
| Student mang token hợp lệ vẫn tạo được đề (`201`) | Kiểm tra request có đang gửi `admin_token` hay không; cập nhật Exam Lambda để kiểm tra `role=Admin` trước các request POST |
| Admin có thể gọi Start/Submit/Result | Cập nhật Attempt Lambda để chỉ cho `role=Student`, kiểm tra `studentId` từ context JWT |

### 5.1. Đường dẫn minh chứng cấp file trên GitHub

Các liên kết dưới đây được viết theo đúng cấu trúc repository. **Chúng chỉ hoạt động sau khi nhóm chụp ảnh thật và đưa các file cùng tên lên GitHub**. Khi nộp GVHD, có thể mở từng link và sao chép địa chỉ file.

- [Cấu hình JWT Authorizer và API routes](../../screenshots/week3/01-api-routes-authorizer.png)
- [Danh sách Lambda Tuần 3](../../screenshots/week3/02-lambda-functions.png)
- [Student đăng nhập và nhận role Student](../../screenshots/week3/04-login-student.png)
- [Student không được tạo đề — 403](../../screenshots/week3/07-student-create-exam-403.png)
- [Student không được thêm câu hỏi — 403](../../screenshots/week3/08-student-add-question-403.png)
- [Admin không được Start — 403](../../screenshots/week3/10-admin-start-403.png)
- [Admin không được Submit — 403](../../screenshots/week3/11-admin-submit-403.png)
- [Admin không được Get Result — 403](../../screenshots/week3/12-admin-result-403.png)
- [Token trước thời điểm hết hạn — 200](../../screenshots/week3/14a-token-valid-before-expiry.png)
- [Cùng token sau khi hết hạn — từ chối](../../screenshots/week3/14-expired-jwt-denied.png)
- [SQS Trigger của Grading Lambda](../../screenshots/week3/18-sqs-grading-trigger.png)
- [Get Result sau khi chấm — COMPLETED](../../screenshots/week3/19-result-completed.png)
- [CloudWatch Metrics](../../screenshots/week3/20-cloudwatch-metrics.png)
- [Postman Collection Tuần 3](../../postman/week3-jwt-rbac.postman_collection.json)
- [Sơ đồ kiến trúc Tuần 3](../../architecture/week3-architecture.png)

## 6. Bảo mật, CloudWatch và tiếp thu góp ý GVHD

### 6.1. Tiếp thu nhận xét GVHD

GVHD đề nghị ở Tuần 3 bổ sung **negative test dùng token hết hạn** để chứng minh hệ thống thực sự từ chối request không còn hợp lệ. Cách thực hiện:

1. Tạm đặt `JWT_TTL_SECONDS=30` trên `quiz-auth`, đồng thời tắt Authorizer caching.
2. Đăng nhập Student lấy **token mới**; gọi `GET /exams` trước khi hết hạn, ghi nhận kết quả thành công.
3. Gọi lại đúng token này sau khi hết hạn; ghi nhận `401` hoặc `403` theo cấu hình HTTP API; phải đảm bảo không trả `200`.
4. Chụp ảnh Postman có URL, status, thời gian; che token trước khi commit.
5. Khôi phục `JWT_TTL_SECONDS=3600` và đăng nhập lại.

Không ghi “Đạt” trong bảng kiểm thử nếu chưa thực hiện và lưu được minh chứng cặp trước hạn/sau hạn.

### 6.2. Kiểm soát truy cập và tính toàn vẹn

- **Authentication** và **Authorization** tách biệt: JWT Authorizer xác thực danh tính; Lambda nghiệp vụ kiểm tra role và chủ sở hữu bài thi.
- Không nhận `studentId` từ body Client để gán quyền sở hữu lượt thi.
- Mật khẩu được băm với salt; public registration không cho truyền `role=Admin`.
- Dữ liệu nhạy cảm cần che trong log/ảnh; secret lưu ở biến môi trường trong phạm vi Learner Lab (chưa phải thiết kế quản lý secrets mức production).
- Kế thừa kiểm tra giới hạn thời gian và tránh sửa điểm ở các lượt thi đã hoàn thành từ Tuần 2.

### 6.3. Giám sát CloudWatch

| Thành phần | Nội dung cần theo dõi | Bằng chứng |
|---|---|---|
| `quiz-auth`, `quiz-jwt-authorizer` | Invocations, Errors, Duration; lỗi xác thực hoặc Handler | Log stream / Metrics |
| Exam, Attempt, Grading Lambda | Invocations, Errors, Throttles, ConcurrentExecutions | CloudWatch Metrics |
| API Gateway HTTP API | Count, 4xx, 5xx, Latency | Stage metrics / Access log nếu đã bật |
| Amazon SQS | Messages visible, messages in flight | SQS Monitoring |
| CloudWatch Alarm | Ví dụ Lambda Errors > 0 trong khoảng 5 phút | Ảnh cấu hình Alarm nếu đã tạo |

Các request không đủ quyền thường gây `4xx` như mong đợi; không đánh đồng test bảo mật bị từ chối với lỗi hệ thống `5xx`. Chưa có số liệu đo tải 200 người dùng và throttling thực tế cho Tuần 3; nội dung đó để Tuần 4.

## 7. Công cụ, dịch vụ và nhật ký công việc

- **Cloud Platform:** AWS Academy Learner Lab, `us-east-1`, IAM `LabRole`.
- **Backend:** Python, boto3, AWS Lambda; JWT HS256 tự cài đặt phục vụ mục đích học tập.
- **API:** Amazon API Gateway (HTTP API), Lambda Authorizer.
- **Database:** Amazon DynamoDB.
- **Queue:** Amazon SQS.
- **Monitoring:** Amazon CloudWatch.
- **Testing:** Postman, Lambda Test Events.
- **Version Control:** Git, GitHub.

Nhật ký thời gian thực tế, phân công, ảnh và commit cần ghi tại [worklog.md](worklog.md). **Phần AI hỗ trợ:** ChatGPT hỗ trợ tham khảo luồng JWT/RBAC, sinh mã mẫu, gỡ lỗi Handler/Timeout và biên soạn tài liệu. Sinh viên trực tiếp cấu hình tài nguyên, triển khai, chạy Postman và tự xác minh kết quả trên Learner Lab.

## 8. Kết quả đạt được và kế hoạch Tuần 4

Tuần 3 bổ sung tầng xác thực JWT và kiểm soát quyền Admin/Student vào nền tảng Serverless hiện có. Hệ thống được định hướng phân tách rõ: **Admin quản lý đề thi; Student thực hiện và xem kết quả bài thi của chính mình**, đồng thời kết hợp CloudWatch hỗ trợ kiểm tra và theo dõi hệ thống.

**Việc phải chốt trước khi nộp Tuần 3:** lưu ảnh các test RBAC sau sửa, cặp test token trước/sau khi hết hạn, cấu hình Authorizer cho route, CloudWatch, và một lần Get Result thực tế đạt `COMPLETED` nếu báo cáo khẳng định chấm điểm đã được kiểm chứng lại ở Tuần 3.

**Kế hoạch Tuần 4:**

- Kiểm thử tổng thể và tải 200 người dùng giả lập; ghi rõ cách giới hạn 10 Lambda đồng thời và đo `Throttles`/`ConcurrentExecutions`.
- Hoàn thiện xuất CSV kết quả lên S3 (nếu chưa triển khai); kiểm tra độ chính xác của dữ liệu.
- Đo metric thực tế và đối chiếu [dự toán chi phí Tuần 2](../week2/cost-estimation.md).
- Kiểm tra xử lý lỗi/retry SQS, dọn dẹp tài nguyên và chuẩn bị video demo không quá 10 phút.

**Tài liệu liên quan:** [Kết quả kiểm thử](week3-test-results.md)
