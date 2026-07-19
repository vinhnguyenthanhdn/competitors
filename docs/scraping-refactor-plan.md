# Kế hoạch refactor dữ liệu tour đối thủ — dễ maintain khi cào thêm

> Ghi lại tối 19/7/2026, giữa lúc đang refactor. Đọc file này trước khi làm tiếp.

## Bối cảnh

`toan-bo-tour-hdv.html` và `so-sanh-gia-tour.html` trước giờ nhúng **cứng từng thẻ tour trực tiếp trong HTML**. Mỗi lần cào thêm phải: tìm đúng dòng, chèn khối HTML, tính lại count/khoảng giá bằng tay, dễ sai số (đã từng bị lệch nhiều lần trong phiên này). Không maintain được lâu dài.

**Mục tiêu refactor:** tách dữ liệu ra khỏi trình bày — `data/tours-data.js` là nguồn dữ liệu duy nhất, 2 trang HTML chỉ load file này và tự render card/bảng/filter/count bằng JS. Cào thêm sau này = thêm object vào mảng dữ liệu, không đụng vào HTML nữa.

## Đã làm xong trong phiên này (trước khi refactor)

Đã cào bổ sung thực tế (không phải mock), tổng đã lập hồ sơ chi tiết: **592 tour/HDV** (từ 198 ban đầu):

| Platform | Trước | Sau |
|---|---|---|
| ToursByLocals | 62 | **117** (100%, đủ 2 trang) |
| GetYourGuide | 24 | **118** (qua Cloudflare, "Show more" x6) |
| Viator | 33 | **105** (4 trang pagination) |
| Airbnb Experiences | 12 | **185** (base + 3 combo tag + 12 tag đơn + Hội An/Huế search riêng) |
| ShowAround/GuruWalk | 30/4 | không đổi (nút load-more không ổn định / đã hết) |

Đã đồng bộ số liệu vào `so-sanh-gia-tour.html` (phân loại theo 9 nhóm điểm đến bằng keyword-matching trên title, quy đổi VNĐ tỷ giá 26.000/USD·30.000/EUR, sắp lại theo giá tăng dần).

## Refactor — ĐÃ XONG (19/7/2026)

1. ✅ `scripts/build_unified_data.py` — chứa `classify(title)` (phân nhóm theo keyword, thứ tự ưu tiên My Son > Huế > Bà Nà > Marble/Monkey > Hội An > Food > Outdoor > City tour > Khác) và `parse_price(price_text, platform)` (quy đổi VNĐ: USD×26.000, EUR×30.000, Free→0).
2. ✅ Parse toàn bộ 592 card từ bản HTML tĩnh cũ → `data/raw/cards-bootstrap-2026-07-18.json` (592 object chuẩn hoá).
3. ✅ `build_unified_data.py` đọc **mọi** `data/raw/cards-*.json` (glob, không chỉ bootstrap), khử trùng theo `(platform, title, href)` — **không phải `href` một mình** (đã phát hiện bug: ShowAround/Tubudd/GoWithGuide dùng chung 1 href hồ sơ chung cho toàn bộ guide, dedupe theo href sẽ làm mất 29/30 guide ShowAround).
4. ✅ Output `data/tours-data.js` (`const TOURS_DATA = [...]`) — 592 tour, 570 có giá/nhóm, 22 không.
5. ✅ `scripts/extractors/{airbnb,getyourguide,viator,toursbylocals}.js` — snippet cào lại, có comment URL + cách chạy.
6. ✅ `data/raw/scrapes/` — 77 file JSON thô từng lượt cào, tách khỏi file đã chuẩn hoá (build script không đọc thư mục này).
7. ✅ `toan-bo-tour-hdv.html` viết lại: xoá 592 `.card` + filter-button tĩnh, thay bằng `<script src="data/tours-data.js">` + script render động (build filter/count/card từ `TOURS_DATA`). Test: 592 card, filter Airbnb (185) ẩn đúng 407 card còn lại.
8. ✅ `so-sanh-gia-tour.html` viết lại tương tự: xoá 10 `.ov-group` tĩnh, render động theo `group`, sort tăng dần theo `vnd`, free-tour ("Miễn phí") xếp đầu mỗi nhóm. Test: 570 row, 10 nhóm, Bà Nà Hills group = 61 tour đúng.
9. ✅ `scripts/README.md` — quy trình cào thêm (platform cũ / platform mới), giới hạn kỹ thuật đã biết per-platform.
10. ⏳ **Còn lại:** dọn file rác trong scratchpad (không ảnh hưởng repo), review lại `git status`, commit + push toàn bộ `data/`, `scripts/`, `docs/`, 2 file HTML đã sửa.

## Việc còn lại

1. `git status` kiểm tra không sót gì ngoài ý muốn (không commit file `.bak`/backup tạm nếu có sót).
2. Xoá `so-sanh-gia-tour.BACKUP*.html` nếu đã copy vào `data/raw/scrapes/` — không cần giữ 2 bản.
3. `git add data/ scripts/ docs/ toan-bo-tour-hdv.html so-sanh-gia-tour.html`, commit, push.
4. (Tuỳ chọn, không bắt buộc) Cân nhắc thêm tương tự cho `index.html` nếu sau này nó cũng cần số liệu động — hiện tại `index.html` là bài phân tích tường thuật, ít con số lặp lại nên chưa cần refactor.

## Lưu ý quan trọng khi làm tiếp

- **Không dùng `fetch()`** để load `tours-data.js` — 2 trang này mở trực tiếp bằng `file://`, Chrome chặn CORS cho fetch giữa 2 file `file://`. Phải dùng `<script src="data/tours-data.js"></script>` (khai báo biến toàn cục), không phải AJAX.
- **3 platform coi là "hồ sơ HDV theo giờ"** (ShowAround, Tubudd, GoWithGuide) phải luôn được gán `group = "Thuê HDV theo giờ / gói giờ (không lịch trình cố định)"` bất kể tiêu đề, không chạy qua `classify()` — nếu không sẽ bị xếp nhầm nhóm theo từ khoá trong tên HDV.
- Airbnb/GetYourGuide/Viator **chưa phải toàn bộ** (146/500+, 118/500+, 105/1.000+ — xem lại, Airbnb đã lên 185 sau khi cào thêm Hội An/Huế) — khi hiển thị tổng số, luôn ghi rõ đây là mẫu đã cào, tổng thật xem ở `index.html` cột "Tổng số tour/HDV đang hoạt động".
- File gốc `so-sanh-gia-tour.html` và `toan-bo-tour-hdv.html` đã có backup tại `data/raw/scrapes/` phòng khi cần đối chiếu (không phải bản backup chính thức, chỉ là snapshot giữa chừng lúc merge).
