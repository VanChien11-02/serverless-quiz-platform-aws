# Tuần 4 – Cost Audit và tối ưu tài nguyên

**Dự án:** Nền tảng thi trắc nghiệm trực tuyến serverless  
**Region triển khai:** `us-east-1`  
**Tài liệu tham chiếu:** `docs/week2/cost-estimation.md`  
**Minh chứng chi phí hiện có:** `screenshots/week4/17-cost-report.png`

## 1. Mục tiêu kiểm tra chi phí

Trong tuần 4, nhóm kiểm tra thông tin chi phí AWS và các số liệu sử dụng tài nguyên để đánh giá mức tiêu thụ của hệ thống thi trắc nghiệm. Việc kiểm tra gồm:

- Quan sát biểu đồ chi phí trong AWS Billing and Cost Management.
- Kiểm tra khả năng truy cập Cost Explorer và Cost Allocation Tags.
- Đối chiếu các số liệu vận hành hiện có của API Gateway, Lambda, DynamoDB, SQS, S3 và CloudWatch.
- So sánh số liệu có thể xác nhận với dự toán đã lập ở tuần 2.

## 2. Kết quả kiểm tra chi phí thực tế

### 2.1. Kết quả từ trang Billing and Cost Management

Ảnh `screenshots/week4/17-cost-report.png` thể hiện biểu đồ chi phí theo tháng từ May đến Oct 2026, được nhóm theo dịch vụ. Các nhãn chi phí hiển thị trên biểu đồ được làm tròn thành `$0.00`. Ảnh này không cung cấp bảng số liệu chi tiết hoặc tổng chi phí có thể xác định riêng cho dự án.

Vì vậy, biểu đồ trên **không đủ căn cứ để kết luận chi phí thực tế của dự án bằng `$0.00`**.

### 2.2. Giới hạn quyền truy cập Billing

Khi kiểm tra sâu hơn, tài khoản AWS Learner Lab hiển thị thông báo:

> You need permission

Điều này cho biết tài khoản sinh viên hiện tại không được cấp quyền xem thông tin Billing. Do đó, nhóm không thể tự mở các trang chi tiết hóa đơn để xác minh số tiền đã phát sinh.

Minh chứng: [Bill](../../screenshots/week4/18-billing-access-denied.png)

### 2.3. Giới hạn quyền truy cập Cost Allocation Tags

Khi truy cập Cost Allocation Tags, AWS hiển thị thông báo chức năng này được quản lý ở cấp **payer account**. Tài khoản Learner Lab của sinh viên không có quyền quản trị tài khoản thanh toán gốc để kích hoạt hoặc quản lý Cost Allocation Tags.

Vì vậy, nhóm chưa thể lọc và xác nhận chi phí riêng của dự án theo tag `Project`.

Minh chứng: [Allocation tags](../../screenshots/week4/19-cost-allocation-access-denied.png)

### 2.4. Kết luận về chi phí thực tế

Tại thời điểm lập báo cáo:

- **Chi phí AWS thực tế của riêng dự án:** Chưa xác minh được bằng tài khoản hiện tại.
- **Nguyên nhân:** Tài khoản Learner Lab không có quyền truy cập Billing; Cost Allocation Tags được quản lý ở cấp payer account.
- **Không kết luận chi phí thực tế bằng `$0.00`** chỉ dựa trên nhãn biểu đồ đã làm tròn hoặc màn hình không có dữ liệu.
- Cần quản trị viên/người quản lý payer account hỗ trợ trích xuất số liệu chi phí hoặc xác nhận số liệu chính thức.

## 3. Các số liệu sử dụng có thể xác nhận

Bảng dưới đây tổng hợp những số liệu đã có trong bộ minh chứng. Các số liệu này phản ánh từng ảnh chụp hoặc lần kiểm tra cụ thể, không mặc nhiên đại diện cho toàn bộ thời gian chạy dự án.

| Dịch vụ | Số liệu có trong bộ minh chứng | Giới hạn khi diễn giải |
|---|---|---|
| API Gateway / Locust | Các snapshot Locust lần lượt ghi nhận 110, 700, 1.400 và 2.792 requests ở các mức 10, 50, 100 và 200 VU | Đây là số request trong từng snapshot/test, không phải tổng request được AWS tính phí trong toàn kỳ |
| Lambda | Account quota `ConcurrentExecutions=400`; `FunctionCount=12`; function `quiz-export-report` sử dụng unreserved concurrency | Quota cấp tài khoản không chứng minh giới hạn concurrency 10 đã được cấu hình cho function. Bộ minh chứng hiện tại cũng chưa có tổng Invocations/Duration theo kỳ |
| DynamoDB | Ảnh scan bảng `Submissions` hiển thị `Items returned (2)` | Đây là số item trả về trong lần scan được chụp, không phải tổng lượt đọc/ghi hoặc tổng số bài thi |
| SQS | Chưa có số liệu `MessagesSent`, `MessagesReceived` hoặc `MessagesDeleted` trong bộ minh chứng đang tổng hợp | Chưa xác định được tổng khối lượng xử lý của hàng đợi |
| S3 | Object CSV được chụp có dung lượng `522.0 B` | Đây là kích thước của object CSV cụ thể, không phải tổng dung lượng bucket hoặc tổng dung lượng lưu trữ trong kỳ |
| CloudWatch | Có một điểm `ConcurrentExecutions=1` và một điểm `Throttles=0` trong khoảng thời gian được chụp | Hai số liệu tại một thời điểm không cùng cửa sổ thời gian với bài kiểm thử Locust nên không thể dùng để kết luận hệ thống không throttling khi chịu tải |

