# Quy trình test tổng hệ thống University SMS

Phiên bản: 20/11/2026. Áp dụng cho bản đang chạy trên server công ty qua Cloudflare.

* **Link:** xem `backups\PUBLIC_URL.txt` trên server (hiện tại `https://wal-establishment-invention-leo.trycloudflare.com`)
* **Mật khẩu mọi tài khoản demo:** `Demo@2026`
* **Dữ liệu:** giả lập, không có thông tin cá nhân thật. Chi tiết tài khoản và tình huống: `docs/TAI_KHOAN_DEMO.md`

## 0. Quy ước

### 0.1 Cách ghi kết quả
Mỗi ca test ghi một trong ba kết quả: **Đạt**, **Lỗi**, **Không rõ** (kết quả khác mô tả nhưng chưa chắc là lỗi).

Khi gặp **Lỗi** hoặc **Không rõ**, gửi đủ 5 thông tin:
1. Mã ca test (ví dụ `DK-04`)
2. Tài khoản đang dùng
3. Thời điểm (giờ:phút)
4. Các bước đã bấm
5. Ảnh chụp màn hình (thấy cả thanh địa chỉ nếu được)

### 0.2 Mức độ lỗi
| Mức | Ý nghĩa | Ví dụ |
|---|---|---|
| Nghiêm trọng | Sai dữ liệu, lộ dữ liệu người khác, không dùng được chức năng chính | Thấy điểm của sinh viên khác; đăng ký vượt sĩ số |
| Cao | Chức năng chạy sai nhưng có cách đi vòng | Thông báo lỗi sai lý do |
| Trung bình | Hiển thị sai, khó dùng | Bảng tràn màn hình điện thoại |
| Thấp | Chính tả, căn lề | Sai dấu tiếng Việt |

### 0.3 Nguyên tắc
* Mỗi người test dùng **tài khoản riêng** theo phân công. Hai người cùng một tài khoản sẽ thấy thao tác của nhau.
* Test cả **máy tính** và **điện thoại** (ít nhất các trang của sinh viên).
* Các ca có ghi "(phá)" là cố tình làm sai để kiểm tra hệ thống có chặn hay không.

## 1. Phân công gợi ý cho 5 người

| Người | Phần test chính | Tài khoản |
|---|---|---|
| 1 | Mục 2, 5, 6 (đăng nhập, đăng ký môn, học phí) | `sv01.demo`, `sv07.demo`, `daotao.demo` |
| 2 | Mục 7, 8 (điểm danh QR, thi và điều kiện dự thi) | `giangvien.demo`, `giangvien2.demo`, `sv02.demo`, `sv08.demo`, `sv10.demo` |
| 3 | Mục 9, 10 (cảnh báo sớm, thông báo) | `covan.demo`, `covan2.demo`, `sv05.demo`, `sv06.demo` |
| 4 | Mục 11, 12, 13 (portal, dịch vụ sinh viên, đăng ký tài khoản) | `sv11.demo`, `sv12.demo`, `ctsv.demo`, `truongkhoa.demo` |
| 5 | Mục 3, 4, 14, 15, 16 (dữ liệu nền, báo cáo, bảo mật, điện thoại) | `admin.demo`, `taichinh.demo`, `sv09.demo`, `sv03.demo` |

## 2. Đăng nhập và phân quyền chung

| Mã | Tài khoản | Thao tác | Kết quả mong đợi |
|---|---|---|---|
| DN-01 | (chưa đăng nhập) | Mở link | Trang đăng nhập tiếng Việt, logo "ĐH DEMO" |
| DN-02 | `sv01.demo` | Đăng nhập | Vào thẳng trang **Học tập** của sinh viên (`/my/academic`) |
| DN-03 | `daotao.demo` | Đăng nhập | Vào giao diện quản trị, trang đầu là danh sách Sinh viên (không phải Discuss) |
| DN-04 | bất kỳ (phá) | Sai mật khẩu | Báo sai thông tin đăng nhập, không vào được |
| DN-05 | (phá) | Mở `/web/signup` và `/web/reset_password` | Không có trang (404). Không tự tạo tài khoản được |
| DN-06 | (phá) | Mở `/web/database/manager` | Báo trình quản lý database đã bị tắt |
| DN-07 | `sv01.demo` (phá) | Gõ thẳng `/web` | Không vào được giao diện quản trị |
| DN-08 | `giangvien.demo` | Xem thanh menu | Không có menu Cảnh báo sớm, Học phí quản trị, cấu hình |
| DN-09 | từng tài khoản cán bộ | Mở lần lượt mọi menu nhìn thấy | Không có màn hình lỗi đỏ "Access Error" hay lỗi hệ thống |
| DN-10 | bất kỳ | Đăng xuất (menu tên người dùng → Đăng xuất) | Về trang đăng nhập |

