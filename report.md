# Báo Cáo Kết Quả Thực Nghiệm Lab 16 — Huấn Luyện & Đo Lường Mô Hình ML Trên AWS

## 1. Thông tin cấu hình thực nghiệm
- **Hạ tầng Cloud**: AWS EC2 Private Compute Node (`t3.medium`, 2 vCPU, 4GB RAM) nằm an toàn trong Private Subnet của VPC chuyên biệt (AI VPC).
- **Hệ điều hành**: Ubuntu Linux (Kernel `6.8.0-1066-aws`, x86_64), Python 3.10.12, LightGBM 4.7.0.
- **Tập dữ liệu**: Mô phỏng Credit Card Fraud Detection (chuẩn 284,807 dòng, 30 features, tỉ lệ mất cân bằng nhãn 0.171%).
  - Tập huấn luyện (Train set): 227,845 mẫu
  - Tập kiểm thử (Test set): 56,962 mẫu

---

## 2. Bảng tổng hợp số liệu Benchmark

| Chỉ số (Metric) | Kết quả đo được | Đánh giá |
| :--- | :--- | :--- |
| **Thời gian nạp dữ liệu (Load data)** | `0.2857 s` | Nạp cực nhanh, dữ liệu lưu trữ trực tiếp trên EBS |
| **Thời gian huấn luyện (Training time)** | `2.4248 s` | LightGBM tối ưu thuật toán Histogram trên CPU |
| **Số vòng lặp tối ưu (Best iteration)** | `7` | Mô hình sớm hội tụ trên tập xác thực |
| **AUC-ROC** | `0.82986` | Khả năng phân loại gian lận đạt mức tốt (> 0.8) |
| **Độ chính xác (Accuracy)** | `0.99821` (99.82%) | Phản ánh đặc trưng tập dữ liệu mất cân bằng cao |
| **F1-Score** | `0.48485` | Trung bình điều hòa giữa Precision và Recall |
| **Precision / Recall** | `0.47525` / `0.49485` | Đạt độ cân bằng hợp lý khi phát hiện giao dịch bất thường |
| **Độ trễ suy luận đơn dòng (Single Latency)** | `1.185 ms` | Phục vụ tốt hệ thống chấm điểm gian lận thời gian thực |
| **Thông lượng suy luận (Batch Throughput)** | `669,431 rows/s` | Thời gian xử lý batch 1,000 mẫu chỉ mất `1.49 ms` |

---

## 3. Báo cáo nhận xét ngắn (5 - 10 dòng theo tiêu chí nộp bài)

1. **Về thời gian huấn luyện (Training time)**: Trên cấu hình CPU của instance `t3.medium` (2 vCPU), thời gian huấn luyện chỉ mất 2.42 giây cho gần 230,000 bản ghi, chứng minh LightGBM có khả năng tối ưu hóa tính toán ma trận trên CPU cực kỳ hiệu quả mà không nhất thiết phải đầu tư GPU đắt đỏ cho dạng dữ liệu bảng (tabular data).
2. **Về độ chính xác và AUC-ROC**: Chỉ số AUC-ROC đạt xấp xỉ 0.83 và Accuracy đạt 99.82% trên tập dữ liệu gian lận có tỷ lệ nhãn dương chỉ 0.17%, cho thấy mô hình học được ranh giới quyết định khả quan chỉ sau 7 vòng lặp lặp sớm (early stopping).
3. **Về tốc độ suy luận (Inference Speed)**: Độ trễ dự đoán từng dòng (single-row latency) chỉ 1.185 ms, hoàn toàn đáp ứng SLA khắt khe của các cổng thanh toán ngân hàng trực tuyến; khi gom theo batch 1,000 dòng, thông lượng đạt tới xấp xỉ 670,000 dòng/giây (1.49 ms).
4. **Về quản lý tài nguyên và chi phí**: Giám sát bằng lệnh `top` và `free -h` cho thấy ứng dụng hoạt động êm ái, chỉ sử dụng khoảng ~194MB RAM trên tổng số 914MB khả dụng, CPU tải tức thời và nhanh chóng trở về mức nhàn rỗi (idle 96.8%).
5. **Tổng kết kiến trúc hạ tầng**: Toàn bộ luồng dữ liệu và node tính toán được bảo vệ an toàn trong Private Subnet sau Bastion Host và NAT Gateway, toàn bộ tài nguyên đã được tự động dọn dẹp sạch bằng `terraform destroy` nhằm tối ưu chi phí học tập dưới $0.15.

---

## 4. Danh sách tệp nộp bài đính kèm
- `screenshot_benchmark.png`: Ảnh chụp màn hình terminal chạy `python3 benchmark.py`.
- `benchmark_result.json`: File metrics kết quả benchmark tải từ AWS EC2.
- `screenshot_resources.png`: Ảnh chụp màn hình kiểm tra tài nguyên (`top`, `free -h`, `ip -s link`).
- `screenshot_billing.png`: Ảnh chụp màn hình AWS Billing / Cost Dashboard.
- `terraform.zip`: Toàn bộ mã nguồn Terraform triển khai hạ tầng.
- `report.md`: Báo cáo nhận xét thực nghiệm này.
