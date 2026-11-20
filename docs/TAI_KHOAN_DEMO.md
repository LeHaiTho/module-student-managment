# Tài khoản demo và kịch bản trình diễn University SMS

Tài liệu đi kèm script `tools/seed_demo.py`. Toàn bộ dữ liệu là **hư cấu**
(tên giả, email `@demo.univ.test`, số điện thoại `09xx` giả, mã BHYT `DEMO-BHYT-…`).

## 1. Nạp dữ liệu demo

```bash
# Git Bash, tại thư mục gốc repo. <db> là database đã cài đủ 16 module univ_sms_*.
MSYS_NO_PATHCONV=1 docker compose run --rm -T odoo odoo shell \
    -c /etc/odoo/odoo.conf -d <db> --no-http < tools/seed_demo.py
```

* Chạy lại bao nhiêu lần cũng được: không sinh bản ghi trùng, không xóa dữ liệu
  có sẵn, **đặt lại mật khẩu** các tài khoản demo về `Demo@2026`.
* Ngày tháng tính theo ngày chạy: học kỳ hiện tại là học kỳ chứa hôm nay
  (HK1: 01/09–15/01, HK2: 16/01–30/06, hè: 01/07–31/08), học kỳ trước đã có điểm.
* Cuối script in bảng số lượng bản ghi và danh sách cảnh báo của sv01–sv12.
  Dòng `Lỗi: 0` nghĩa là mọi phần đều chạy được.
* Trên server deploy: đặt `web.base.url` (Thiết lập → Tham số hệ thống) là URL
  công khai **trước** khi demo QR, vì mã QR chứa URL này.
* Lưu ý bảo mật cho bản demo công khai: module `univ_sms_base` còn tạo sẵn các tài
  khoản cũ `giangvien`, `phongdaotao`, `sinhvien`, `covanht`, `truongkhoa` với mật
  khẩu trùng tên đăng nhập (`univ_sms_base/data/demo_users.xml`). Hãy lưu trữ
  (archive) hoặc đổi mật khẩu các tài khoản này trước khi mở cho người ngoài.

Số liệu sau khi chạy trên DB mới (lần 1 và lần 2 giống nhau): 112 sinh viên,
4 lớp hành chính, 20 lớp học (7 lớp học kỳ trước, 13 lớp học kỳ hiện tại),
13 lớp môn học, 2 đợt đăng ký, 527 đăng ký, 1 người trong danh sách chờ,
101 phiếu điểm danh (100 đã xác nhận, 1 nháp hôm nay), 5.453 dòng điểm danh,
15 kỳ thi, 1.120 kết quả thi, 112 bảng điểm, 224 khoản học phí, 181 hóa đơn,
10 cảnh báo sớm.

## 2. Bảng tài khoản

Mật khẩu chung: **`Demo@2026`**. Đăng nhập tại `/web/login`. Tài khoản sinh viên
tự chuyển sang cổng `/my/academic`.

### 2.1 Cán bộ, giảng viên (giao diện quản trị)

| Tên đăng nhập | Vai trò (nhóm quyền) | Người dùng | Dùng để thử |
|---|---|---|---|
| `admin.demo` | Quản trị viên SMS (không phải quản trị Odoo) | Lê Minh Quân | Xem toàn bộ dữ liệu, dashboard, cấu hình danh mục |
| `daotao.demo` | Cán bộ Phòng Đào tạo | Trần Thị Hồng | Đợt đăng ký, lớp môn học, danh sách chờ, đưa phiếu điểm danh về nháp, cảnh báo sớm (thấy tất cả), chạy đánh giá cảnh báo |
| `taichinh.demo` | Phòng Tài chính - Kế toán | Phạm Văn Tài | Học phí, hóa đơn, khoản nợ quá hạn của sv09 |
| `ctsv.demo` | Phòng Công tác Sinh viên | Nguyễn Thị Thu | Giấy chứng nhận, BHYT, ngoại trú, nghĩa vụ quân sự, góp ý, khảo sát, cảnh báo sớm |
| `truongkhoa.demo` | Trưởng khoa (Khoa CNTT) | PGS.TS. Võ Thanh Bình | Duyệt cấp khoa điểm rèn luyện (phiếu sv02 đang chờ khoa duyệt) |
| `covan.demo` | Cố vấn học tập lớp **A** (DH20KTPM-A) và **D** (DH20CNTT-D) | ThS. Đặng Minh Châu | Chỉ thấy cảnh báo của sinh viên mình phụ trách (8 cảnh báo), ghi nhận tư vấn, đóng cảnh báo |
| `covan2.demo` | Cố vấn học tập lớp **B** (DH20CNTT-B) và **C** (DH20QTKD-C) | ThS. Hồ Thị Diễm | Đối chứng phân quyền: chỉ thấy 2 cảnh báo của lớp B |
| `giangvien.demo` | Giảng viên, dạy 3 lớp học kỳ hiện tại: Lập trình nâng cao, Cấu trúc dữ liệu và giải thuật, Cơ sở dữ liệu (Nhóm 1) | TS. Trần Minh Đức | Điểm danh QR (phiếu nháp hôm nay lớp CSDL Nhóm 1), xét điều kiện dự thi, nạp sinh viên vào kỳ thi |
| `giangvien2.demo` | Giảng viên các lớp khác (Mạng máy tính, CSDL Nhóm 2, Tiếng Anh 2 Nhóm 1, Trí tuệ nhân tạo, Marketing căn bản, …) | ThS. Nguyễn Thu Thảo | Đối chứng: không thấy lớp/phiếu của giangvien.demo; quét QR bằng tài khoản không phải sinh viên |