## 3. Dữ liệu nền (Danh mục)

Tài khoản: `admin.demo` hoặc `daotao.demo` → menu **📁 Danh mục**.

| Mã | Thao tác | Kết quả mong đợi |
|---|---|---|
| DM-01 | Xem Khoa, Bộ môn, Ngành, Môn học, Năm học, Học kỳ | Có dữ liệu FIT, FEB, 3 ngành, khoảng 21 môn |
| DM-02 | Tạo khoa mới mã `TEST1` | Lưu được |
| DM-03 (phá) | Tạo khoa thứ hai cũng mã `TEST1` | Báo mã đã tồn tại, không lưu |
| DM-04 (phá) | Tạo môn học trùng mã với môn có sẵn | Báo mã môn học đã tồn tại |
| DM-05 (phá) | Tạo năm học có ngày kết thúc trước ngày bắt đầu | Báo lỗi ngày |
| DM-06 (phá) | Tạo học kỳ có ngày bắt đầu bằng ngày kết thúc | Báo lỗi ngày |
| DM-07 | Mở môn **Lập trình nâng cao** | Thấy môn tiên quyết "Lập trình cơ bản" |
| DM-08 | Lưu trữ (archive) khoa `TEST1` vừa tạo | Khoa biến khỏi danh sách mặc định, vẫn tìm được bằng bộ lọc "Đã lưu trữ" |

## 4. Hồ sơ sinh viên, lớp hành chính, lớp học

Tài khoản: `daotao.demo`.

| Mã | Thao tác | Kết quả mong đợi |
|---|---|---|
| SV-01 | Sinh viên → Tạo mới (họ tên, ngành, niên khóa) → Lưu | MSSV tự sinh dạng `<2 số năm nhập học><mã ngành><số>`, email trường `<mssv>@student.edu.vn` |
| SV-02 | Tạo thêm 2 sinh viên cùng ngành | MSSV không trùng nhau |
| SV-03 (phá) | Sửa MSSV đã sinh | Không cho sửa |
| SV-04 (phá) | Nhập số CCCD trùng với sinh viên khác | Báo CCCD đã tồn tại |
| SV-05 | Sinh viên mới (Hồ sơ mới) → **Xác nhận nhập học** | Trạng thái **Đang học** |
| SV-06 | **Bảo lưu** → **Quay lại học** | Đổi trạng thái đúng, có lịch sử trong khung trao đổi bên phải |
| SV-07 (phá) | Sinh viên đang ở "Hồ sơ mới" bấm Tốt nghiệp (nếu thấy nút) | Báo không được chuyển trạng thái |
| SV-08 | Mở `sv05.demo` (Hoàng Minh Đức) → **Tốt nghiệp** | Báo chưa đủ điều kiện (thiếu tín chỉ), liệt kê lý do |
| SV-09 (phá) | Xóa sinh viên đang học | Không cho xóa, gợi ý dùng Lưu trữ |
| SV-10 | Lớp hành chính DH20KTPM-A | Có cố vấn ThS. Đặng Minh Châu, số sinh viên đúng |
| LH-01 | 🏫 Lớp học → **Cơ sở dữ liệu (Nhóm 1)** | Có giảng viên, thời khóa biểu Thứ Tư, danh sách sinh viên |
| LH-02 (phá) | Thêm buổi học có giờ kết thúc trước giờ bắt đầu | Báo lỗi giờ |
| LH-03 | So sĩ số lớp với số sinh viên trong danh sách | Khớp (không đếm đăng ký đã hủy) |

## 5. Đăng ký môn học thông minh (F1)

Đợt đang mở: **Đợt 2 – Đăng ký bổ sung**, tối thiểu 6, tối đa 20 tín chỉ. Trang: **Đăng ký môn học** trên portal sinh viên.

