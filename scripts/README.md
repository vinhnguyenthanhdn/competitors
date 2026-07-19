# Quy trình cào thêm tour đối thủ

Kiến trúc: **dữ liệu tách khỏi trình bày**. `data/tours-data.js` là nguồn duy
nhất; `toan-bo-tour-hdv.html` và `so-sanh-gia-tour.html` chỉ load file này
(`<script src="data/tours-data.js">`, không phải `fetch()` — tránh lỗi CORS
khi mở trực tiếp bằng `file://`) và tự render card/bảng/filter/count bằng JS.
**Không sửa HTML tay khi cào thêm.**

## Quy trình cào thêm tour cho platform đã có

1. Mở Chrome thật qua skill `astraler-agent-browser`, connect `agent-browser`.
2. Mở trang danh sách của platform, dùng snippet tương ứng trong
   `scripts/extractors/<platform>.js` (mỗi file có comment ghi URL + cách chạy):
   ```bash
   cat scripts/extractors/airbnb.js | agent-browser eval --stdin --json > data/raw/scrapes/airbnb_<mô-tả>.json
   ```
3. Kết quả thô có 2 dạng tuỳ platform:
   - Airbnb: `{id, title, text, img}`
   - GetYourGuide/Viator/ToursByLocals: `{href, text, img}`
4. Parse `text` thành các trường chuẩn hoá (xem `parse_price`/`classify` trong
   `build_unified_data.py` để biết logic quy đổi giá + phân nhóm điểm đến).
   Viết ra 1 file JSON mới dạng **card chuẩn hoá**:
   ```json
   [
     {
       "platform": "Airbnb Experiences",
       "color": "#E84068",
       "title": "...",
       "img": "https://...",
       "href": "https://www.airbnb.com/experiences/123456",
       "price": "₫364,000",
       "duration": "8 - 9 hours",
       "rating": "★ 5.0 (2,099)",
       "cardText": "..."
     }
   ]
   ```
   Lưu vào `data/raw/cards-<mô-tả>.json` (bắt buộc prefix `cards-` để script build nhận diện).
5. Chạy lại:
   ```bash
   python3 scripts/build_unified_data.py
   ```
   Script tự động: gộp mọi `data/raw/cards-*.json`, khử trùng theo
   `(platform, title, href)` — **không dedupe theo `href` một mình**, vì
   ShowAround/Tubudd/GoWithGuide dùng chung 1 href hồ sơ chung cho mọi guide —
   tính `vnd`/`unit`/`group` cho từng tour, ghi ra `data/tours-data.js`.
6. Mở lại 2 trang HTML bằng Chrome, kiểm tra tổng số card + filter + bảng giá
   không cần sửa gì thêm (tự động cập nhật từ data mới).

## Cào thêm platform hoàn toàn mới

1. Viết 1 file JS mới trong `scripts/extractors/<platform>.js` (theo mẫu các
   file hiện có — tìm selector ổn định nhất cho card: thường là 1 thẻ `<a>`
   bao trọn ảnh + tên + giá, lấy `href`, `innerText`, `querySelector('img').src`).
2. Làm theo các bước "cào thêm cho platform đã có" ở trên.
3. Nếu platform là **marketplace hồ sơ HDV** (khách chọn guide, đặt theo
   giờ/ngày, không phải tour lịch trình cố định — như ShowAround/Tubudd/
   GoWithGuide) thì thêm tên platform vào `GUIDE_PROFILE_PLATFORMS` trong
   `build_unified_data.py` để nó luôn được xếp vào nhóm "Thuê HDV theo giờ"
   thay vì bị phân loại nhầm theo từ khoá trong tên.

## Giới hạn đã biết (đọc trước khi cào thêm để khỏi mất công lặp lại)

- **Airbnb Experiences**: mỗi lượt xem (trang gốc, hoặc filter theo category
  tag) chỉ render tối đa ~20 card, không có phân trang/infinite-scroll thật.
  Cách duy nhất để gom thêm là đổi *view*: 3 tổ hợp 4-tag, 12 tag đơn lẻ, và
  search riêng theo thành phố lân cận (Hội An, Huế — cùng place_id taxonomy).
  Đổi ngày check-in / số khách **không** đổi kết quả (đã test, 0 tour mới).
