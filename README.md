# Vuahem (vuahem.lol)

> Rà soát rủi ro hóa đơn đầu vào trước khi nộp tờ khai thuế GTGT.

Vuahem là giải pháp đối soát và phát hiện rủi ro hóa đơn điện tử đầu vào dành cho Kế toán trưởng, CFO và chủ doanh nghiệp tại Việt Nam:
1. **Kiểm tra trạng thái người bán**: Đối chiếu tức thì với danh mục NNT ngừng hoạt động, bỏ địa chỉ kinh doanh, đóng MST từ cơ quan thuế.
2. **So khớp thời điểm phát hành**: Cảnh báo các hóa đơn xuất sau ngày cơ quan thuế ra thông báo vi phạm.
3. **3-Way Reconciliation**: Đối chiếu 3 chiều giữa Hóa đơn XML ↔ Sao kê Ngân hàng (Ủy nhiệm chi) ↔ Phiếu nhập kho/Hợp đồng. Phát hiện chi tiền mặt vượt ngưỡng quy định.

---

## Kiến Trúc Hệ Thống (3-Way Audit Engine)

![Vuahem Architecture](assets/vuahem_diagram.png)

---

## Cấu Trúc Dự Án

Dự án được thiết kế dạng **single-file web page** không phụ thuộc build tooling phức tạp, tối ưu hóa tốc độ tải và khả năng triển khai:

- `index.html`: Landing page hoàn chỉnh (thiết kế theo ngôn ngữ cinematic black & cream/mint của Shopifi, kiểu chữ Grotesk nét thanh, hệ thống nút bấm dạng pill).
- `check_design.py`: Bộ kiểm tra tuân thủ thiết kế (9 tiêu chí: pill button geometry, canvas discipline, font scale, ss03, touch target floors).
- `verify.py`: Bộ kiểm thử nội dung và pháp lý (14 tiêu chí: quét từ cấm/hứa hẹn sai, kiểm tra liên kết anchor, đối soát logic demo).
- `BUILD_LOG.md`: Nhật ký phát triển và các vòng tự phản biện (self-critique) cùng mô hình Claude Opus & GPT-6.1-sol.
- `assets/`: Sơ đồ kiến trúc và ảnh xem trước giao diện.

---

## Chạy Thử Tại Local

Không cần cài đặt npm hay build step:

```bash
# Cách 1: Mở trực tiếp bằng trình duyệt
open index.html

# Cách 2: Chạy qua Python HTTP server
python3 -m http.server 8000
# Truy cập: http://localhost:8000
```

---

## Kiểm Tra Tự Động (Quality Gates)

Chạy các bài kiểm tra tự động trước khi triển khai:

```bash
# Kiểm tra quy chuẩn thiết kế
python3 check_design.py index.html

# Kiểm tra tính toàn vẹn nội dung & pháp lý
python3 verify.py index.html
```

---

## Bản Quyền & Trách Nhiệm

© 2026 Vuahem (vuahem.lol). Bản thử nghiệm kỹ thuật. Hệ thống cung cấp cảnh báo kỹ thuật hỗ trợ kế toán soát xét, không thay thế nghĩa vụ và kết luận của cơ quan thuế.