| Mã | Tài khoản | Thao tác | Kết quả mong đợi |
|---|---|---|---|
| DK-01 | `sv01.demo` | Mở trang đăng ký | Thấy đợt đang mở, số tín chỉ đã đăng ký, danh sách môn đã đăng ký và các lớp đang mở (sĩ số, lịch, phòng) |
| DK-02 (AT01) | `sv01.demo` | Đăng ký **An toàn thông tin** | "Đăng ký thành công…", môn xuất hiện trong danh sách đã đăng ký, sĩ số lớp tăng 1, số tín chỉ tăng 2 |
| DK-03 | `sv01.demo` | Mở **Thời khóa biểu** | Có thêm buổi Thứ Bảy 13:00-15:00 |
| DK-04 (AT03) | `sv01.demo` | Đăng ký **Mạng máy tính** | Từ chối: "Trùng lịch với môn Lập trình nâng cao (Thứ Hai 07:00-09:30)". Sĩ số không đổi |
| DK-05 | `sv01.demo` | Đăng ký **Cơ sở dữ liệu** nhóm còn lại | Từ chối: đã đăng ký môn này ở lớp khác |
| DK-06 (AT02) | `sv07.demo` | Đăng ký **Lập trình nâng cao** | Từ chối: "Chưa hoàn thành môn tiên quyết: Lập trình cơ bản" |
| DK-07 | `sv01.demo` | Đăng ký **Tài chính doanh nghiệp** | Từ chối: thiếu "Nguyên lý kế toán" |
| DK-08 (AT04) | `sv01.demo` | Lớp **Trí tuệ nhân tạo** (2/2) → bấm "vào danh sách chờ" | "Lớp đã đủ chỗ. Bạn đang ở vị trí chờ số 2". Mục "Danh sách chờ" trên trang hiện vị trí |
| DK-09 | `sv01.demo` | Bấm đăng ký lại lớp AI | Không tạo vị trí chờ thứ hai |
| DK-10 (AT05) | `sv02.demo` | Hủy đăng ký lớp **Trí tuệ nhân tạo** | Hủy thành công |
| DK-11 (AT05) | `sv04.demo` | Mở trang đăng ký | Lớp AI chuyển sang **Đã đăng ký** (được nhận tự động); có thông báo "Đã được nhận vào lớp" |
| DK-12 | `sv01.demo` | Mở lại trang | Vị trí chờ lớp AI lên **số 1** |
| DK-13 | `daotao.demo` | ✍️ Đăng ký môn → ⏳ Danh sách chờ | Thấy đúng thứ tự và trạng thái (đã nhận, đang chờ) |
| DK-14 | `sv02.demo` | Đăng ký lại lớp AI sau khi hủy | Lớp đã đầy → vào danh sách chờ (không tạo bản ghi trùng) |
| DK-15 | `sv01.demo` | Đăng ký liên tục nhiều môn cho tới khi vượt 20 tín chỉ của đợt | Môn làm vượt bị từ chối, báo số tín chỉ hiện có và tối đa |
| DK-16 | `sv01.demo` | Hủy môn vừa đăng ký ở DK-02 | Sĩ số giảm, tín chỉ giảm, học phí giảm (mục 6) |
| DK-17 (phá) | `sv01.demo` | Bấm nhanh nút Đăng ký 2–3 lần liên tiếp | Chỉ xử lý một lần, nút chuyển "Đang xử lý…" |
| DK-18 | `daotao.demo` | Mở một đăng ký của sinh viên | Thấy liên kết tới ghi danh (enrollment), thông điệp kết quả |
| DK-19 | `daotao.demo` | Đóng **Đợt 2** (Đợt đăng ký → Đóng), rồi `sv01.demo` mở trang đăng ký | Không còn nút đăng ký; báo không có đợt đang mở. **Nhớ mở lại đợt sau khi test** |

## 6. Học phí

