# Setup Neo4j & Import Dữ Liệu GraphRAG

Tài liệu này ghi lại cách setup Cơ sở dữ liệu đồ thị Neo4j và nạp (import) kết quả output Parquet của GraphRAG vào Neo4j để trực quan hóa.

## 1. Cài đặt Driver Python Neo4j
Để script Python có thể kết nối đến Neo4j, cần cài đặt thư viện driver `neo4j` vào môi trường ảo:
```bash
uv add neo4j
```

## 2. Setup Cơ sở dữ liệu Neo4j bằng Docker

### ⚠️ BẪY SETUP (Lưu ý quan trọng)
Neo4j phiên bản mới (`latest`) mặc định yêu cầu độ dài mật khẩu tối thiểu là **8 ký tự**. Nếu chạy lệnh docker mặc định với mật khẩu `123456` (6 ký tự) như cấu hình mặc định trong file script:
```bash
docker run -d --name neo4j-local -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/123456 neo4j:latest
```
Container sẽ khởi động thất bại (Status: `Exited (1)`) với lỗi:
> *Invalid value for password. The minimum password length is 8 characters.*

### Giải pháp khắc phục:
Thêm cấu hình bỏ qua giới hạn độ dài mật khẩu bằng cách truyền biến môi trường `-e NEO4J_dbms_security_auth__minimum__password__length=6`.

Lệnh chạy Docker hoàn chỉnh:
```bash
docker run -d \
  --name neo4j-local \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/123456 \
  -e NEO4J_dbms_security_auth__minimum__password__length=6 \
  neo4j:latest
```

*   **Giao diện Web console**: `http://localhost:7474`
*   **Cổng Bolt kết nối**: `bolt://localhost:7687`
*   **Tài khoản đăng nhập**: `neo4j` / `123456`

---

## 3. Chạy script Import dữ liệu

### ⚠️ Đường dẫn thực thi (Lưu ý thư mục làm việc)
*   **Lỗi thường gặp**: Nếu đang đứng ở thư mục `scripts` và chạy `uv run python scripts/import_to_neo4j.py`, Python sẽ tìm file tại `scripts/scripts/...` và báo lỗi `No such file or directory`.
*   **Cách chạy đúng**: Đứng ở **thư mục gốc** (`/Users/quoctang/workspaces/master/graphrag`) và thực thi lệnh:
```bash
uv run python scripts/import_to_neo4j.py --output ./output
```

Nếu muốn chạy trực tiếp khi đang ở trong thư mục `scripts`, cần trỏ lại đường dẫn output ra bên ngoài:
```bash
uv run python import_to_neo4j.py --output ../output
```

### Kết quả import thành công:
```
Đọc parquet từ: /Users/quoctang/workspaces/master/graphrag/output
  + entities: 98 dòng
  + relationships: 106 dòng
  + communities: 19 dòng
  + community_reports: 19 dòng
  -> đã tạo node Entity
  -> đã tạo quan hệ RELATED
  -> đã tạo node Community + IN_COMMUNITY
  -> đã gắn community reports

Xong! Mở http://localhost:7474 và chạy:  MATCH (n) RETURN n LIMIT 200
```

---

## 4. Xem dữ liệu trên Neo4j
1. Truy cập **[http://localhost:7474](http://localhost:7474)** bằng trình duyệt.
2. Đăng nhập với tài khoản `neo4j` / `123456`.
3. Nhập và chạy truy vấn Cypher để hiển thị đồ thị:
   ```cypher
   MATCH (n) RETURN n LIMIT 200
   ```
