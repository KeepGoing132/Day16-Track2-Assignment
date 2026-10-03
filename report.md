# Báo Cáo Kết Quả Thực Nghiệm Lab 16 — Huấn Luyện & Đo Lường Mô Hình ML Trên AWS

## 1. Thông tin cấu hình thực nghiệm
- **Hạ tầng Cloud**: AWS EC2 Private Compute Node (`t3.micro`, 1 vCPU, 1 GiB RAM ~ 914 MiB khả dụng trên Linux + 1 GiB Swap) nằm trong Private Subnet của VPC cách ly (`AI-VPC`), trung chuyển an toàn qua Bastion Host (`t3.micro`) tại Public Subnet.
- **Khu vực triển khai (AWS Region)**: `ap-southeast-2` (Sydney).  
  *Ghi chú xác minh cấu hình*: Mặc dù đề cương bài lab mẫu ban đầu đề xuất `us-east-1` và `t3.medium`, tài khoản phòng lab thuộc AWS Organization áp dụng chính sách SCP (`p-7pylswvc`) chặn khởi tạo tài nguyên ngoài vùng `ap-southeast-2` (báo lỗi `UnauthorizedOperation`), đồng thời áp dụng chính sách hạn chế loại máy chủ ngoài Free Tier (báo lỗi `InvalidParameterCombination` khi khởi tạo `t3.medium`). Do đó, thực nghiệm được cấu hình chuẩn xác và thực thi thành công trên `t3.micro` tại `ap-southeast-2`.
- **Hệ điều hành & Môi trường**: Ubuntu Linux 22.04 LTS (Kernel `6.8.0-1066-aws`, x86_64), Python 3.10.12, LightGBM 4.7.0, Scikit-learn 1.7.2, Pandas 2.3.3, NumPy 2.2.6.
- **Tập dữ liệu**: Bộ dữ liệu thực tế **Credit Card Fraud Detection** từ Kaggle (`creditcard.csv`, kích thước 150.8 MB).
  - Tổng số bản ghi: **284,807 dòng**, 31 cột (Time, V1–V28 PCA, Amount, Class).
  - Phân bố nhãn: 284,315 giao dịch hợp lệ (99.827%) và 492 giao dịch gian lận (0.173%).
  - Tập huấn luyện (Train set - 80% stratify): **227,845 mẫu**
  - Tập kiểm thử (Test set - 20% stratify): **56,962 mẫu**

---

## 2. Bảng tổng hợp số liệu Benchmark thực tế (Khớp với `benchmark_result.json`)

| Chỉ số (Metric) | Kết quả đo được | Đánh giá kỹ thuật |
| :--- | :--- | :--- |
| **Thời gian nạp dữ liệu (Load data)** | `2.5745 s` | Nạp và parse 284,807 dòng CSV từ ổ đĩa gp3 EBS vào bộ nhớ RAM |
| **Thời gian huấn luyện (Training time)** | `1.8747 s` | LightGBM tối ưu thuật toán Histogram song song trên CPU |
| **Số vòng lặp tối ưu (Best iteration)** | `1` | Early stopping kích hoạt do phân bố PCA phân tách lớp rất mạnh ngay cây đầu tiên |
| **AUC-ROC** | `0.95165` | Khả năng phân loại và tách biệt gian lận đạt mức xuất sắc (> 0.95) |
| **Độ chính xác (Accuracy)** | `0.99895` (99.89%) | Phản ánh tính chất tập dữ liệu có độ mất cân bằng lớp cực cao |
| **F1-Score** | `0.72727` | Điểm hài hòa giữa Precision và Recall trên bài toán gian lận thực tế |
| **Precision** | `0.65574` | Tỷ lệ dự báo đúng gian lận trong số các ca bị gắn cờ cảnh báo |
| **Recall** | `0.81633` | Phát hiện thành công hơn 81.6% tổng số các ca gian lận trong tập test |
| **Độ trễ suy luận đơn dòng (Single Latency)** | `1.236 ms` | Thời gian xử lý trung bình qua 200 lượt suy luận 1 giao dịch |
| **Thông lượng suy luận (Batch Throughput)** | `650,534 rows/s` | Gom batch 1,000 mẫu chỉ mất `1.54 ms` để xử lý xong toàn bộ |