| Mã | Tài khoản | Thao tác | Kết quả mong đợi |
|---|---|---|---|
| HP-01 | `sv01.demo` | Portal → **Học phí** trước và sau khi đăng ký thêm môn (DK-02) | Học kỳ hiện tại tăng 2 tín chỉ, tăng 1.000.000đ (đơn giá 500.000đ/TC) khi khoản phí còn ở trạng thái Dự kiến |
| HP-02 | `sv09.demo` | Portal → Học phí | Học kỳ trước còn nợ 7.000.000đ, đã quá hạn |
| HP-03 | `taichinh.demo` | 💰 Học phí → khoản phí của sv09 | Đúng số tiền, hạn thanh toán, trạng thái |
| HP-04 | `taichinh.demo` | Khoản phí ở trạng thái Dự kiến → **Tạo hóa đơn** hai lần | Lần hai mở lại đúng hóa đơn cũ, không tạo hóa đơn thứ hai |
| HP-05 | `taichinh.demo` | Hóa đơn → Xác nhận → Đã thanh toán | Số đã thanh toán, còn lại và trạng thái khoản phí cập nhật đúng |
| HP-06 | `taichinh.demo` | Hóa đơn đã xác nhận → **Tạo hóa đơn kế toán** | Tạo được, hoặc báo rõ thiếu cấu hình kế toán (không lỗi hệ thống) |
| HP-07 | `sv03.demo` (phá) | Thử xem học phí của người khác bằng cách sửa đường dẫn | Không thấy |

## 7. Điểm danh và điểm danh QR (F2)

Phiếu dùng để test: **Cơ sở dữ liệu (Nhóm 1) – ngày demo**, trạng thái Nháp, giảng viên `giangvien.demo`.

| Mã | Tài khoản | Thao tác | Kết quả mong đợi |
|---|---|---|---|
| DD-01 | `giangvien.demo` | ✅ Điểm danh → mở phiếu nháp → **Bắt đầu điểm danh QR** | Hiện mã QR, giờ hết hạn (tối đa 10 phút), số đã quét. Sinh viên chưa quét mặc định **Vắng mặt** |
| DD-02 (AT06) | `sv02.demo` trên điện thoại | Quét QR bằng camera → đăng nhập nếu được hỏi | "Điểm danh thành công: Có mặt" (hoặc Đi trễ nếu quét sau 5 phút) |
| DD-03 | `giangvien.demo` | Tải lại phiếu | Dòng sv02: Có mặt, có giờ check-in, nguồn "Quét QR"; số đã quét tăng |
| DD-04 (AT09) | `sv02.demo` | Quét lại cùng mã | "Bạn đã điểm danh bằng QR… rồi". Không thêm dòng |
| DD-05 (AT07) | `sv10.demo` | Quét cùng mã | Từ chối: không có tên trong danh sách lớp. Phiếu không thêm dòng nào |
| DD-06 | `giangvien2.demo` | Quét cùng mã | Từ chối: không phải tài khoản sinh viên |
| DD-07 | (chưa đăng nhập) | Mở link QR | Chuyển sang trang đăng nhập; đăng nhập xong quay lại điểm danh |
| DD-08 (AT08) | `giangvien.demo` + sv bất kỳ | Bấm **Tạo mã QR mới**, rồi quét **mã cũ** (chụp ảnh mã cũ trước) | Từ chối: mã hết hạn hoặc phiên đã đóng |
| DD-09 | sv trong lớp | Quét mã sau hơn 5 phút kể từ lúc mở phiên | Ghi nhận **Đi trễ** |
| DD-10 | `giangvien.demo` | **Đóng phiên** → **Xác nhận** phiếu | Phiếu chuyển Đã xác nhận, mã QR không còn dùng được |
| DD-11 (phá) | `giangvien.demo` | Sửa trạng thái một dòng trên phiếu đã xác nhận | Không cho sửa |
| DD-12 | `daotao.demo` | Phiếu đã xác nhận → **Về nháp** | Chỉ Phòng Đào tạo / admin làm được |
| DD-13 | `giangvien.demo` | Tạo phiếu điểm danh mới cho lớp mình → **Tải danh sách SV** hai lần | Không bị trùng sinh viên |
| DD-14 | `giangvien2.demo` | Xem danh sách phiếu điểm danh | Không thấy phiếu các lớp của `giangvien.demo` |
| DD-15 | `sv08.demo` | Portal → **Điểm danh** | Thấy tỷ lệ vắng từng lớp; lớp Cấu trúc dữ liệu vắng 3/6 (50%) |

## 8. Thi, bảng điểm, điều kiện dự thi

