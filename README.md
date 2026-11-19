# Japan News Video Factory

Máy dựng video tin tức Nhật Bản dạng dọc 1080 × 1920: ảnh thật, giọng đọc tiếng Nhật, phụ đề khớp với giọng. Lịch tự chạy mỗi sáng đã tắt. Mỗi video là một phiếu `[Tin Nhật] …`, giống các kênh khác của chủ repo.

## Dựng từ kịch bản (cách dùng chính)

1. Mở phiếu mới bằng mẫu **📰 Video tin Nhật (ảnh thật)**, dán kịch bản, bấm **Create**. Hoặc dán kịch bản vào một phiên chat Claude có kết nối repo này: Claude tự mở phiếu.
2. Không cần làm gì thêm. Claude dịch sát sang tiếng Nhật và chia cảnh (`stories/<tên>.json`), máy tìm ảnh thật trên Wikimedia Commons và trên web (báo, blog; ảnh trên web có thể có bản quyền, chủ kênh đã chấp nhận), Claude xem và chọn ảnh cho từng cảnh, máy tạo giọng đọc VOICEVOX:青山龍星 và dựng video, Claude kiểm tra từng cảnh. Mỗi bước xong đều báo trong phiếu; link video ở bình luận cuối.
3. Muốn sửa thì viết bình luận trong phiếu.

Kết quả nằm ở nhánh `renders`, thư mục `<tên>/`: video, phụ đề, `credits.txt` (nguồn ảnh để dán vào mô tả video), `caption.txt` (lời giới thiệu để đăng kèm video: tiêu đề, vài câu, hashtag), ảnh tĩnh; ảnh tìm được ở `<tên>/find/`. Mỗi lần đăng, thư mục được thay mới hoàn toàn và có `status.json` ghi lần chạy và commit. Chi tiết cho Claude: `CLAUDE.md`, `AGENT_JNEWS.md`.

**Tải video về máy:** mỗi tuần workflow **Dọn video cũ (nhánh renders)** xóa video của phiếu đã đóng quá 2 ngày hoặc không có hoạt động trong 14 ngày, khi đó link video hết hiệu lực. Video luôn nhẹ hơn 100 MB (giới hạn của GitHub); video dài hơn khoảng 1 phút 50 giây được nén nhiều hơn một chút.

**Cấu hình:** để GitHub gọi Claude sau mỗi bước, repo cần hai secret `CLAUDE_TASK_URL` và `CLAUDE_TASK_TOKEN` (cùng giá trị như ở `japan-video-factory`). Không có lượt chạy mỗi giờ: nếu Claude lỡ một lần gọi (ví dụ hết hạn mức), vào **Actions → Gọi Claude ngay → Run workflow**. Khi chưa gọi được Claude, máy ghi rõ điều đó trong phiếu kèm link nút bấm. Nhãn của phiếu được tạo bằng workflow **Tạo nhãn**.

## Ghi chú 17/11/2026: tìm ảnh tốt hơn (đã vào bản chính)

Vì video hay thiếu ảnh hợp, phần tìm ảnh được làm thêm ba việc. Phần này **đã vào `main` ngày 17/11/2026** (chủ kênh: "đưa tất cả các phần đã cải thiện lên nhánh chính đi"). Khi đưa vào chưa chạy thử trên GitHub: video đầu tiên sau ngày này là lần chạy thật đầu tiên, nên xem kỹ nhật ký bước tìm ảnh.

1. **Tìm theo tên người, tên nơi chốn** (`wiki:`): chỉ cần ghi tên một người, một nơi, một tòa nhà, máy lấy luôn các ảnh nói về chính người hay nơi đó trên Wikipedia và kho ảnh Wikimedia (tối đa 24 ảnh), có sẵn tên tác giả và giấy phép dùng tự do.
2. **Tìm ảnh chụp quanh một địa điểm** (`geo:`): ghi tọa độ và bán kính, máy lấy các ảnh chụp ở quanh đó.
3. **Nói rõ ảnh phải có gì**: Claude ghi thêm một câu tả bằng tiếng Anh sau từ khóa (ví dụ "một phụ nữ đang hát trên sân khấu lớn"); máy xem nhiều ảnh hơn, chấm điểm từng ảnh theo câu tả đó, giữ những ảnh đúng nhất và bỏ ảnh lạc đề. Nếu GitHub không cài được bộ chấm điểm thì máy tìm như cũ.

Ngoài ra máy tải vài ảnh cùng lúc nên nhanh hơn, không chờ lâu ở trang web chết, và khi Wikimedia báo "quá nhiều yêu cầu" thì dừng hỏi tiếp trong lượt đó (lượt sau tìm lại phần còn thiếu). Kịch bản cũ không đổi gì. Chưa chạy thử trên GitHub.

## Ghi chú 19/11/2026: chủ kênh đổi 6 luật

Chủ kênh đọc danh sách luật cứng và thấy mấy luật "ko hợp lí", rồi chọn lại như sau (áp dụng cho mọi kênh tiếng Nhật):