### 2.2 Sinh viên (cổng sinh viên)

Lớp hành chính A = DH20KTPM-A (cố vấn `covan.demo`), B = DH20CNTT-B (cố vấn `covan2.demo`).
Các lớp đã đăng ký ở Đợt 1 (đã đóng) của học kỳ hiện tại được ghi ở cột "Đang học".

| Tên đăng nhập | Họ tên | Lớp HC | Đang học (học kỳ hiện tại) | Kịch bản để thử |
|---|---|---|---|---|
| `sv01.demo` | Nguyễn Văn An | A | LTNC, CTDL, CSDL N1, HĐH, Tiếng Anh 2 N1 (14 TC) | Sinh viên "bình thường" để thử **mọi luồng đăng ký**: An toàn thông tin → thành công; Mạng máy tính → trùng lịch; CSDL Nhóm 2 → trùng môn; Tài chính doanh nghiệp → thiếu tiên quyết; Trí tuệ nhân tạo → vào danh sách chờ. Quét QR lớp CSDL N1 hôm nay |
| `sv02.demo` | Trần Thị Bình | A | Như sv01 + **Trí tuệ nhân tạo** (đăng ký ở Đợt 2) | Một trong 2 người giữ chỗ lớp AI (2 chỗ). Hủy đăng ký AI để sv04 được nhận tự động (AT05). Học phí đã đóng. Rèn luyện chờ khoa duyệt |
| `sv03.demo` | Lê Hoàng Cường | A | Như sv01 + Trí tuệ nhân tạo | Người thứ 2 giữ chỗ lớp AI. Học phí đã lập hóa đơn, chưa đóng (chưa quá hạn). Rèn luyện còn nháp. NVQS đã duyệt |
| `sv04.demo` | Phạm Thu Dung | A | Như sv01 | Đang ở **vị trí chờ số 1** lớp Trí tuệ nhân tạo |
| `sv05.demo` | Hoàng Minh Đức | A | Như sv01 | **GPA học kỳ trước 4,14 < 5** và trượt 3 môn → cảnh báo GPA + nợ môn. Rèn luyện bị trả về. BHYT năm trước đã hết hạn |
| `sv06.demo` | Vũ Thị Hà | A | Như sv01 | **Trượt 2 môn** (Toán rời rạc 4,0; Triết 4,5), GPA 6,07 → cảnh báo nợ môn, đã có 1 lần tư vấn của cố vấn (trạng thái Đang xử lý) |
| `sv07.demo` | Đặng Quốc Huy | A | CSDL N1, Mạng máy tính, HĐH, Tiếng Anh 2 N1 (11 TC) | **Trượt Lập trình cơ bản (3,3)** → đăng ký Lập trình nâng cao / CTDL bị từ chối vì thiếu tiên quyết |
| `sv08.demo` | Bùi Thanh Hương | A | Như sv01 | **Vắng 3/6 buổi (50%) lớp Cấu trúc dữ liệu** → không đủ điều kiện dự thi + cảnh báo chuyên cần |
| `sv09.demo` | Đỗ Văn Khánh | A | Như sv01 | **Nợ học phí học kỳ trước 7.000.000đ, quá hạn** → cảnh báo công nợ |
| `sv10.demo` | Ngô Thị Lan | A | Chỉ Hệ điều hành (3 TC) | **Đợt 1 chỉ đăng ký 3 TC < tối thiểu 10** → cảnh báo thiếu tín chỉ. Không học lớp CSDL N1 → quét QR lớp đó bị từ chối (AT07) |
| `sv11.demo` | Dương Văn Minh | B | Như sv01 | Dịch vụ sinh viên: 3 yêu cầu giấy chứng nhận (chờ duyệt / đã duyệt / hoàn thành), NVQS tạm hoãn đã nộp, BHYT chờ xác nhận, ở ký túc xá, góp ý mới, rèn luyện đã gửi |
| `sv12.demo` | Lý Thị Ngọc | B | Như sv01 | Sinh viên xuất sắc (GPA 9,23), học phí đã đóng, rèn luyện khoa đã duyệt, đã trả lời khảo sát đang mở |

