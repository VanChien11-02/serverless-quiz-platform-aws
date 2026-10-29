# Tuần 4 – Kết quả kiểm thử thực tế

**Đề tài:** Nền tảng thi trắc nghiệm trực tuyến Serverless (Capstone)  
**Region:** `us-east-1`  
**Nguồn minh chứng:** thư mục `screenshots/week4/` trong bộ hồ sơ này.

## 1. Xuất CSV lên S3 và phân quyền

| ID | Kiểm thử | Kết quả quan sát được | Đánh giá | Minh chứng |
|---|---|---|---|---|
| W4-01 | Kiểm tra Lambda xuất báo cáo | AWS Console hiển thị function `quiz-export-report` tại `us-east-1`. | Đã xác minh function tồn tại | [01-export-lambda.png](../../screenshots/week4/01-export-lambda.png) |
| W4-02 | Admin gọi `POST /reports/export` | Postman trả `200 OK` sau khoảng `2.81 s`; response có `message=CSV export completed`, `examId=EXAM001`, `rows=3`, bucket `serverless-quiz-report-team-2026` và key `reports/EXAM001/results-20261028T033915Z-51a0bfbf.csv`. | Thành công theo response API | [02-export-api-admin-200.png](../../screenshots/week4/02-export-api-admin-200.png) |
| W4-03 | Student gọi `POST /reports/export` | Postman trả `403 Forbidden`, body `error=Admin role required`. | Có bằng chứng chặn theo role | [03-export-api-student-403.png](../../screenshots/week4/03-export-api-student-403.png) |
| W4-04 | Kiểm tra object trên S3 | Bucket hiển thị object CSV trong prefix `reports/EXAM001/`, dung lượng `522.0 B`, storage class `Standard`. | Object đã được tạo | [04-s3-csv-object.png](../../screenshots/week4/04-s3-csv-object.png) |
| W4-05 | Đọc nội dung CSV | Ảnh bảng tính hiển thị các cột `submissionId`, `examId`, `studentId`, `correctCount`, `totalQuestions`, `score`, `status`, `gradedAt`. | Nội dung CSV đọc được | [05-s3-csv-content.png](../../screenshots/week4/05-s3-csv-content.png) |

## 2. Kết quả Locust

| Virtual users | Requests | Failures | Failure rate | Current RPS | P95 (ms) | P99 (ms) | Average response (ms) | Minh chứng |
|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 10 | 110 | 0 | 0.00% | 4.1 | 3300 | 3900 | 764.53 | [06-locust-10.png](../../screenshots/week4/06-locust-10.png) |
| 50 | 700 | 50 | 7.14% | 7.9 | 3100 | 3200 | 591.92 | [07-locust-50.png](../../screenshots/week4/07-locust-50.png) |
| 100 | 1400 | 100 | 7.14% | 7.5 | 3100 | 3200 | 589.02 | [08-locust-100.png](../../screenshots/week4/08-locust-100.png) |
| 200 | 2792 | 194 | 6.95% | 9.6 | 3200 | 3300 | 577.07 | [09-locust-200.png](../../screenshots/week4/09-locust-200.png) |

Công thức `Failure rate = Failures / Requests × 100%`. Tỷ lệ được tính từ hàng `Aggregated` trong từng ảnh.

### Phân tích mức 200 virtual users

Ảnh thống kê Locust cho thấy các request sau:

| Endpoint | Requests | Failures | P95 (ms) | Average (ms) | Nhận xét |
|---|---:|---:|---:|---:|---|
| `GET /exams [E2E]` | 200 | 0 | 410 | 394.50 | Không có failure trong snapshot |
| `POST /auth/login` | 200 | 0 | 3400 | 3212.59 | Đây là endpoint có độ trễ cao nhất trong các endpoint được liệt kê |
| `POST /exams/{id}/start` | 200 | 0 | 440 | 399.64 | Không có failure trong snapshot |
| `POST /submissions/{id}/submit` | 200 | 0 | 460 | 400.41 | Không có failure trong snapshot |
| `GET /submissions/{id}/result` | 1992 | 194 | 390 | 366.35 | Các failure được báo là chưa thấy `COMPLETED` trong cửa sổ polling 20 giây |

- [10-locust-charts.png](../../screenshots/week4/10-locust-charts.png): biểu đồ requests và response time.
- [11-locust-failures.png](../../screenshots/week4/11-locust-failures.png): thông báo lỗi polling kết quả.
- [09-locust-200.png](../../screenshots/week4/09-locust-200.png): thống kê tại snapshot mức 200 VU.

## 3. DynamoDB sau kiểm thử tải

Ảnh Explore items cho bảng `Submissions` báo `Items returned (2)`. Hai dòng hiển thị `examId=EXAM001`; `correctCount` nhìn thấy lần lượt là `2` và `0`.

- Minh chứng: [12-dynamodb-submissions-after-load.png](../../screenshots/week4/12-dynamodb-submissions-after-load.png)

## 4. Quota, concurrency và throttling

| Hạng mục | Giá trị nhìn thấy | Kết luận đúng theo minh chứng |
|---|---|---|
| Account Lambda quota | `ConcurrentExecutions=400`, `UnreservedConcurrentExecutions=400`; `FunctionCount=12` | Quota tài khoản là 400, không phải 10 |
| `quiz-export-report` concurrency | `Use unreserved account concurrency`; `Unreserved account concurrency=400` | Ảnh không cho thấy Reserved Concurrency bằng 10 trên function này |
| CloudWatch `ConcurrentExecutions` | Tooltip hiển thị `1` tại `2026-10-29 03:35 UTC` | Có một điểm đo bằng 1 trong khoảng thời gian đang xem |
| CloudWatch `Throttles` | Tooltip hiển thị `0` tại `2026-10-29 04:00 UTC` | Không quan sát thấy throttle tại điểm đo này |

Minh chứng: [13-lambda-account-quota.png](../../screenshots/week4/13-lambda-account-quota.png), [14-lambda-concurrency-config.png](../../screenshots/week4/14-lambda-concurrency-config.png), [15-cloudwatch-concurrent-executions.png](../../screenshots/week4/15-cloudwatch-concurrent-executions.png), [16-cloudwatch-throttles.png](../../screenshots/week4/16-cloudwatch-throttles.png).

## 5. Chi phí và cleanup

- [17-cost-report.png](../../screenshots/week4/17-cost-report.png) cho thấy trang Billing and Cost Management có biểu đồ chi phí theo tháng. Các nhãn hiển thị làm tròn về `$0.00`; ảnh không có số chi phí chính xác theo dịch vụ hoặc bộ lọc riêng cho project. Vì vậy không thể dùng ảnh này để báo cáo một tổng chi phí thực tế cụ thể.

