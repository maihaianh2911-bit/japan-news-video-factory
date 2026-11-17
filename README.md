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

## Ghi chú 17/11/2026: hiệu ứng hình thử nghiệm (chỉ ở nhánh `claude/stoic-darwin-utl7qq`, chưa vào bản chính)

Bản B của video Chiêu Hòa – Kuroyanagi (đã gửi chủ kênh trong chat ngày 17/11) dùng bốn thứ, bật bằng `"fx"` trong file kịch bản, mặc định tắt: máy quay có nhịp nhanh chậm (`motion`), ảnh có chiều sâu mức nhẹ (`depth`), tiêu đề và câu trích hiện từng dòng còn phụ đề đậm dần theo lời đọc (`text`), phông chữ Shippori Mincho B1 (`face`). Kịch bản không có `"fx"` dựng ra y như cũ (đã so 6 khung hình của `mau-boj`). **Chưa vào `main`** vì chủ kênh chưa nói có dùng cho kênh này không, và trên GitHub còn thiếu: tải phông chữ, cài thư viện cho chiều sâu, lấy thời điểm thật của từng chữ từ máy tạo giọng (hiện phụ đề đậm dần theo ước lượng số chữ).

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
