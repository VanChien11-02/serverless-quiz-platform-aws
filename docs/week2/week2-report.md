## Tuần 2 – Triển khai các chức năng lõi (Core Functions Implementation)

**Môi trường:** AWS Academy Learner Lab  
**Region:** us-east-1 (N. Virginia)  
**Trạng thái:** Đã triển khai và kiểm thử thành công các chức năng lõi.

### 1. Các chức năng đã triển khai (Completed Features)

Trong Tuần 2, hệ thống được phát triển dựa trên kiến trúc Serverless đã thiết kế ở Tuần 1, tập trung xây dựng các API phục vụ quá trình tạo đề thi, làm bài và chấm điểm tự động.

Các chức năng đã thực hiện:

- **Quản lý đề thi (Exam Management):** Xây dựng API tạo đề thi, thêm câu hỏi, lấy danh sách và thông tin đề thi bằng AWS Lambda kết hợp DynamoDB.
- **Bắt đầu bài thi (Start Exam):** Tạo lượt thi mới, xáo trộn thứ tự câu hỏi (Question Randomization) và trả về nội dung bài thi cho thí sinh.
- **Giới hạn thời gian (Time Limit):** Kiểm tra thời gian làm bài phía Backend, từ chối nộp bài khi hết thời gian.
- **Nộp bài (Submit Exam):** Tiếp nhận câu trả lời, lưu thông tin bài làm vào bảng `Submissions` và đưa yêu cầu chấm điểm vào Amazon SQS.
- **Chấm điểm tự động (Auto Grading):** Sử dụng Grading Lambda được kích hoạt bởi SQS để chấm điểm bất đồng bộ (Asynchronous Processing).
- **Xem kết quả (Get Result):** Truy xuất số câu đúng, tổng số câu và điểm số từ DynamoDB.
- **Kiểm thử API (API Testing):** Kiểm thử từng chức năng bằng Postman và theo dõi quá trình thực thi thông qua AWS CloudWatch Logs.

### 2. Cơ sở dữ liệu DynamoDB

Hệ thống sử dụng 4 bảng DynamoDB đã được tạo trong Tuần 1 và tiếp tục khai thác trong Tuần 2.

| Table | Partition Key | Sort Key | Chức năng |
|---|---|---|---|
| Users | userId | — | Lưu thông tin người dùng |
| Exams | examId | — | Lưu thông tin đề thi |
| Questions | examId | questionId | Lưu ngân hàng câu hỏi |
| Submissions | submissionId | — | Lưu lượt thi, đáp án và kết quả |

### 3. Các API đã triển khai (API Endpoints)

| Method | Endpoint | Chức năng |
|---|---|---|
| GET | `/health` | Kiểm tra trạng thái API |
| POST | `/exams` | Tạo đề thi mới |
| GET | `/exams` | Lấy danh sách đề thi |
| GET | `/exams/{id}` | Lấy thông tin đề thi |
| POST | `/exams/{id}/questions` | Thêm câu hỏi vào đề |
| POST | `/exams/{id}/start` | Bắt đầu làm bài thi |
| POST | `/submissions/{id}/submit` | Nộp bài thi |
| GET | `/submissions/{id}/result` | Xem kết quả chấm điểm |

### 4. Quy trình hoạt động (System Workflow)

Hệ thống thực hiện quy trình thi trắc nghiệm và chấm điểm như sau:

1. Người dùng gửi request thông qua API Gateway.
2. API Gateway chuyển request đến AWS Lambda tương ứng.
3. Lambda truy vấn dữ liệu đề thi và câu hỏi từ DynamoDB.
4. Khi bắt đầu thi, Lambda xáo trộn thứ tự câu hỏi và tạo lượt thi trong bảng `Submissions`.
5. Khi thí sinh nộp bài, Lambda lưu đáp án và gửi message đến Amazon SQS.
6. SQS kích hoạt Grading Lambda để xử lý chấm điểm tự động.
7. Grading Lambda cập nhật điểm và trạng thái bài thi trong DynamoDB.
8. Người dùng gọi API Get Result để xem kết quả.

**Luồng xử lý chính:**

`API Gateway → AWS Lambda → DynamoDB → Amazon SQS → Grading Lambda → DynamoDB`

### 5. Kết quả kiểm thử (Testing Results)

Các API được kiểm thử bằng Postman và xác minh dữ liệu trên AWS.

**Kết quả kiểm thử End-to-End:**

| Thông tin | Kết quả |
|---|---|
| Exam ID | EXAM001 |
| Tổng số câu hỏi | 3 |
| Số câu trả lời đúng | 1 |
| Điểm số | 3.33/10 |
| Trạng thái | COMPLETED |
| Phương thức chấm điểm | Asynchronous Grading (SQS + Lambda) |

**Các trường hợp kiểm thử bổ sung:**

- Bắt đầu bài thi không tồn tại: hệ thống từ chối request.
- Nộp bài quá thời gian quy định: hệ thống từ chối xử lý.
- Gửi mã câu hỏi không hợp lệ: hệ thống trả về thông báo lỗi.
- Nộp lại bài đã hoàn thành: dữ liệu và điểm số không thay đổi.
- Kiểm tra trường hợp trả lời sai toàn bộ: điểm số được tính chính xác.
- Kiểm tra dữ liệu Start Exam: không trả về trường `correctAnswer`.

### 6. Bổ sung thêm tính năng theo nhận xét của GVHD

Dựa vào nhận xét

> "Thiết kế serverless tốt. Nhắc thêm cost estimation và security ở tuần 2."

#### 6.1. Bổ sung ước tính chi phí (Cost Estimation)

