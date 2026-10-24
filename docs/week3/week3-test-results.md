# Tuần 3 – Kết quả kiểm thử JWT, phân quyền và tích hợp (Test Results)

> **Trạng thái:** Bảng kiểm thử dựa trên API, mã nguồn và quá trình thực hành đã trao đổi. Mục nào thiếu response/ảnh từ lần chạy cuối phải đối chiếu và cập nhật trước khi nộp. **Chưa kiểm thử tải 200 người dùng đồng thời** trong Tuần 3.

## 1. Mục tiêu và phạm vi

Tiếp nối [kết quả Tuần 2](../week2/week2-test-results.md), Tuần 3 xác minh:

- Người dùng đăng ký/đăng nhập và nhận JWT có chữ ký, role, thời gian hết hạn.
- API Gateway chặn request thiếu JWT hoặc dùng JWT sai/hết hạn.
- Lambda phân quyền đúng Admin/Student trên từng API, không phụ thuộc role do client tự khai báo.
- Student chỉ được nộp và xem kết quả `submissionId` thuộc sở hữu của mình.
- Luồng Start → Submit → SQS → Grading → Get Result vẫn hoạt động sau khi bổ sung phân quyền.
- CloudWatch ghi nhận các lần gọi và hỗ trợ chẩn đoán lỗi.

**Môi trường:** AWS Academy Learner Lab, Region `us-east-1`; dùng Postman và AWS Console. **Bộ test:** `postman/week3-jwt-rbac.postman_collection.json`.

## 2. Danh sách API và phân quyền kỳ vọng

| Method | Endpoint | Không token | Admin | Student |
|---|---|---|---|---|
| POST | `/auth/register` | Cho phép đăng ký Student | Cho phép đăng ký Student | Cho phép đăng ký Student |
| POST | `/auth/login` | Cho phép đăng nhập | `200` nếu hợp lệ | `200` nếu hợp lệ |
| GET | `/exams` | Bị từ chối | `200` | `200` |
| GET | `/exams/{id}` | Bị từ chối | `200` | `200` |
| POST | `/exams` | Bị từ chối | `201` | **`403`** |
| POST | `/exams/{id}/questions` | Bị từ chối | `201` | **`403`** |
| POST | `/exams/{id}/start` | Bị từ chối | **`403`** | `201` |
| POST | `/submissions/{id}/submit` | Bị từ chối | **`403`** | `202` |
| GET | `/submissions/{id}/result` | Bị từ chối | **`403`** | `200` nếu là chủ bài |

Các mã thành công áp dụng khi request/dữ liệu hợp lệ. Trường hợp không token có thể trả `401` hoặc `403` tùy phản hồi của API Gateway/Authorizer; quan trọng là request **không được thực hiện thành công**.

## 3. Kết quả các trường hợp kiểm thử

**Quy ước:**

- **Đã trao đổi:** chức năng đã được người thực hiện mô tả trong quá trình sửa lỗi; cần ảnh lần test cuối.
- **Cần đối chiếu:** thiếu ảnh hoặc log đủ để xác nhận status thực tế.
- Điền cột “Status thực tế” đúng giá trị Postman hiển thị trước khi nộp; không điền theo kỳ vọng.

