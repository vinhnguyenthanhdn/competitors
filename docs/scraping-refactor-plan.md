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
- **2 platform coi là "hồ sơ HDV theo giờ" thuần** (ShowAround, Tubudd) phải luôn được gán `group = "Thuê HDV theo giờ / gói giờ (không lịch trình cố định)"` bất kể tiêu đề, không chạy qua `classify()`. **GoWithGuide là mô hình lai** (37 tour đóng gói + 8 hồ sơ HDV) — chỉ card có `title` kết thúc bằng `" (guide)"` mới bị force vào nhóm này (`is_guide_profile()` trong `build_unified_data.py`), 37 tour còn lại chạy qua `classify()` bình thường. Nếu thêm platform hồ sơ HDV thuần mới, thêm vào `GUIDE_PROFILE_PLATFORMS`; nếu platform lai như GoWithGuide, đặt suffix `" (guide)"` vào title khi build card cho phần hồ sơ.
- Airbnb/GetYourGuide/Viator **chưa phải toàn bộ** (185/309, 118/500+, 105/1.000+) — khi hiển thị tổng số, luôn ghi rõ đây là mẫu đã cào, tổng thật xem ở `index.html` cột "Tổng số tour/HDV đang hoạt động". GetYourGuide/Viator hiển thị dạng ngưỡng "500+"/"1.000+" (không phải số đếm chính xác), Airbnb ghi số cụ thể.
- **ShowAround cũng có trần hiển thị ~32 hồ sơ/lượt xem** giống Airbnb (không phải do lỗi thao tác trước đây) — trang tự công bố 74 guide nhưng chỉ duyệt được tối đa ~32/lượt; workaround: lọc theo Gender (Nam=26 đầy đủ, Nữ=44 nhưng vẫn cắt ở 38) rồi hợp nhất theo href thật (không dùng href chung của trang danh sách) → cào được 61/74 (19/07/2026). Bộ lọc Activities/Languages trên ShowAround **không hoạt động** (luôn trả về full 74, coi như no-op — đừng phí thời gian thử lại).
- **GoWithGuide có 2 view riêng biệt** dễ bị bỏ sót: `/vietnam/da-nang/tours` (catalog tour đóng gói) và `/vietnam/da-nang/guides` (hồ sơ HDV) — nếu chỉ cào 1 trong 2 sẽ ra số thấp hơn thực tế nhiều (từng bị ghi nhầm là "8" vì chỉ cào phần guides). Trang tours mặc định (`/s?city=da-nang&t=tours`) cũng chỉ hiển thị 11/37 tour thật — phải duyệt qua từng category (`/vietnam/da-nang/category/<slug>`: highlights, art-culture-historical, food-drink, nature-outdoor, off-the-beaten-path, day-trip, nightlife) rồi hợp nhất theo href mới ra đủ 37.
- Klook bị chặn bởi DataDome CAPTCHA khi kiểm tra lại ngày 19/07/2026 — không có cách nào bypass CAPTCHA một cách hợp lệ, đành giữ nguyên số cũ (1 SKU), thử lại sau.
- Ong Vò Vẽ không có bộ lọc theo tỉnh/thành đáng tin cậy trên site, và số marketing tự công bố ở trang chủ không nhất quán qua các lần kiểm tra (từng "57 toàn hệ thống", nay "+1999") — không dùng số này, giữ đếm thủ công qua link hồ sơ trực tiếp.
- File gốc `so-sanh-gia-tour.html` và `toan-bo-tour-hdv.html` đã có backup tại `data/raw/scrapes/` phòng khi cần đối chiếu (không phải bản backup chính thức, chỉ là snapshot giữa chừng lúc merge).

## Rà soát độ tin cậy số liệu (19/07/2026)

Theo yêu cầu "biết số total chính xác từng đối thủ làm cơ sở phân tích", đã đối chiếu lại số ở mỗi nền tảng với chính trang web của họ (không suy diễn/ước tính):

| Platform | Số cũ | Số đã xác minh (19/07/2026) | Ghi chú |
|---|---|---|---|
| Airbnb Experiences | 310 | **200–309 (dao động, không đáng tin)** | Cùng URL/ngày/filter, số tự công bố lệch 309→200 (35%) qua các lần load lại — xem mục xác minh sâu bên dưới |
| GetYourGuide | 500+ | **500+** (chưa xác minh sâu được) | Thử đếm sản phẩm thật như Viator nhưng bị Cloudflare chặn liên tục lúc kiểm tra |
| Viator | 1.000+ | **≥1.750 (đã xác minh sâu, không bị thổi phồng)** | Cào 73/77 trang bằng selector card chính xác — số thật CAO hơn số công bố, xem mục xác minh sâu bên dưới |
| ToursByLocals | 117 | **117** (không đổi) | Khớp 100% với số nền tảng tự công bố |
| WithLocals | 8 | **8** (không đổi) | Khớp 100% qua tìm kiếm trực tiếp |
| Tubudd | 9 | **9** (không đổi) | Khớp 100% với "Da Nang · 9 buddies" |
| GuruWalk | 5 | **4** | Trang tự ghi "5 free tours" nhưng chỉ 4 tour có link thật hiển thị/đặt được |
| ShowAround | 30 (cào được) / 74 (công bố) | **61/74** | Trần hiển thị ~32/lượt xem; dùng thêm filter Gender mới lên 61 |
| GoWithGuide | 8 (chỉ tính guide) | **45** (37 tour + 8 guide) | Số cũ bỏ sót toàn bộ catalog tour đóng gói — sai lệch lớn nhất phát hiện được |
| Ong Vò Vẽ | 2 | **2** (không đổi) | Site không có filter tỉnh/thành đáng tin, giữ đếm thủ công |
| Klook | 1 | không kiểm tra được | Bị chặn DataDome CAPTCHA lúc truy cập |