| Mã | Tài khoản | Thao tác | Kết quả mong đợi |
|---|---|---|---|
| TH-01 (AT10) | `giangvien.demo` | 🏫 Lớp học → **Cấu trúc dữ liệu và giải thuật** → **Xét điều kiện dự thi** | sv08 không đủ điều kiện, lý do "Vắng 3/6 buổi (50.0%) vượt ngưỡng 20%" |
| TH-02 | `giangvien.demo` | 📝 Kỳ thi → **Giữa kỳ – Cấu trúc dữ liệu** → **Nạp sinh viên** hai lần | Không có sv08; lần hai không tạo trùng |
| TH-03 | `giangvien.demo` | Nhập điểm 8,5 cho một sinh viên | Lưu được, cột Đạt đúng (≥ 5 là đạt) |
| TH-04 (phá) | `giangvien.demo` | Nhập điểm -1 hoặc 11 | Báo lỗi khoảng điểm |
| TH-05 | `giangvien2.demo` (phá) | Tìm kỳ thi hoặc kết quả của lớp `giangvien.demo` | Không thấy, không sửa được |
| TH-06 | `sv08.demo` | Portal → Điểm danh | Lớp CTDL ghi "Không đủ điều kiện dự thi" kèm lý do; có thông báo cá nhân tương ứng |
| TH-07 | `sv12.demo` | Portal → **Bảng điểm** | Điểm học kỳ trước, kết quả Đạt / Không đạt từng môn |
| TH-08 | `daotao.demo` | Bảng điểm → bảng điểm của sv05 | GPA học kỳ 4,14; xếp loại tương ứng |
| TH-09 | `sv07.demo` | Portal → Bảng điểm | Lập trình cơ bản 3,3 (không đạt), khớp với lý do bị chặn ở DK-06 |

## 9. Cảnh báo sớm và cố vấn học tập (F3)

| Mã | Tài khoản | Thao tác | Kết quả mong đợi |
|---|---|---|---|
| CB-01 (AT12) | `daotao.demo` | **Cảnh báo sớm** → Danh sách cảnh báo | 10 cảnh báo: GPA thấp (sv05), nợ môn (sv05, sv06), vắng học (sv08 và 4 sinh viên lớp B/D), nợ học phí (sv09), thiếu tín chỉ (sv10) |
| CB-02 | `daotao.demo` | Mở cảnh báo GPA của sv05 | Có bằng chứng (GPA, học kỳ, chi tiết), mức độ Cao, cố vấn phụ trách |
| CB-03 (AT11) | `daotao.demo` | **Chạy đánh giá cảnh báo** cho toàn bộ | Kết quả "tạo mới 0, cập nhật 10". Tổng số cảnh báo không tăng |
| CB-04 | `daotao.demo` | **Dashboard cảnh báo** | Biểu đồ và bảng tổng hợp, nhóm được theo lớp, ngành, loại, mức độ, trạng thái |
| CB-05 (AT13) | `covan.demo` | Cảnh báo sớm | Chỉ thấy 8 cảnh báo của lớp A và D |
| CB-06 (AT13) | `covan2.demo` | Cảnh báo sớm | Chỉ thấy 2 cảnh báo của lớp B; không thấy sv05–sv10 |
| CB-07 | `covan.demo` | Mở cảnh báo sv05 → **Bắt đầu xử lý** → **Ghi nhận tư vấn** (nội dung, kết quả) | Có dòng tư vấn kèm người, thời gian; trạng thái Đang xử lý; ghi vào lịch sử |
| CB-08 (phá) | `covan.demo` | Đóng một cảnh báo chưa có tư vấn và không ghi chú | Hệ thống yêu cầu ghi tư vấn hoặc ghi chú khi đóng |
| CB-09 | `covan.demo` | **Đóng cảnh báo** sau khi đã tư vấn → **Mở lại** | Ghi người đóng và thời gian đóng; mở lại thì về Đang xử lý |
| CB-10 (phá) | `covan.demo` | Sửa cố vấn phụ trách hoặc giá trị bằng chứng | Không cho sửa |
| CB-11 | `giangvien.demo` | Tìm menu Cảnh báo sớm | Không có |
| CB-12 | `sv06.demo` | Mở cảnh báo của mình (nếu có link trong thông báo) | Chỉ xem được của chính mình |

## 10. Thông báo cá nhân (F4)