## 4. So sánh với dự toán tuần 2

Tài liệu dự toán tuần 2 (`docs/week2/cost-estimation.md`) nêu mức khoảng `0.0069 USD` cho một kịch bản giả định 200 lượt thi. Đây là **chi phí ước tính theo giả định**, không phải số tiền được xác nhận từ hóa đơn AWS.

Bản nháp trước có đề cập mức khoảng `0.01 USD` cho tuần 4. Tuy nhiên, do chưa truy cập được dữ liệu Billing chi tiết và chưa có bảng tính/nguồn đối chiếu xác nhận, con số này **không được sử dụng làm chi phí thực tế của dự án**.

| Khoản mục | Giá trị | Phân loại | Ghi chú |
|---|---:|---|---|
| Kịch bản 200 lượt thi theo dự toán tuần 2 | `~0.0069 USD` | Ước tính | Theo giả định trong tài liệu dự toán tuần 2 |
| Chi phí thực tế riêng của dự án trong tuần 4 | Chưa xác minh | Chưa có dữ liệu xác nhận | Billing bị từ chối quyền truy cập; cần quản trị viên hỗ trợ |
| Mức `~0.01 USD` trong bản nháp trước | Không dùng làm kết quả thực tế | Ước tính chưa được xác minh | Không có dữ liệu Billing chi tiết để đối chiếu |

## 5. Đánh giá tối ưu tài nguyên

Dựa trên bộ minh chứng hiện có, nhóm chỉ có thể xác nhận một số thông tin vận hành cụ thể như số request trong các snapshot Locust, số lượng function được ghi nhận, một lần scan DynamoDB trả về 2 item và object CSV có dung lượng 522 bytes.

Các thông tin này chưa đủ để tính mức tiết kiệm chi phí hoặc khẳng định chi phí đã giảm sau tối ưu. Để đánh giá chính xác hơn, cần có số liệu sử dụng theo cùng một khoảng thời gian, bao gồm:

- Lambda: `Invocations`, `Duration`, `Errors`, `Throttles` và concurrency trong thời gian kiểm thử.
- API Gateway: tổng request và lỗi trong cùng khoảng thời gian kiểm thử.
- DynamoDB: số liệu read/write capacity hoặc request thực tế theo cấu hình sử dụng.
- SQS: số message gửi, nhận, xóa và số message tồn đọng.
- S3: tổng dung lượng lưu trữ và số object liên quan đến dự án.

## 6. Minh chứng và giới hạn xác minh

| Minh chứng | Nội dung chứng minh |
|---|---|
| `screenshots/week4/17-cost-report.png` | Biểu đồ chi phí theo tháng; nhãn hiển thị đã được làm tròn, không đủ để xác định chi phí riêng của dự án |
| `screenshots/week4/18-billing-access-denied.png` | Tài khoản Learner Lab không có quyền xem thông tin Billing |
| `screenshots/week4/19-cost-allocation-access-denied.png` | Cost Allocation Tags được quản lý ở cấp payer account |
| `docs/week2/cost-estimation.md` | Dự toán chi phí theo kịch bản giả định của tuần 2 |
| `screenshots/week4/cleanup/` | Ảnh kiểm tra tài nguyên trong quá trình dọn dẹp; đối chiếu với trạng thái thực tế của từng dịch vụ |

## 7. Kiến nghị hỗ trợ xác minh chi phí

Do giới hạn quyền của Learner Lab, nhóm kính đề nghị giảng viên hoặc quản trị viên tài khoản hỗ trợ một trong các phương án sau:

1. Trích xuất chi phí theo tài khoản và khoảng thời gian triển khai dự án từ payer account.
2. Xác nhận số liệu chi phí thực tế được phép sử dụng trong báo cáo.
3. Hướng dẫn nguồn báo cáo ngân sách/chi phí chính thức dành cho sinh viên Learner Lab.

Nếu sử dụng số liệu Budget Usage trên trang AWS Academy Learner Lab, nhóm sẽ ghi rõ đó là **mức sử dụng ngân sách của Learner Lab**, không đồng nhất với hóa đơn AWS thực tế hoặc chi phí riêng của project.

## 8. Kết luận

Nhóm đã thực hiện kiểm tra biểu đồ chi phí và các số liệu sử dụng tài nguyên có trong bộ minh chứng. Tuy nhiên, do tài khoản Learner Lab không được cấp quyền truy cập Billing và không có quyền quản lý Cost Allocation Tags ở cấp payer account, nhóm chưa thể xác minh tổng chi phí AWS thực tế của riêng dự án.

Báo cáo phân biệt rõ số liệu vận hành đã quan sát, chi phí ước tính và chi phí thực tế chưa xác minh; không sử dụng giá trị hiển thị `$0.00` đã làm tròn để khẳng định dự án không phát sinh chi phí. Việc xác nhận chi phí cuối cùng cần được hỗ trợ từ quản trị viên hoặc người quản lý payer account.