## Xác minh sâu "số công bố có bị thổi phồng không" (19/07/2026, theo yêu cầu riêng của user)

User nghi ngờ Viator "1.000+" là "số láo" — thay vì trả lời cảm tính, đã đếm thật:

**Viator — không bị thổi phồng, thậm chí bảo thủ.** Lượt kiểm tra đầu dùng selector rộng `a[href*="/tours/Da-Nang/"]` trên 6 trang mẫu (1, 10, 20, 40, 60, 77) ra 51% trùng lặp — trông giống bị lặp/ảo. Nhưng đối chiếu DOM thấy selector đó lẫn cả link ở khu vực đề xuất/carousel lặp lại giữa các trang, không phải card sản phẩm thật (`a[class*="_productCard_"]`, mỗi trang đúng 24-25 card). Cào lại bằng selector đúng cho 73/77 trang (dừng ở 73 vì Viator bắt đầu trả về trang trắng — rate-limit tạm thời sau ~75 lượt điều hướng liên tục, không phải hết nội dung thật): 1.824 sản phẩm thô, trùng lặp chỉ ~4%, ra **1.752 sản phẩm riêng biệt**, và ngay tại trang 73 (gần cuối danh sách 77 trang) vẫn cho 24/25 sản phẩm hoàn toàn mới — không có dấu hiệu cạn dần. Kết luận: số nền tảng công bố ("1.000+") thực ra là con số **bảo thủ**, thực tế cao hơn. Có một điểm cần lưu ý khác (không phải "số láo" nhưng đáng ghi chú): ~7% kết quả là tour Hội An/Huế/TP.HCM được gắn kèm vì liên quan đến khách tìm "Da Nang" (di chuyển từ ĐN), không phải tour nằm hoàn toàn trong nội đô Đà Nẵng.

**Airbnb — phát hiện vấn đề thật, nhưng khác loại.** Không nghi Airbnb ban đầu vì số "309" là số cụ thể (không phải ngưỡng "X+"), nhưng khi kiểm tra lại cùng ngày để đối chiếu: load lại đúng URL `airbnb.com/s/Da-Nang/experiences`, không đổi bất kỳ filter/ngày/khách nào, buổi sáng ra "Explore 309 experiences in Da Nang", buổi chiều load lại 2 lần liên tiếp đều ra "Explore 200 experiences" — chênh 35% trong cùng một ngày, không có nguyên nhân nào quan sát được (nghi do cá nhân hoá/A-B test kết quả tìm kiếm phía Airbnb, không kiểm chứng được vì đây là hộp đen). Kết luận: số Airbnb tự công bố **không ổn định đủ để dùng làm tổng chính xác**, dù bản thân nó không phải dạng ngưỡng mơ hồ như GetYourGuide/Viator. Số đáng tin nhất vẫn là 185 experience đã lập hồ sơ chi tiết qua cào trực tiếp.

**GetYourGuide — chưa kết luận được.** Định làm quy trình giống Viator (đếm card sản phẩm thật thay vì tin số ngưỡng) nhưng trang bị Cloudflare "Just a moment..." chặn liên tục >1 phút mỗi lần thử trong lúc kiểm tra — nhiều khả năng do IP/profile đã bị gắn cờ sau khối lượng lớn thao tác tự động trong ngày (Viator 73 trang + ShowAround + GoWithGuide). Để ngỏ, thử lại vào phiên khác khi Cloudflare hạ mức cảnh giác.

**Bài học phương pháp:** một selector CSS quá rộng có thể tạo ảo giác "số bị thổi phồng" (trường hợp Viator) — luôn đối chiếu DOM để chắc chắn đang đếm đúng card sản phẩm, không phải link ở carousel/đề xuất trước khi kết luận. Ngược lại, một con số cụ thể (không phải ngưỡng "X+") vẫn có thể không đáng tin nếu nó dao động giữa các lần tải cùng ngày (trường hợp Airbnb) — "số cụ thể" không đồng nghĩa "số ổn định".