| Mã | Tài khoản | Thao tác | Kết quả mong đợi |
|---|---|---|---|
| TB-01 | `sv01.demo` | Trang Học tập | Khung "Bạn có N thông báo chưa đọc" |
| TB-02 | `sv01.demo` | Sau DK-02, DK-04, DK-08 → mở **Thông báo** | Mỗi sự kiện có một thông báo: đăng ký thành công, bị từ chối (có lý do), đang chờ (có vị trí) |
| TB-03 | `sv04.demo` | Sau DK-11 | Có thông báo "Đã được nhận vào lớp…" |
| TB-04 | `sv08.demo` | Sau TH-01 | Có thông báo không đủ điều kiện dự thi |
| TB-05 | `sv05.demo` | Thông báo | Có thông báo cảnh báo học vụ |
| TB-06 | `sv01.demo` | Bấm **Đã đọc** một thông báo, rồi **Đánh dấu tất cả đã đọc** | Số chưa đọc giảm về 0 |
| TB-07 | `daotao.demo` | Sinh viên → **Thông báo cá nhân** | Thấy danh sách thông báo của mọi sinh viên |
| TB-08 | `sv01.demo` | Mục **Thông báo chung** trên trang giới thiệu `/university` | Chỉ thấy thông báo đã đăng, còn hạn; thông báo ghim nằm đầu |

## 11. Portal sinh viên (từng trang)

Tài khoản: `sv12.demo` (sinh viên xuất sắc), lặp lại với `sv05.demo`.

| Mã | Trang | Kết quả mong đợi |
|---|---|---|
| PT-01 | Học tập (trang chủ) | Đúng họ tên, MSSV, ngành, lớp hành chính, email trường; các nút chức năng |
| PT-02 | Thời khóa biểu | Lịch theo thứ, giờ, phòng; chỉ các lớp đang học |
| PT-03 | Bảng điểm | Điểm từng môn, học kỳ, đạt/không đạt |
| PT-04 | Điểm danh | Lịch sử từng buổi, tỷ lệ vắng, điều kiện dự thi |
| PT-05 | Học phí | Từng học kỳ: tín chỉ, tổng tiền, đã đóng, còn lại |
| PT-06 | Đăng ký môn | Như mục 5 |
| PT-07 | Giấy chứng nhận | Danh sách yêu cầu và trạng thái; form gửi yêu cầu |
| PT-08 | Công tác SV | BHYT, cư trú, nghĩa vụ quân sự |
| PT-09 | Rèn luyện | Điểm rèn luyện các học kỳ và trạng thái duyệt |
| PT-10 | Khảo sát | Khảo sát đang mở và đã trả lời |
| PT-11 | Góp ý | Lịch sử góp ý và phản hồi |
| PT-12 | Thông báo | Như mục 10 |

## 12. Dịch vụ sinh viên