**Nội dung tiếp thu từ nhận xét GVHD:**

Em đã bổ sung việc tìm hiểu mô hình tính phí và phân tích các thành phần có thể phát sinh chi phí, bao gồm:

| Dịch vụ AWS | Yếu tố ảnh hưởng đến chi phí |
|---|---|
| API Gateway | Số lượng API requests |
| AWS Lambda | Số lần thực thi, memory và execution duration |
| DynamoDB | Số lượt đọc/ghi và dung lượng lưu trữ |
| Amazon SQS | Số lượng queue requests |
| Amazon CloudWatch | Logs, metrics và thời gian lưu trữ |
| Amazon S3 | Dung lượng lưu trữ và số lượng requests |

**Phương án ước tính:**

- Sử dụng AWS Pricing Calculator để xây dựng dự toán chi phí.
- Lấy Region `us-east-1` làm cơ sở tham khảo.
- Xây dựng kịch bản giả định với 200 người dùng để đánh giá khả năng phát sinh chi phí khi hệ thống có nhiều lượt thi.
- Phân biệt chi phí dự kiến với chi phí sử dụng thực tế trong AWS Learner Lab.
- Xem xét các biện pháp tối ưu như sử dụng kiến trúc Serverless, điều chỉnh cấu hình Lambda và dọn dẹp tài nguyên không sử dụng.

**Kết quả bổ sung:** em đã xác định được các thành phần phát sinh chi phí chính và xây dựng cơ sở để lập bảng dự toán. Kết quả ước tính chi tiết sẽ được cập nhật sau khi hoàn tất tính toán trên AWS Pricing Calculator.

[Cost estimation](cost-estimation.md)

#### 6.2. Bổ sung đánh giá bảo mật hệ thống (Security)

**Nội dung tiếp thu từ nhận xét GVHD:**

Em đã bổ sung và kiểm thử các cơ chế bảo vệ cơ bản sau:

| Nội dung bảo mật | Kết quả Tuần 2 |
|---|---|
| HTTPS Communication | Sử dụng HTTPS thông qua API Gateway |
| Input Validation | Kiểm tra dữ liệu đầu vào của API |
| Exam Time Validation | Xác minh thời hạn nộp bài tại Backend |
| Answer Protection | Không trả về `correctAnswer` khi bắt đầu thi |
| Duplicate Submission Protection | Không cho thay đổi kết quả bài thi đã hoàn thành |
| IAM Role | Sử dụng `LabRole` có sẵn trong Learner Lab |
| Error Monitoring | Sử dụng CloudWatch Logs để phát hiện và xử lý lỗi |

**Kết quả kiểm thử:**

- Hệ thống từ chối nộp bài khi quá thời gian quy định.
- Hệ thống phát hiện mã đề thi hoặc mã câu hỏi không hợp lệ.
- Đáp án đúng không xuất hiện trong dữ liệu trả về khi bắt đầu thi.
- Khi gửi lại bài đã chấm, kết quả và điểm số được giữ nguyên.
- Các lỗi phát sinh trong Lambda được kiểm tra thông qua CloudWatch Logs.

**Hạn chế và hướng cải thiện:**

Hiện tại, hệ thống mới triển khai các biện pháp bảo mật ở mức cơ bản, chưa hoàn thiện xác thực danh tính và phân quyền truy cập.

Trong Tuần 3, em dự kiến tiếp tục:

- Xây dựng JWT Authentication tự cài đặt, không sử dụng Cognito.
- Phân quyền Admin/Student bằng Role-Based Access Control (RBAC).
- Bảo vệ các API theo quyền của người dùng.
- Hoàn thiện cơ chế kiểm soát truy cập và giám sát bảo mật.

#### 6.3. Đánh giá kết quả tiếp thu nhận xét

Thông qua việc bổ sung Cost Estimation và Security trong Tuần 2, em không chỉ hoàn thành các chức năng lõi mà còn bước đầu xem xét hệ thống dưới góc độ **chi phí vận hành, tính an toàn và khả năng mở rộng**.

Việc tiếp thu nhận xét của GVHD giúp quá trình phát triển đồ án có định hướng rõ ràng hơn, đồng thời tạo nền tảng để tiếp tục hoàn thiện bảo mật, giám sát và tối ưu hệ thống trong Tuần 3 và Tuần 4.

[Security](security.md)

### 7. Công cụ và dịch vụ sử dụng (Technology Stack)

- **Cloud Platform:** AWS Academy Learner Lab
- **Backend:** Python, AWS Lambda, boto3
- **API Management:** Amazon API Gateway
- **Database:** Amazon DynamoDB
- **Message Queue:** Amazon SQS
- **Monitoring:** Amazon CloudWatch
- **API Testing:** Postman
- **Version Control:** Git, GitHub

### 8. Kết quả đạt được và hướng phát triển

Sau Tuần 2, hệ thống đã hoàn thành luồng xử lý chính của nền tảng thi trắc nghiệm trực tuyến trên AWS, từ khởi tạo đề thi đến tiếp nhận bài làm, chấm điểm tự động và trả kết quả.

Các chức năng lõi đã được triển khai và kiểm thử thực tế trên AWS Learner Lab.

**Kế hoạch Tuần 3:**

- Triển khai JWT Authentication tự cài đặt, không sử dụng Amazon Cognito.
- Xây dựng phân quyền Admin/Student (Role-Based Access Control).
- Hoàn thiện CloudWatch Monitoring.
- Bổ sung các biện pháp Security.
- Tìm hiểu và áp dụng Infrastructure as Code (IaC) nếu phù hợp.
