# Japan News Video Factory

Lịch tự chạy mỗi sáng đã tắt: video chỉ được dựng khi bấm **Run workflow**. Khi chạy, GitHub Actions tìm một tin chính sách hoặc kinh tế Nhật Bản, soạn lời dẫn tiếng Nhật, tìm hình và dựng một video dọc 1080 × 1920. Artifact chứa video H.264/AAC, ảnh bìa, phụ đề SRT, lời dẫn và danh sách nguồn.

## Dựng từ kịch bản (cách dùng chính)

Dán kịch bản vào một phiên chat Claude có kết nối repo này. Claude viết `stories/<tên>.json`, máy tìm ảnh thật trên Wikimedia Commons theo từng cảnh, Claude xem và chọn ảnh, máy tạo giọng đọc và dựng video. Kết quả nằm ở nhánh `renders`, thư mục `<tên>/` (video, phụ đề, nguồn ảnh). Chi tiết: `CLAUDE.md`.

## Luồng tự tìm tin (chạy tay)

1. Đọc thông cáo từ [Ngân hàng Trung ương Nhật Bản](https://www.boj.or.jp/rss/whatsnew.xml) [Bộ Kinh tế, Thương mại và Công nghiệp Nhật Bản](https://www.meti.go.jp/press/index.html) và [Cục Thống kê Nhật Bản](https://www.stat.go.jp/data/cpi/sokuhou/tsuki/index-z.html). Nếu thiếu tin đủ mới và có đủ dữ kiện, ghi lý do trong run summary.
2. Dùng mẫu lời dẫn tiếng Nhật bám theo thông cáo. Tin về lãi suất và CPI có phần giải thích theo loại số liệu. Những tin khác dùng các câu trích có ghi nguồn từ thông cáo. Mục tiêu là 60–90 giây. Bản tin có thể ngắn hơn khi thông cáo ngắn.
3. Tìm ảnh đúng cơ quan trên Wikimedia Commons và lọc theo giấy phép. Ảnh được ghi rõ là ảnh tư liệu (資料写真), kèm credit. Các cảnh số liệu và tài liệu dùng nội dung gốc, ngày công bố và tên cơ quan. Khi thiếu ảnh phù hợp, cảnh mở dùng thẻ thông cáo.
4. Tạo giọng đọc tiếng Nhật với VOICEVOX:青山龍星, canh phụ đề theo lời đọc rồi xuất MP4. Video được lưu trong Actions để tải về.

## Chạy thử

Mở [Actions → Japan News Video](https://github.com/maihaianh2911-bit/japan-news-video-factory/actions/workflows/news-video.yml) rồi chọn **Run workflow**.

| Chế độ | Đầu vào |
| --- | --- |
| `daily` | Tìm tin trong ngày hoặc hôm trước theo giờ Nhật |
| `demo` | Quyết định lãi suất BOJ ngày 24/01/2025, đánh dấu là tin cũ để thử dựng |
| `source` | Dán link thông cáo HTML của BOJ, METI hoặc trang CPI toàn quốc vào `source_url` |

Khi job xong, tải `japan-news-video-<run>` trong **Artifacts**. Artifact được giữ 14 ngày. Chạy thử bằng nguồn cũ sẽ hiển thị ngày công bố trên video.

## Chạy trên máy

Cần Python 3.12, FFmpeg, font Noto Sans CJK JP và Docker. VOICEVOX chạy cục bộ, luồng cơ bản không cần API key.

```sh
python -m pip install -r requirements.txt
docker run --rm -p 127.0.0.1:50021:50021 voicevox/voicevox_engine:cpu-latest
```

Mở terminal khác rồi chạy:

```sh
python -m news --demo
python -m news --plan-only
python -m news --url 'https://www.boj.or.jp/mopo/mpmdeci/state_2025/k250124a.htm'
```

`--plan-only` in nguồn và lời dẫn. Chạy dựng đầy đủ sẽ lưu kết quả trong `dist/`.