| Mã | Tài khoản | Thao tác | Kết quả mong đợi |
|---|---|---|---|
| DV-01 | `sv11.demo` | Giấy chứng nhận → chọn **Bảng điểm song ngữ**, nhập lý do → Gửi | "Đã gửi yêu cầu thành công", có trong danh sách (Chờ duyệt) |
| DV-02 (phá) | `sv11.demo` | Gửi lại cùng loại giấy | "Bạn đã có yêu cầu đang xử lý cho loại giấy này" |
| DV-03 (phá) | `sv11.demo` | Gửi mà bỏ trống lý do | Báo phải nhập lý do |
| DV-04 | `ctsv.demo` | 📜 Giấy chứng nhận → yêu cầu ở DV-01 → **Duyệt** → **Hoàn thành** | Trạng thái đổi đúng thứ tự; sinh viên thấy trạng thái mới |
| DV-05 (phá) | `ctsv.demo` | Hoàn thành một yêu cầu chưa duyệt | Không cho |
| DV-06 | `ctsv.demo` | Từ chối một yêu cầu đang chờ | Trạng thái Từ chối |
| DV-07 | `sv11.demo` | Công tác SV → khai báo nghĩa vụ quân sự | Gửi được; gửi lần hai khi còn đang chờ thì bị chặn |
| DV-08 | `ctsv.demo` | 🤝 Công tác SV → duyệt NVQS, xác nhận BHYT, xác nhận cư trú | Chuyển trạng thái đúng |
| DV-09 | `sv01.demo` | Khảo sát → trả lời **Đánh giá giảng dạy** | Gửi thành công; lần sau hiện "đã trả lời", không gửi lại được |
| DV-10 (phá) | `sv01.demo` | Gửi khảo sát với nội dung trống | Báo phải nhập nội dung |
| DV-11 | `sv11.demo` | Góp ý → chọn loại, bộ phận, tiêu đề, nội dung → Gửi | Gửi được; gửi y hệt ngay lập tức lần hai thì bị chặn |
| DV-12 | `ctsv.demo` | 💬 Góp ý → Đang xử lý → nhập phản hồi → Đã xử lý → Đóng | Sinh viên thấy phản hồi |
| DV-13 | `sv03.demo` | Rèn luyện → xem phiếu nháp | Thấy tiêu chí và điểm |
| DV-14 | `covan.demo` | 🏆 Rèn luyện → phiếu đã gửi → chấm điểm CVHT → **CVHT duyệt** | Chuyển "CVHT đã duyệt" |
| DV-15 (phá) | `covan.demo` | Chấm điểm vượt điểm tối đa của tiêu chí | Báo lỗi |
| DV-16 | `truongkhoa.demo` | Phiếu sv02 (CVHT đã duyệt) → **Khoa duyệt** | Chuyển "Khoa đã duyệt", xếp loại theo tổng điểm |
| DV-17 (phá) | `covan.demo` | Thử bấm duyệt cấp khoa | Không có quyền |
| DV-18 | `admin.demo` | 📢 Thông báo → tạo thông báo mới → Đăng | Sinh viên thấy trên trang `/university` |

## 13. Đăng ký tài khoản sinh viên công khai

Mở cửa sổ ẩn danh (chưa đăng nhập) → `/student/register`.

| Mã | Thao tác | Kết quả mong đợi |
|---|---|---|
| TK-01 | Điền đủ thông tin hợp lệ (tên đăng nhập mới, mật khẩu ≥ 8 ký tự) → Gửi | Tạo thành công, hiện MSSV; đăng nhập được bằng tài khoản mới |
| TK-02 | Đăng nhập tài khoản mới → Đăng ký môn | Chưa được đăng ký vì hồ sơ đang "Hồ sơ mới" (chờ Phòng Đào tạo xác nhận) |
| TK-03 | `daotao.demo` xác nhận nhập học cho hồ sơ mới | Sinh viên mới đăng ký môn được |
| TK-04 (phá) | Tên đăng nhập đã tồn tại (ví dụ `sv01.demo`) | Báo tên đăng nhập đã tồn tại |
| TK-05 (phá) | Email sai định dạng; mật khẩu 5 ký tự; xác nhận mật khẩu không khớp | Báo từng lỗi, giữ lại thông tin đã nhập |
| TK-06 (phá) | Ngày sinh trong tương lai hoặc dưới 15 tuổi | Báo lỗi ngày sinh |
| TK-07 (phá) | CCCD có chữ hoặc ít hơn 9 số | Báo lỗi CCCD |

## 14. Báo cáo PDF và dashboard

| Mã | Tài khoản | Thao tác | Kết quả mong đợi |
|---|---|---|---|
| BC-01 | `daotao.demo` | Sinh viên → chọn sv12 → **In** → Bảng điểm sinh viên | File PDF tiếng Việt đúng dấu, đúng điểm của sv12 |
| BC-02 | `daotao.demo` | In bảng điểm cho sinh viên mới tạo (chưa có điểm) | PDF vẫn tạo được, bảng trống, không lỗi |
| BC-03 | `taichinh.demo` | Hóa đơn → In hóa đơn học phí | PDF đúng số tiền |
| BC-04 | `giangvien.demo` | Phiếu điểm danh → In | PDF đủ danh sách, nhiều trang thì phân trang đúng |
| BC-05 | `ctsv.demo` | Yêu cầu giấy chứng nhận → In giấy | PDF đúng thông tin sinh viên |
| BC-06 | `daotao.demo` | Đăng ký môn → In phiếu đăng ký | PDF đúng các môn |
| BC-07 | `truongkhoa.demo` | Rèn luyện → In phiếu điểm rèn luyện | PDF đúng tiêu chí và điểm |
| BC-08 | từng vai trò | 📈 Dashboards → từng dashboard | Mở được biểu đồ và bảng; số liệu chỉ trong phạm vi được phép |

