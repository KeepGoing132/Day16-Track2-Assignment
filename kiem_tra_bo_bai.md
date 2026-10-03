# Kiểm tra bộ bài theo README_aws.md

| Yêu cầu | Kết quả rà soát |
|---|---|
| Script huấn luyện LightGBM | Có; bản đã dùng cho kết quả cũ được giữ nguyên |
| Metrics JSON | Đủ 10 chỉ số yêu cầu, khớp log terminal |
| Dữ liệu thật | File CSV có 284.807 dòng, 31 cột, 492 mẫu gian lận; không thiếu giá trị |
| Ảnh benchmark | Có ảnh sẵn; chưa xác minh ảnh chụp trực tiếp |
| Ảnh CPU/RAM/Network | Có ảnh và log sau benchmark; không đo peak lúc huấn luyện |
| Ảnh Cost Explorer | Đã có ảnh người dùng cung cấp: Daily, Group by Service, không có bộ lọc; ngày 03/10 hiển thị $0.00, chưa có phân rã chi phí EC2/NAT/ALB |
| Mã Terraform nén | Có; chỉ chứa mã và file khóa phiên bản provider |
| Báo cáo ngắn 5–10 dòng | Có 8 nhận xét, giữ nguyên metric và sửa diễn giải |
| Dọn tài nguyên | Local state có 0 resources; API AWS tại ap-southeast-2 xác nhận không còn EC2 chưa kết thúc, EBS volume/snapshot sở hữu, Elastic IP hoặc Load Balancer; NAT deleted, không còn VPC AI-VPC |

## Chạy lại khi có yêu cầu

1. Dùng thư mục `terraform/`, tạo SSH key riêng với tên `lab-key` và public key `lab-key.pub`.
2. Cấu hình AWS bằng credential CSV riêng ở thư mục Track2. Không chép khóa vào mã nguồn hoặc gói nộp.
3. Cấu hình mặc định hiện là `ap-southeast-2`, CPU `t3.micro`; khác hướng dẫn mẫu `us-east-1` / `t3.medium`. Xác nhận quyền và cấu hình tài khoản trước khi tạo lại tài nguyên.
4. Sau khi triển khai, kết nối compute node trực tiếp qua SSH ProxyJump từ máy local hoặc SSH agent forwarding phù hợp; câu lệnh SSH hai chặng trong README cần thêm cách cung cấp key cho chặng private.
5. Chép `benchmark.py` và CSV dữ liệu thật lên compute node, luôn truyền `--data-path` cụ thể. Ví dụ: `python3 benchmark.py --data-path /home/ubuntu/creditcard.csv --output /home/ubuntu/benchmark_result.json`.
6. Lưu ảnh chụp terminal thực tế, ảnh tài nguyên và Billing theo dịch vụ; sau đó dọn đúng tài nguyên bài bằng Terraform.

Lưu ý: script gốc có thể tự dùng dữ liệu mô phỏng khi không tìm thấy CSV và chạy không tương tác. Cần kiểm tra đường dẫn và `metadata.is_synthetic` trước khi dùng kết quả nộp bài. Script gốc chưa tách validation riêng; thay đổi phương pháp cần chạy lại và lưu bộ metric mới.

Báo cáo, ảnh Cost Explorer và gói nộp bài được cập nhật trực tiếp trong thư mục Day16 theo yêu cầu người dùng. Bộ này tổng hợp và chỉnh báo cáo từ kết quả có sẵn, không phải bằng chứng về một lần triển khai mới.