100 sinh viên còn lại (MSSV `25<ngành>9101`…`25<ngành>9200`) không có tài khoản,
dùng cho số liệu dashboard. Trong đó 4 sinh viên lớp B, D vắng 2/6 buổi lớp Hệ điều hành.

### 2.3 Dữ liệu nền quan trọng

| Hạng mục | Nội dung |
|---|---|
| Khoa / bộ môn / ngành | FIT (Khoa CNTT, trưởng khoa `truongkhoa.demo`), FEB (Khoa Kinh tế); 3 bộ môn; 3 ngành KTPM, CNTT, QTKD |
| Môn tiên quyết | Lập trình nâng cao, CTDL&GT ← Lập trình cơ bản; Tiếng Anh 2 ← Tiếng Anh 1; Tài chính doanh nghiệp ← Nguyên lý kế toán; CNPM ← CTDL&GT; Web ← CSDL |
| Đợt 1 (đã đóng) | Đăng ký chính thức, tối thiểu 10 TC, tối đa 22 TC. Dùng cho cảnh báo thiếu tín chỉ |
| Đợt 2 (đang mở) | Đăng ký bổ sung, mở từ hôm-qua-3-ngày đến 14 ngày sau, tối thiểu 6, tối đa 20 TC. Cổng sinh viên dùng đợt này |
| Lớp đầy | Trí tuệ nhân tạo (Chuyên đề, 2 chỗ, Thứ Sáu 13:00-15:30): sv02, sv03 đã giữ chỗ, sv04 đang chờ |
| Trùng lịch có chủ ý | Mạng máy tính (Thứ Hai 08:00-10:30) trùng Lập trình nâng cao (Thứ Hai 07:00-09:30) |
| Trùng môn | Cơ sở dữ liệu có 2 nhóm (Nhóm 1 Thứ Tư, Nhóm 2 Thứ Sáu) |
| Lớp trống để thử | An toàn thông tin (2 TC, 40 chỗ, chưa ai đăng ký) |
| Điểm danh | 6 buổi đã xác nhận / lớp học kỳ hiện tại; phiếu **nháp hôm nay** lớp CSDL Nhóm 1 (giangvien.demo) |
| Kỳ thi | Học kỳ trước: giữa kỳ + cuối kỳ đã xong cho 7 lớp; học kỳ này: "Giữa kỳ - Cấu trúc dữ liệu" ở trạng thái Dự kiến (chưa nạp sinh viên) |
| Học phí | Học kỳ trước: đã đóng (trừ sv09). Học kỳ này: hạn 21 ngày sau ngày seed; một phần đã đóng, một phần đã lập hóa đơn, phần còn lại nháp |
| Khảo sát | "Đánh giá giảng dạy" đang mở (sv01 chưa trả lời → thử nộp); "Khảo sát cơ sở vật chất" học kỳ trước đã đóng |
| Thông báo | 3 đã đăng (1 ghim, 1 đã hết hạn nên sinh viên không thấy), 1 bản nháp |

## 3. Kịch bản demo trước hội đồng (AT01–AT14)

Chuẩn bị: hai cửa sổ trình duyệt (một cửa sổ thường cho cán bộ, một cửa sổ ẩn danh
cho sinh viên) và một điện thoại để quét QR. Nên chạy lại seed trước buổi demo để
mật khẩu và đợt đăng ký về đúng trạng thái.

### Phần A. Đăng ký môn thông minh (F1)

**AT01 – Đăng ký hợp lệ tạo ghi danh và cập nhật học phí**
1. Cửa sổ ẩn danh: đăng nhập `sv01.demo` → **Đăng ký môn** (`/my/academic/registration`).
2. Mở **Học phí** trước: học kỳ hiện tại 14 TC, 7.000.000đ (trạng thái Dự kiến).
3. Quay lại trang đăng ký, bấm đăng ký **An toàn thông tin (IT3104)** → "Đăng ký thành công".
4. Mở lại **Học phí**: 16 TC, 8.000.000đ. **Thời khóa biểu** có thêm buổi Thứ Bảy 13:00-15:00.
5. Cửa sổ cán bộ `daotao.demo` → ✍️ Đăng ký môn → 📝 Đăng ký môn học: thấy bản ghi mới của sv01.

