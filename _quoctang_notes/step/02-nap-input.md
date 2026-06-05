# Nạp input (tải dữ liệu mẫu vào `input/`)

## Lệnh tải
```shell
mkdir -p input
curl -sSL https://www.gutenberg.org/cache/epub/24022/pg24022.txt -o ./input/book.txt
```

Ghi chú:
- `-sSL`: `-s` im lặng (không hiện progress bar), `-S` vẫn báo lỗi nếu fail,
  `-L` đi theo redirect (Gutenberg hay redirect).
- `-o ./input/book.txt`: lưu ra file đích.
- Trong project này **không cần** `mkdir -p input` vì `graphrag init` đã tạo sẵn `input/`.

## Dữ liệu tải về
- ID 24022 trên Project Gutenberg = **A Christmas Carol** (Charles Dickens).
- Kích thước ~**189 KB**, 3976 dòng. Public domain.
- Đây là bộ dữ liệu mẫu trong getting-started của GraphRAG.

## Vị trí project
Project này được `init` ngay tại **repo root** (`settings.yaml`, `.env`, `input/`, `prompts/`
đều nằm ở `/home/quoctang/my_projects/graphrag/`). Nên `input/` = `./input/` ở root.

## Điều kiện để `index` đọc được
- `settings.yaml` phải có `input.type: text` (mặc định init ra là `text`).
- Với `type: text`, GraphRAG tự đọc **mọi file `.txt`** trong thư mục `input/`.
- Các type khác: `csv`, `json`, `jsonl`.

## Bước tiếp theo
1. Điền API key thật vào `.env` (đang là `GRAPHRAG_API_KEY=<API_KEY>`).
2. `uv run poe index`
3. `uv run poe query`

Xem thêm: [[01-graphrag-init]] (lệnh init tạo khung project).
