# Xiangqi GUI - Game Cờ Tướng

Game cờ tướng sử dụng PyQt5 với engine UCI/UCCI bên ngoài, hỗ trợ phân tích engine và gợi ý nước đi.

## Tính năng chính

### 🎮 Gameplay
- **Bàn cờ tương tác**: Click để di chuyển quân cờ với validation luật chơi đầy đủ
- **Undo/Redo**: Hoàn tác và làm lại nước đi với phím tắt (Ctrl+Z / Ctrl+Y)
- **Move validation**: Kiểm tra luật cờ tướng đầy đủ bao gồm:
  - Luật di chuyển từng quân cờ
  - Kiểm tra chiếu tướng
  - Luật "tướng đối mặt"
  - Phát hiện chiếu bí và hòa cờ

### 🤖 Engine Integration
- **Multi-engine support**: Hỗ trợ nhiều engine khác nhau
- **UCCI Protocol**: Giao tiếp thread-safe với engine cờ tướng chuẩn
- **Engine hints**: Gợi ý nước đi tốt nhất với mũi tên màu sắc
- **Continuous analysis**: Chế độ phân tích liên tục với depth cao
- **Dual arrow system**: 
  - Mũi tên chính cho bestmove (tím/xanh dương tùy lượt)
  - Mũi tên phụ cho ponder move (trong suốt, đứt nét)

### 📊 Analysis Features
- **Engine analysis panel**: Hiển thị chi tiết:
  - Depth (độ sâu tìm kiếm)
  - Evaluation score (điểm đánh giá với màu sắc)
  - Nodes và NPS (tốc độ tính toán)
  - Principal Variation (biến thể chính)
  - Time spent (thời gian tính toán)
- **Real-time updates**: Cập nhật thông tin phân tích theo thời gian thực
- **Position setup**: Thiết lập vị trí từ FEN notation

### 🎨 User Interface
- **Modern GUI**: Giao diện PyQt5 đẹp mắt và responsive
- **Move history**: Lịch sử nước đi với notation chuẩn
- **Status updates**: Thông báo trạng thái chi tiết
- **Toolbar shortcuts**: Các nút nhanh cho tính năng chính
- **Menu system**: Menu đầy đủ với phím tắt

### 🔧 Technical Features
- **Thread-safe communication**: Giao tiếp engine không block UI
- **Memory management**: Quản lý memory engine an toàn
- **Error handling**: Xử lý lỗi engine và exception robust
- **Coordinate conversion**: Chuyển đổi tọa độ board/engine chính xác
- **Resource cleanup**: Dọn dẹp resource khi đóng ứng dụng

## Cấu trúc thư mục

```
xiangqi-gui/
├── main.py                 # Entry point của ứng dụng
├── requirements.txt        # Dependencies
├── config/
│   ├── __init__.py
│   ├── settings.py        # Cấu hình game
│   └── engines.json       # Danh sách engine
├── src/
│   ├── gui/
│   │   ├── main_window.py      # Cửa sổ chính với engine integration
│   │   ├── board_widget.py     # Widget bàn cờ với dual arrow system
│   │   ├── game_info_widget.py # Widget thông tin game và engine analysis
│   │   └── dialogs/
│   │       └── fen_dialog.py   # Dialog setup position
│   ├── core/
│   │   └── game_state.py      # Logic game với undo/redo
│   ├── engine/
│   │   └── ucci_protocol.py   # Thread-safe UCCI protocol
│   └── utils/
│       ├── constants.py       # Hằng số game
│       └── svg_renderer.py    # SVG rendering utilities
├── assets/
│   ├── images/
│   │   ├── pieces/           # Hình ảnh quân cờ PNG
│   │   │   ├── red/          # Quân đỏ (rK, rA, rB, rN, rR, rC, rP)
│   │   │   └── black/        # Quân đen (bK, bA, bB, bN, bR, bC, bP)
│   │   └── board/
│   │       └── xiangqiboard_.png  # Nền bàn cờ
│   └── sounds/              # Âm thanh (tùy chọn)
├── engines/                 # Engine executables
│   └── Fairy-Stockfish/     # Engine mặc định
└── tests/                   # Unit tests
```

## Hướng dẫn sử dụng

### 🚀 Khởi động
```bash
pip install -r requirements.txt
python main.py
```

### 🎯 Chơi cờ
1. **New Game**: Bắt đầu ván mới
2. **Di chuyển**: Click quân cờ rồi click ô đích
3. **Undo/Redo**: Ctrl+Z để hoàn tác, Ctrl+Y để làm lại
4. **Load Engine**: Chọn engine từ menu hoặc toolbar

### 🔍 Engine Features
1. **Load Engine**: Chọn file engine executable (Fairy-Stockfish khuyến nghị)
2. **Enable Hints**: Bật gợi ý để thấy mũi tên bestmove
3. **Analysis Mode**: Bật phân tích liên tục để theo dõi evaluation
4. **Engine Panel**: Xem thông tin chi tiết depth, score, nodes, PV

### 📋 FEN Support
- **Copy FEN**: Sao chép position hiện tại
- **Load FEN**: Thiết lập position từ FEN string
- **Engine sync**: Engine tự động đồng bộ với position mới

## Engine được đề xuất

- **Fairy-Stockfish**: Engine đa variant mạnh, hỗ trợ Xiangqi/UCCI
- **Pikafish**: Engine cờ tướng chuyên dụng
- **ElephantEye**: Engine mã nguồn mở Trung Quốc

## Công nghệ sử dụng

- **PyQt5**: GUI framework với signals/slots thread-safe
- **Subprocess**: Giao tiếp engine process
- **Threading**: Xử lý engine không đồng bộ
- **UCCI Protocol**: Giao thức chuẩn cho engine cờ tướng
- **FEN Notation**: Format position chuẩn

## Phím tắt

- `Ctrl+N`: Game mới
- `Ctrl+Z`: Hoàn tác nước đi
- `Ctrl+Y`: Làm lại nước đi
- `Ctrl+H`: Bật/tắt gợi ý engine
- `Ctrl+A`: Bật/tắt phân tích liên tục
- `Ctrl+L`: Load engine
- `Ctrl+C`: Copy FEN position
- `F1`: Về ứng dụng

## Troubleshooting

### Engine không hoạt động
- Kiểm tra file engine executable có quyền thực thi
- Đảm bảo engine hỗ trợ UCCI protocol
- Xem console log để debug

### Performance issues
- Giảm depth analysis nếu engine chậm
- Tắt continuous analysis khi không cần
- Kiểm tra RAM usage của engine process

### UI freezing
- Ứng dụng sử dụng thread-safe communication
- Nếu vẫn freeze, restart và báo bug

## Development

Ứng dụng được thiết kế modular với:
- **Clean separation**: GUI/Core/Engine tách biệt
- **Thread safety**: Engine communication không block UI
- **Error handling**: Robust exception handling
- **Memory management**: Proper resource cleanup
- **Extensible**: Dễ thêm engine và features mới 