**AT02 – Thiếu môn tiên quyết bị từ chối**
1. Đăng nhập `sv07.demo` → đăng ký **Lập trình nâng cao (IT2101)**.
2. Kết quả: "Chưa hoàn thành môn tiên quyết: Lập trình cơ bản." (sv07 được 3,3 điểm môn này ở học kỳ trước, xem **Bảng điểm**).
3. (Tùy chọn) `sv01.demo` đăng ký **Tài chính doanh nghiệp** → thiếu "Nguyên lý kế toán".

**AT03 – Trùng lịch bị từ chối, sĩ số không đổi**
1. `sv01.demo` đăng ký **Mạng máy tính (IT2104)** → "Trùng lịch với môn Lập trình nâng cao (Thứ Hai 07:00-09:30)".
2. Sĩ số lớp Mạng máy tính trên trang không tăng.
3. (Tùy chọn) đăng ký **Cơ sở dữ liệu Nhóm 2** → "Bạn đã đăng ký môn Cơ sở dữ liệu ở lớp khác trong học kỳ này."

**AT04 – Lớp đầy chuyển vào danh sách chờ, có vị trí**
1. Lớp **Trí tuệ nhân tạo** hiển thị "2/2 · còn 0 chỗ · 1 người chờ".
2. `sv01.demo` bấm đăng ký → "Lớp đã đủ chỗ. Bạn đang ở vị trí chờ số 2."
3. `daotao.demo` → ✍️ Đăng ký môn → ⏳ Danh sách chờ: sv04 vị trí 1, sv01 vị trí 2.

**AT05 – Hủy đăng ký tự động nhận người chờ đầu tiên**
1. Đăng nhập `sv02.demo` → trang đăng ký → hủy lớp **Trí tuệ nhân tạo** (đăng ký ở Đợt 2 nên được phép hủy).
2. Đăng nhập `sv04.demo` → lớp AI chuyển sang "Đã đăng ký" (thông báo cá nhân "Đã được nhận vào lớp môn…" được tạo cho sv04).
3. `daotao.demo` → Danh sách chờ: bản ghi của sv04 ở trạng thái "Đã được nhận"; sv01 lên vị trí 1.

### Phần B. Điểm danh QR và điều kiện dự thi (F2)

**AT06 – Quét mã hợp lệ, sinh viên trong lớp được ghi Có mặt**
1. Cửa sổ cán bộ: đăng nhập `giangvien.demo` → ✅ Điểm danh → mở phiếu **"Cơ sở dữ liệu (Nhóm 1) - <ngày hôm nay>"** (trạng thái Nháp).
2. Bấm **Bắt đầu điểm danh QR** → mã QR hiện trên màn hình (hiệu lực tối đa 10 phút).
3. Điện thoại: đăng nhập `sv01.demo`, quét mã → "Điểm danh thành công: bạn được ghi nhận Có mặt".
4. Trên phiếu: dòng của sv01 nguồn "Quét QR", có giờ check-in; sinh viên chưa quét mặc định Vắng.

**AT07 – Tài khoản ngoài lớp bị từ chối**
1. Quét cùng mã bằng `sv10.demo` (không học lớp này) → "Bạn không có tên trong danh sách lớp này…".
2. (Tùy chọn) quét bằng `giangvien2.demo` → "Tài khoản này không phải tài khoản sinh viên…".

**AT08 – Mã hết hạn bị từ chối**
1. Chờ quá 10 phút, hoặc bấm **Tạo mã QR mới** (mã cũ bị đóng) rồi quét lại bằng mã cũ.
2. Kết quả: "Mã QR đã hết hạn…" hoặc "Phiên điểm danh đã đóng…".

**AT09 – Quét lại không tạo bản ghi trùng**
1. `sv01.demo` quét lại mã đang mở → "Bạn đã điểm danh bằng QR trong buổi học này rồi."
2. Phiếu vẫn chỉ có một dòng cho sv01. Bấm **Xác nhận** để khóa phiếu (sau đó không sửa được dòng).