- **GetYourGuide / Viator**: chặn bot bằng Cloudflare — chỉ qua được bằng
  Chrome thật (profile đã có session), đợi vài giây sau khi `open()`. GYG có
  nút "Show more" (bấm nhiều lần, mỗi lần +15-18 card). Viator có phân trang
  URL `/Da-Nang/d4680-ttd/<số trang>` (77 trang, ~40-50 unique/trang).
- **ToursByLocals**: chỉ có đúng 2 trang (`?page=2`), gộp lại đúng bằng tổng
  thật platform tự công bố (117) — đã cào hết 100%, không cần cào thêm.
- **ShowAround**: có trần hiển thị ~32 hồ sơ/lượt xem giống Airbnb (không phải
  do bấm nhầm nút review như từng nghi ngờ trước đây) — nút "Show More" của
  lưới guide (`button[class*="ShowMoreButton"]`) chỉ tăng từ 16 lên 32 rồi biến
  mất, dù trang tự công bố tổng lớn hơn (vd 74). Workaround: mở "Advanced
  Filters" → lọc theo Gender (Male/Female/Couple) → mỗi lượt lọc lại có trần
  32 riêng nhưng là tập con khác nhau → hợp nhất theo **href thật của từng hồ
  sơ** (`a[href*="-vietnam-"]`, KHÔNG dùng href trang danh sách chung) sẽ ra
  nhiều hơn hẳn so với chỉ dùng view mặc định. Bộ lọc Activities và Languages
  trên ShowAround **không hoạt động** (áp dụng vẫn trả về full tổng, coi như
  no-op, đừng mất thời gian thử). Couple luôn ra 0. Lưu ý quan trọng: nhiều
  guide trùng tên (vd 2 người tên "Trang", "Miu"...) — nếu dùng href trang
  danh sách chung làm key dedupe sẽ mất dữ liệu, phải dùng href hồ sơ thật.
- **GoWithGuide**: là mô hình lai, có **2 view tách biệt** dễ bỏ sót nếu chỉ
  cào 1 view — `/vietnam/da-nang/tours` (catalog tour đóng gói giá cố định) và
  `/vietnam/da-nang/guides` (hồ sơ HDV đặt theo giờ). View tours mặc định
  (`/s?city=da-nang&t=tours`) chỉ hiển thị một phần tour thật có — phải duyệt
  qua từng link category ở trang `/vietnam/da-nang/tours` (7 category:
  highlights, art-culture-historical, food-drink, nature-outdoor,
  off-the-beaten-path, day-trip, nightlife) rồi hợp nhất theo href mới ra đủ
  catalog. Không có trần ~32 như Airbnb/ShowAround, mỗi category page hiển thị
  đủ số tour của nó, không cần Show More.
- **Klook**: có DataDome (CAPTCHA riêng, khác Cloudflare) — khi gặp trang
  CAPTCHA `geo.captcha-delivery.com`, không có cách bypass hợp lệ, phải bỏ qua
  lượt cào đó và thử lại sau, không được tự động giải CAPTCHA.
- **Ong Vò Vẽ**: không có bộ lọc theo tỉnh/thành hoạt động được trên site,
  và số liệu marketing tự công bố ở trang chủ (vd "+1999 HDV") không nhất
  quán giữa các lần kiểm tra — không dùng số này làm tổng, chỉ đếm thủ công
  qua các link hồ sơ đã xác định được.

## File liên quan

- `scripts/build_unified_data.py` — script build chính, chứa `classify()` +
  `parse_price()` (logic phân nhóm điểm đến + quy đổi VNĐ, dùng chung cho mọi
  platform).
- `scripts/extractors/*.js` — snippet cào theo từng platform.
- `data/raw/cards-*.json` — dữ liệu đã chuẩn hoá, input cho build script.
- `data/raw/scrapes/*.json` — dữ liệu thô từng lượt cào (chỉ để truy vết
  nguồn, build script không đọc các file này).
- `data/tours-data.js` — output cuối, 2 trang HTML load trực tiếp.
- `docs/scraping-refactor-plan.md` — nhật ký + kế hoạch của lần refactor này.