1. **Kịch bản chủ kênh gửi:** Claude được cắt, thêm, viết lại cho hay và cuốn hơn, giữ ý chính (trước: dịch sát, không sửa).
2. **Tin đồn:** kênh nào cũng được kể tin đồn và chi tiết chưa xác nhận, có câu kiểu "nghe nói" trong lời đọc và ghi chú đính chính (※) ở caption.
3. **Thêm thắt cho kịch tính:** được thêm cảm xúc, lời dẫn, cách kể. Điều duy nhất còn cấm: dựng ra sự kiện hay câu nói của người thật rồi kể như thật.
4. **Câu kết:** tự do, miễn hay (trước: phải quay về câu mở đầu, không được hỏi người xem).
5. **Giọng và nhạc của video chủ kênh gửi:** được dùng. Rủi ro đã nói: nhạc có bản quyền dễ bị YouTube nhận ra (tắt tiếng, mất tiền quảng cáo, gậy), và dùng càng nhiều của video gốc thì càng dễ bị coi là "nội dung dùng lại". Máy dựng hiện chưa chèn được tiếng của video gốc: phải làm thêm và có bản thử cho chủ kênh duyệt.
6. **Số ảnh mỗi cảnh:** cảnh dài hơn 6 giây thì phải có 2 ảnh, dưới 6 giây thì 1 ảnh cũng được (trước: cảnh nào cũng 2 ảnh).

## Ghi chú 19/11/2026: tìm ảnh rộng hơn, và bớt báo đỏ giả

Chủ kênh hỏi "có cách nào để tìm hình ảnh mở rộng ra ko" và chọn làm cả ba hướng; thêm ý "video tao gửi thì được dùng hình ảnh/video trong đó".

1. **Tìm web rộng hơn** (`web:`): mỗi lần tìm máy xem khoảng 55 ảnh (trước là 20) và giữ 20 ảnh (trước là 12). Ảnh nào trang gốc không cho tải thì máy lấy bản sao cùng cỡ mà Yahoo! JAPAN đang giữ; nguồn ghi vẫn là trang gốc.
2. **Lấy ảnh trong một bài báo** (`page:` + link bài): máy lấy các ảnh lớn của đúng bài đó, tối đa 20 ảnh. Thử trên 8 trang báo: mỗi bài được từ 2 đến 20 ảnh.
3. **Kho lưu trữ Nhật** (`jps:`): Japan Search, nơi gộp thư viện quốc hội, thư viện và kho lưu trữ các thành phố, các trường đại học… Chỉ lấy ảnh được phép dùng (hết bản quyền hoặc giấy phép tự do), có ghi nơi giữ và giấy phép. Hợp với chuyện xưa (tranh, ảnh cũ, hiện vật); nên tìm theo sự việc, địa danh, đồ vật chứ không theo tên người. Nguồn này khiêm tốn: chạy thử 6 lần tìm trên GitHub thì 2 lần được 12 ảnh (động đất Kantō, tượng đất 土偶), 2 lần được 1–2 ảnh, 2 lần tìm theo tên người không được ảnh nào. Ảnh của các bảo tàng quốc gia (ColBase) và bảo tàng Tokyo hiện chưa tải được (link trong danh mục của họ bị hỏng hoặc bị chặn).
4. **Hình từ video chủ kênh gửi**: `tools/video_frames.py` bày mỗi cảnh của video thành một ô trên một tấm ảnh để Claude chọn, rồi cất hình đã chọn vào repo (ghi nguồn 元動画), cắt bỏ được phần chữ hay nền mờ. Đoạn video chuyển động thì chủ kênh cũng cho dùng, nhưng khung hình hiện chỉ hiện ảnh tĩnh: muốn chèn đoạn video phải làm thêm và có bản thử cho chủ kênh duyệt.
5. **Bớt báo đỏ giả**: nguồn ảnh không bao giờ lấy được (tên không có trong Wikidata, ảnh mà trang web từ chối) chỉ còn là một dòng ghi chú; máy không báo lỗi và không thử lại. Nguồn tạm thời không trả lời thì vẫn báo đỏ để chạy lại.

Không thêm Thư viện Quốc hội Mỹ: chạy thử trên GitHub mất 35 giây cho một lần hỏi và bị từ chối ngay lần hỏi thứ hai; các bộ ảnh hết bản quyền nổi tiếng của họ đã có trong Wikimedia Commons, nơi máy vẫn tìm.

## Ghi chú 17/11/2026: hiệu ứng hình (chủ kênh đã đồng ý bật cho kênh này)

Từ 17/11/2026, mọi video **mới** của kênh dùng bốn hiệu ứng của bản B (video Chiêu Hòa – Kuroyanagi đã gửi trong chat): máy quay có nhịp nhanh chậm, ảnh có chiều sâu mức nhẹ, tiêu đề và câu trích hiện từng dòng còn phụ đề đậm dần theo đúng lời đọc, và phông chữ Shippori Mincho B1 (phông miễn phí, giấy phép SIL OFL). Claude bật bằng dòng `"fx"` trong file kịch bản. Video cũ không đổi gì; muốn làm lại một video cũ với hiệu ứng thì nói trong phiếu.