---

## 3. Báo cáo nhận xét ngắn (5 - 10 dòng theo tiêu chí nộp bài)

1. **Về hiệu năng nạp dữ liệu và huấn luyện (Load & Training Time)**: Trên cấu hình máy chủ CPU tiết kiệm `t3.micro` (1 vCPU, 914 MiB RAM khả dụng), thời gian nạp bộ dữ liệu thực tế gần 285,000 dòng chỉ mất 2.57 giây và thời gian huấn luyện chỉ 1.87 giây, chứng tỏ LightGBM có cấu trúc dữ liệu nén Histogram cực kỳ nhẹ và tối ưu hóa vượt trội cho dữ liệu dạng bảng mà không đòi hỏi GPU đắt đỏ.
2. **Về chất lượng mô hình (AUC-ROC & Recall)**: Với tập dữ liệu thực có mức độ mất cân bằng nghiêm trọng (chỉ 0.173% gian lận), mô hình đạt diện tích dưới đường cong ROC xuất sắc (`AUC = 0.95165`) và độ nhạy `Recall = 81.63%`, giúp nhận diện phần lớn các hành vi lừa đảo mà vẫn duy trì độ chính xác tổng thể 99.89%.
3. **Về tốc độ suy luận (Inference Latency & Throughput)**: Tốc độ chấm điểm đơn dòng đạt trung bình `1.236 ms` và thông lượng xử lý theo lô đạt hơn `650,000 dòng/giây` (1.54 ms cho 1,000 giao dịch). Mức thời gian đáp ứng ở tầng thuật toán này nằm trong ngưỡng khả thi cho các hệ thống chấm điểm gian lận trực tuyến (thường yêu cầu xử lý tổng thể dưới 50–100 ms), tuy nhiên khi triển khai production thực tế cần tính toán thêm độ trễ truyền gói tin mạng (network round-trip) và cơ chế xác thực bảo mật.
4. **Về mức độ tiêu thụ tài nguyên phần cứng**: Dữ liệu giám sát thời gian thực qua lệnh `top` và `free -h` cho thấy tiến trình chỉ chiếm khoảng `205 MiB` RAM trên tổng số `914 MiB` bộ nhớ vật lý khả dụng (swap chỉ sử dụng 4 MiB), bộ nhớ đệm cache được giải phóng an toàn sau khi chạy, khẳng định kiến trúc hoàn toàn khả thi và vận hành ổn định trên các instance nhỏ nhất.
5. **Về an toàn hạ tầng và quản lý chi phí**: Toàn bộ luồng tính toán được cô lập trong Private Subnet sau Bastion Host và NAT Gateway. Sau khi thu thập đầy đủ minh chứng thực nghiệm, lệnh dọn dẹp `terraform destroy` được thực thi để hủy toàn bộ tài nguyên (EC2, VPC, NAT Gateway, ALB), đảm bảo chi phí phát sinh trong phiên thực hành ngắn duy trì ở mức tối thiểu (ước tính dưới $0.05 - $0.10 theo đơn giá On-Demand).

---

## 4. Danh sách tệp nộp bài đính kèm
- `screenshot_benchmark.png`: Ảnh chụp màn hình terminal chạy `python3 benchmark.py` với tập dữ liệu Kaggle thực tế.
- `benchmark_result.json`: File metrics kết quả benchmark chính thức tải về từ máy chủ AWS EC2 (`is_synthetic: false`).
- `screenshot_resources.png`: Ảnh chụp màn hình terminal kiểm tra tài nguyên thực tế (`top`, `free -h`, `ip -s link`).
- `screenshot_billing.png`: Ảnh chụp màn hình giao diện AWS Billing / Cost Management Dashboard.
- `terraform.zip`: Toàn bộ mã nguồn Terraform triển khai hạ tầng.
- `report.md`: Báo cáo kết quả thực nghiệm chi tiết này.