## 15. Bảo mật và truy cập chéo (AT14)

| Mã | Tài khoản | Thao tác | Kết quả mong đợi |
|---|---|---|---|
| BM-01 | `sv01.demo` | Mọi trang portal | Chỉ thấy dữ liệu của chính mình |
| BM-02 (phá) | `sv01.demo` | Sửa số trong đường dẫn có ID (ví dụ hủy đăng ký `/cancel/<số khác>`) | Báo không hợp lệ hoặc từ chối, không thay đổi dữ liệu người khác |
| BM-03 (phá) | `sv01.demo` | Mở link QR của một lớp không học | Từ chối, không tạo dữ liệu |
| BM-04 | `giangvien.demo` | Danh sách sinh viên / kết quả thi | Chỉ sửa được điểm lớp mình dạy |
| BM-05 | `covan2.demo` | Cảnh báo, kết quả học tập | Chỉ sinh viên mình phụ trách |
| BM-06 | `taichinh.demo` | Học phí, ghi danh | Xem được toàn bộ học phí; không sửa điểm thi |

## 16. Điện thoại và trình duyệt

| Mã | Thao tác | Kết quả mong đợi |
|---|---|---|
| DT-01 | Mở toàn bộ trang portal sinh viên trên điện thoại | Không phải cuộn ngang trang; bảng dài thì cuộn trong khung bảng |
| DT-02 | Đăng ký môn trên điện thoại | Bấm được nút, đọc được thông báo kết quả |
| DT-03 | Quét QR bằng camera điện thoại (iPhone và Android) | Mở đúng trang điểm danh, chữ dễ đọc |
| DT-04 | Chrome, Edge, Safari, Firefox trên máy tính | Hiển thị và thao tác như nhau |

## 17. Nhiều người dùng đồng thời

| Mã | Thao tác | Kết quả mong đợi |
|---|---|---|
| ĐT-01 | 5 người cùng thao tác trong 10–15 phút (theo phân công mục 1) | Không ai gặp lỗi hệ thống; trang mở dưới 2–3 giây |
| ĐT-02 | 3 sinh viên cùng bấm đăng ký **một lớp còn đúng 1 chỗ** trong vài giây | Chỉ 1 người được nhận, những người khác vào danh sách chờ; sĩ số không vượt tối đa |
| ĐT-03 | Cả lớp cùng quét QR một lúc | Mỗi người đúng một dòng, không lỗi |

Kết quả đo trước khi gửi: 5 người dùng đồng thời trong 60 giây qua Cloudflare, 1.273 request, 0 lỗi, thời gian phản hồi trung vị 0,23 giây.

## 18. Bảng tổng hợp kết quả

| Mục | Số ca | Đạt | Lỗi | Không rõ | Người test |
|---|---|---|---|---|---|
| 2 Đăng nhập và phân quyền | 10 | | | | |
| 3 Dữ liệu nền | 8 | | | | |
| 4 Hồ sơ sinh viên, lớp | 13 | | | | |
| 5 Đăng ký môn (F1) | 19 | | | | |
| 6 Học phí | 7 | | | | |
| 7 Điểm danh QR (F2) | 15 | | | | |
| 8 Thi, điều kiện dự thi | 9 | | | | |
| 9 Cảnh báo sớm (F3) | 12 | | | | |
| 10 Thông báo (F4) | 8 | | | | |
| 11 Portal sinh viên | 12 | | | | |
| 12 Dịch vụ sinh viên | 18 | | | | |
| 13 Đăng ký tài khoản | 7 | | | | |
| 14 Báo cáo, dashboard | 8 | | | | |
| 15 Bảo mật | 6 | | | | |
| 16 Điện thoại | 4 | | | | |
| 17 Đồng thời | 3 | | | | |
| **Tổng** | **159** | | | | |

## 19. Sau khi test

* Dữ liệu sau buổi test sẽ bị thay đổi. Muốn đưa về trạng thái ban đầu, khôi phục từ bản backup sạch (`backups\univ_sms_demo_deploy.dump`). Việc này do quản trị thực hiện, mất khoảng 2 phút.
* Mọi lỗi báo về được sửa, kiểm tra lại bằng automated test (hiện có 174 test), rồi cập nhật lên server.