**AT10 – Vắng vượt ngưỡng thì không đủ điều kiện dự thi**
1. `giangvien.demo` → 🏫 Lớp học → **Cấu trúc dữ liệu và giải thuật** → bấm **Xét điều kiện dự thi**.
2. Thông báo: 1 sinh viên không đủ điều kiện. Mở danh sách: sv08 – "Vắng 3/6 buổi (50.0%) vượt ngưỡng 20%".
3. 📝 Kỳ thi → **Giữa kỳ - Cấu trúc dữ liệu và giải thuật** → **Nạp sinh viên**: không có sv08.
4. `sv08.demo` → **Điểm danh** trên cổng: thấy tỷ lệ vắng lớp CTDL.

### Phần C. Cảnh báo sớm (F3)

**AT11 – Hệ thống phát hiện cảnh báo**
1. `daotao.demo` → **Cảnh báo sớm** → Danh sách cảnh báo / Dashboard cảnh báo.
2. Có 10 cảnh báo: GPA thấp (sv05 4,14), nợ nhiều môn (sv05, sv06), vắng vượt ngưỡng (sv08 50% và 4 sinh viên lớp B/D), nợ học phí quá hạn (sv09 7.000.000đ), thiếu tín chỉ (sv10: 3/10 TC ở Đợt 1).
3. Mở cảnh báo của sv05: phần bằng chứng ghi học kỳ, điểm từng môn; cố vấn phụ trách là ThS. Đặng Minh Châu.

**AT12 – Chạy lại không tạo cảnh báo trùng**
1. **Cảnh báo sớm → Chạy đánh giá cảnh báo** → chạy cho toàn bộ sinh viên.
2. Kết quả: tạo mới 0, cập nhật 10. Số cảnh báo vẫn là 10.

**AT13 – Cố vấn chỉ thấy sinh viên mình phụ trách**
1. Đăng nhập `covan.demo` → Cảnh báo sớm: 8 cảnh báo (lớp A và D). Mở cảnh báo nợ môn của sv06: đã có 1 lần tư vấn. Thử **Ghi nhận tư vấn** cho sv05 rồi **Đóng** cảnh báo.
2. Đăng nhập `covan2.demo`: chỉ 2 cảnh báo của lớp B, không thấy sv05–sv10.
3. Đăng nhập `giangvien.demo`: không có menu Cảnh báo sớm.

### Phần D. Bảo mật dữ liệu sinh viên

**AT14 – Sinh viên A không đọc được dữ liệu của sinh viên B**
1. `sv01.demo` trên cổng chỉ thấy bảng điểm, học phí, điểm danh, đăng ký của chính mình.
2. Truy cập thẳng `/web` → bị chuyển về cổng (tài khoản portal không vào được giao diện quản trị).
3. (Kỹ thuật) gọi JSON-RPC `/web/dataset/call_kw` model `univ.sms.exam.result` bằng phiên sv01 → chỉ trả về kết quả của sv01 (10 bản ghi), không có của sv02.

### Phần E. Các chức năng khác (nếu còn thời gian)

| Chức năng | Tài khoản | Thao tác |
|---|---|---|
| Duyệt rèn luyện cấp khoa | `truongkhoa.demo` | 🏆 Rèn luyện → phiếu sv02 (CVHT đã duyệt) → Duyệt cấp khoa |
| Giấy chứng nhận | `ctsv.demo` | 📜 Giấy chứng nhận → yêu cầu "Giấy xác nhận sinh viên" của sv11 → Duyệt → Hoàn thành |
| Học phí | `taichinh.demo` | 💰 Học phí → lọc sv09: học kỳ trước đã lập hóa đơn, còn nợ, quá hạn |
| Khảo sát | `sv01.demo` | Cổng → Khảo sát → trả lời "Đánh giá giảng dạy" (mỗi sinh viên một lần) |
| Góp ý | `sv11.demo` / `ctsv.demo` | Sinh viên gửi góp ý; CTSV tiếp nhận, phản hồi, đóng |
| Thông báo | `admin.demo` / `sv01.demo` | 📢 Danh sách thông báo: 3 đã đăng (1 ghim, 1 hết hạn) + 1 nháp; quyền portal chỉ đọc được 2 thông báo còn hiệu lực |
| Dịch vụ CTSV | `sv11.demo` | Cổng → Công tác SV: BHYT, ngoại trú (KTX), nghĩa vụ quân sự |

## 4. Đưa dữ liệu về trạng thái ban đầu sau khi tester thao tác

Script không xóa dữ liệu, nên các thao tác của tester (đăng ký thêm, hủy, quét QR,
đóng cảnh báo…) được giữ lại khi chạy lại seed. Muốn có trạng thái sạch hoàn toàn:
tạo DB mới, cài module rồi chạy seed (hoặc khôi phục bản sao DB đã chụp ngay sau
khi seed).