| ID | Test case | Status | Ảnh minh chứng |
|---|---|---|---|
| T01 | Register Student hợp lệ | `201` | `03-register-student.png` |
| T02 | Login Student → nhận JWT có `role=Student` | `200` | Đã trao đổi, cần ảnh đã che token | `04-login-student.png` |
| T03 | Login Admin → role Admin | `200` | `05-login-admin.png` |
| T04 | Đăng ký công khai với `role=Admin` | `400` | `06-reject-admin-registration.png` |
| T05 | Student tạo đề `POST /exams` | `403` | `07-student-create-exam-403.png` |
| T06 | Student thêm câu hỏi | `403` | `08-student-add-question-403.png` |
| T07 | Admin tạo đề hợp lệ | `201` | `09-admin-create-exam-201.png` |
| T08 | Admin Start Exam | `403` | `10-admin-start-403.png` |
| T09 | Admin Submit Exam | `403` | `11-admin-submit-403.png` |
| T10 | Admin Get Result | `403` | `12-admin-result-403.png` |
| T11 | Gọi `GET /exams` không token | `403` | `13-no-token-denied.png` |
| T12 | JWT sai chữ ký/cấu trúc | `403` | `13b-invalid-jwt-denied.png` |
| T13 | JWT có hiệu lực **trước thời điểm hết hạn** | `200` | `14a-token-valid-before-expiry.png` |
| T14 | **Cùng JWT đã hết hạn** gọi lại API | `403` | `14-expired-jwt-denied.png` |
| T15 | Student B xem kết quả Student A | `403` | `15-other-student-result-403.png` |
| T16 | Student Start Exam hợp lệ | `201` | `16-student-start-201.png` |
| T17 | Student Submit hợp lệ | `202` | `17-student-submit-202.png` |
| T18 | SQS kích hoạt Grading Lambda | Có event và xử lý | `18-sqs-grading-trigger.png` |
| T19 | Get Result sau chấm | `200`, `COMPLETED`, có `score` | `19-result-completed.png` |


## 4. Negative Test bắt buộc: JWT hết hạn

Theo góp ý GVHD, cần chứng minh token **đã từng dùng được**, rồi mới hết hạn và bị chặn. Không đủ nếu chỉ gửi token sai định dạng.

**Các bước:**

1. Trên Auth Lambda, tạm đổi `JWT_TTL_SECONDS` thành `30`, tắt authorizer caching.
2. Login Student để nhận token mới `token_A` (không đưa token vào báo cáo).
3. Gọi `GET /exams` với `token_A` ngay sau login: kỳ vọng `200`.
4. Để quá thời gian hết hạn theo `exp`, gọi lại chính `token_A`: kỳ vọng `401` hoặc `403`, tuyệt đối không phải `200`.
5. Chụp `14a-token-valid-before-expiry.png` và `14-expired-jwt-denied.png`; che Bearer token, thể hiện status và thời gian.
6. Khôi phục TTL về `3600`, đăng nhập mới và kiểm tra lại luồng bình thường.

Có thể gắn Postman test:

```javascript
pm.test("Expired JWT is rejected", function () {
    pm.expect([401, 403]).to.include(pm.response.code);
});
```

## 5. Lỗi gặp phải, cách xử lý và kết luận

| Lỗi/hiện tượng | Phân tích, hướng khắc phục |
|---|---|
| Auth Lambda báo `No module named 'lambda_function'` | Đồng bộ tên file `.py` với Runtime Handler; Deploy và Test lại |
| Auth Lambda timeout 3 giây | Điều chỉnh Timeout để debug; kiểm tra tài nguyên và kết nối DynamoDB/VPC nếu còn timeout |
| Student có JWT nhưng tạo đề được `201` | Kiểm tra Authorization header Postman; bổ sung kiểm tra vai trò trong Exam Lambda |
| Admin có JWT nhưng Start/Submit/Result vẫn thành công | Bổ sung kiểm tra `role=Student` trong Attempt Lambda và kiểm tra JWT context |
| Get Result trả `200` nhưng `SUBMITTED` | Cần xem trigger SQS, lỗi Grading Lambda, message backlog hoặc quyền DynamoDB; không xem là chấm xong |

**Kết luận:** Tuần 3 tập trung đưa xác thực JWT và RBAC vào API đang hoạt động. Các trường hợp **bị từ chối quyền** có thể kiểm chứng độc lập trên Postman với mã `403`, còn token hết hạn cần một cặp thử trước/sau thời hạn. **Bảng này được thiết kế để ghi kết quả thật, không thay thế ảnh minh chứng.** Bài test tải 200 người dùng và đo throttling theo giới hạn 10 Lambda thuộc Tuần 4.

**Tài liệu liên quan:** [Báo cáo Tuần 3](week3-report.md)
