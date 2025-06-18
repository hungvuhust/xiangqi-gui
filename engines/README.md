# Hướng dẫn cài đặt Engine cờ tướng

Để sử dụng Xiangqi GUI, bạn cần tải và cài đặt các engine cờ tướng hỗ trợ giao thức UCCI.

## Engine được khuyến nghị

### 1. Pikafish
- **Mô tả**: Engine cờ tướng mạnh nhất hiện tại, dựa trên Stockfish
- **Tải về**: [GitHub - Pikafish](https://github.com/official-pikafish/Pikafish)
- **Cài đặt**: 
  1. Tải file executable cho hệ điều hành của bạn
  2. Đặt file `pikafish` hoặc `pikafish.exe` vào thư mục `engines/`
  3. Đảm bảo file có quyền thực thi: `chmod +x pikafish`

### 2. ElephantEye (象眼)
- **Mô tả**: Engine mã nguồn mở phổ biến
- **Tải về**: [XQbase.com](http://www.xqbase.com)
- **Cài đặt**:
  1. Tải ElephantEye Engine
  2. Đặt file `eleeye` vào thư mục `engines/`
  3. Cấp quyền thực thi nếu cần

### 3. Cyclone
- **Mô tả**: Engine nhẹ và nhanh
- **Tải về**: Tìm kiếm "Cyclone Xiangqi Engine"
- **Cài đặt**: Tương tự các engine khác

## Cấu trúc thư mục engines

```
engines/
├── README.md          # File này
├── pikafish           # Pikafish engine (Linux/Mac)
├── pikafish.exe       # Pikafish engine (Windows)
├── eleeye             # ElephantEye engine
├── cyclone            # Cyclone engine
└── books/             # Thư mục chứa file khai cuộc (tùy chọn)
    ├── BOOK.DAT
    └── opening.bin
```

## Kiểm tra engine

Để kiểm tra engine hoạt động đúng:

1. Mở terminal/command prompt
2. Chuyển đến thư mục engines: `cd engines`
3. Chạy engine: `./pikafish` (Linux/Mac) hoặc `pikafish.exe` (Windows)
4. Gõ `ucci` và nhấn Enter
5. Engine sẽ trả về `ucciok` nếu hoạt động đúng
6. Gõ `quit` để thoát

## Giao thức UCCI

Các engine phải hỗ trợ giao thức UCCI (Universal Chinese Chess Interface):

### Lệnh cơ bản:
- `ucci` - Khởi tạo engine
- `isready` - Kiểm tra engine sẵn sàng  
- `position fen <fen_string>` - Thiết lập vị trí
- `go depth <n>` - Tìm kiếm với độ sâu n
- `go movetime <ms>` - Tìm kiếm trong thời gian ms
- `stop` - Dừng tìm kiếm
- `quit` - Thoát engine

### Phản hồi từ engine:
- `ucciok` - Engine đã khởi tạo
- `readyok` - Engine sẵn sàng
- `bestmove <move>` - Nước đi tốt nhất
- `info depth <n> score <score> ...` - Thông tin phân tích

## Troubleshooting

### Engine không khởi động:
1. Kiểm tra đường dẫn file engine
2. Kiểm tra quyền thực thi: `ls -la engines/`
3. Thử chạy engine trực tiếp từ terminal

### Engine không phản hồi:
1. Kiểm tra engine có hỗ trợ UCCI không
2. Thử gửi lệnh `ucci` thủ công
3. Kiểm tra log trong GUI

### Lỗi permissions (Linux/Mac):
```bash
chmod +x engines/pikafish
chmod +x engines/eleeye
```

## Cấu hình Engine trong GUI

1. Mở Xiangqi GUI
2. Menu Engine → Tải Engine...
3. Chọn file executable của engine
4. Engine sẽ xuất hiện trong danh sách và sẵn sàng sử dụng

## Tùy chỉnh cài đặt

Chỉnh sửa file `config/engines.json` để:
- Thêm engine mới
- Thay đổi cài đặt mặc định
- Cấu hình tham số engine

Ví dụ thêm engine mới:
```json
{
  "name": "MyEngine",
  "path": "./engines/myengine",
  "protocol": "ucci",
  "description": "Engine tự tạo"
}
``` 