- Phụ đề giờ đậm dần theo thời điểm thật của từng chữ do máy tạo giọng báo lại, không còn ước lượng theo số chữ.
- Ảnh phẳng (tài liệu, trang báo, ảnh ghép, biểu đồ) không dùng chiều sâu, để khỏi bị méo.
- Nếu GitHub không cài được thư viện hay không tải được phông chữ thì video vẫn được dựng, chỉ thiếu hiệu ứng đó (ảnh phẳng như cũ, hoặc phông chữ thường); Claude sẽ nói rõ trong phiếu.
- Mỗi lần sửa mã, GitHub tự dựng thử ảnh mẫu có bật hiệu ứng để chắc là thư viện, mô hình chiều sâu và phông chữ chạy được trên đó. Phần này chưa chạy thử trên GitHub lần nào; lần đẩy mã đầu tiên sẽ cho biết.

## Luồng tự tìm tin (chạy tay)

1. Đọc thông cáo từ [Ngân hàng Trung ương Nhật Bản](https://www.boj.or.jp/rss/whatsnew.xml) [Bộ Kinh tế, Thương mại và Công nghiệp Nhật Bản](https://www.meti.go.jp/press/index.html) và [Cục Thống kê Nhật Bản](https://www.stat.go.jp/data/cpi/sokuhou/tsuki/index-z.html). Nếu thiếu tin đủ mới và có đủ dữ kiện, ghi lý do trong run summary.
2. Dùng mẫu lời dẫn tiếng Nhật bám theo thông cáo. Tin về lãi suất và CPI có phần giải thích theo loại số liệu. Những tin khác dùng các câu trích có ghi nguồn từ thông cáo. Mục tiêu là 60–90 giây. Bản tin có thể ngắn hơn khi thông cáo ngắn.
3. Tìm ảnh đúng cơ quan trên Wikimedia Commons và lọc theo giấy phép. Ảnh được ghi rõ là ảnh tư liệu (資料写真), kèm credit. Các cảnh số liệu và tài liệu dùng nội dung gốc, ngày công bố và tên cơ quan. Khi thiếu ảnh phù hợp, cảnh mở dùng thẻ thông cáo.
4. Tạo giọng đọc tiếng Nhật với VOICEVOX:青山龍星, canh phụ đề theo lời đọc rồi xuất MP4. Video được lưu trong Actions để tải về.

## Chạy thử

Mở [Actions → Japan News Video](https://github.com/maihaianh2911-bit/japan-news-video-factory/actions/workflows/news-video.yml) rồi chọn **Run workflow**.

| Chế độ | Đầu vào |
| --- | --- |
| `story` | Tên file trong `stories/` (không có `.json`): tìm ảnh hoặc dựng video, theo `stage` trong file |
| `daily` | Tìm tin trong ngày hoặc hôm trước theo giờ Nhật |
| `demo` | Quyết định lãi suất BOJ ngày 24/01/2025, đánh dấu là tin cũ để thử dựng |
| `source` | Dán link thông cáo HTML của BOJ, METI hoặc trang CPI toàn quốc vào `source_url` |

Đẩy mã (không phải kịch bản) lên `main` chạy một bước kiểm tra không cần mạng: dựng ảnh tĩnh và 3 giây video thử của `stories/mau-boj.json`, không tạo giọng, không đọc trang BOJ. Video mẫu `demo` chỉ chạy khi chọn tay.

Khi job xong, tải `japan-news-video-<run>-<n>` trong **Artifacts**. Artifact được giữ 14 ngày. Chạy thử bằng nguồn cũ sẽ hiển thị ngày công bố trên video.

## Chạy trên máy

Cần Python 3.12, FFmpeg, font Noto Sans CJK JP và Docker. VOICEVOX chạy cục bộ, luồng cơ bản không cần API key.

```sh
python -m pip install -r requirements.txt
docker run --rm -p 127.0.0.1:50021:50021 voicevox/voicevox_engine:cpu-0.26.1
```

Mở terminal khác rồi chạy:

```sh
python -m news --demo
python -m news --plan-only
python -m news --url 'https://www.boj.or.jp/mopo/mpmdeci/state_2025/k250124a.htm'
```

Xem trước một kịch bản (không cần VOICEVOX, cần font Noto CJK và `budoux` trong `requirements.txt`):

```sh
python -m news.custom stories/mau-boj.json            # kiểm tra file kịch bản
python -m news --story stories/mau-boj.json --pictures <thư mục find> --stills /tmp/stills
```

`--plan-only` in nguồn và lời dẫn. Chạy dựng đầy đủ sẽ lưu kết quả trong `dist/`.
