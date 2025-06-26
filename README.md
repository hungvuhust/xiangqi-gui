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
├── main.py                    # Entry point của ứng dụng
├── requirements.txt           # Dependencies Python
├── setup.py                   # Setup cho ROS2 package
├── package.xml               # ROS2 package manifest
├── saved_position.fen        # Position đã lưu
├── shared_game_state.json    # Trạng thái game chia sẻ
├── config/
│   ├── __init__.py
│   ├── settings.py           # Cấu hình game
│   └── engines.json          # Danh sách engine
├── src/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   └── game_state.py     # Logic game với undo/redo
│   ├── gui/
│   │   ├── __init__.py
│   │   ├── main_window.py         # Cửa sổ chính với multi-engine
│   │   ├── board_widget.py        # Widget bàn cờ với arrows & analysis info
│   │   ├── game_info_widget.py    # Widget thông tin game
│   │   ├── multi_engine_widget.py # Widget quản lý nhiều engine
│   │   ├── setup_widget.py        # Widget thiết lập position
│   │   └── dialogs/
│   │       ├── __init__.py
│   │       └── fen_dialog.py      # Dialog setup position
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── ucci_protocol.py       # UCCI protocol implementation
│   │   └── multi_engine_manager.py # Quản lý nhiều engine đồng thời
│   ├── ros/
│   │   └── ros_controller.py      # ROS2 integration controller
│   └── utils/
│       ├── __init__.py
│       ├── constants.py           # Hằng số game và Chinese notation
│       ├── shared_state.py        # Shared state management
│       └── svg_renderer.py        # SVG/PNG rendering utilities
├── xiangqi_gui/
│   ├── __init__.py
│   └── ros_service_node.py       # ROS2 service node
├── resource/
│   └── xiangqi_gui              # ROS2 resource marker
├── assets/
│   ├── images/
│   │   ├── pieces/              # Hình ảnh quân cờ PNG
│   │   │   ├── red/             # Quân đỏ (rK, rA, rB, rN, rR, rC, rP)
│   │   │   └── black/           # Quân đen (bK, bA, bB, bN, bR, bC, bP)
│   │   ├── board/
│   │   │   └── xiangqiboard_.png # Nền bàn cờ
│   │   └── ui/
│   │       └── icons/           # Icons cho UI
│   └── sounds/                  # Âm thanh (tùy chọn)
├── engines/                     # Engine executables
│   ├── README.md               # Hướng dẫn engines
│   ├── Fairy-Stockfish/
│   │   ├── fairy-stockfish     # Engine executable
│   │   └── bench.txt          # Benchmark results
│   └── Pikafish/
│       ├── pikafish           # Engine executable
│       └── pikafish.nnue      # Neural network weights
├── tests/                      # Unit tests
│   ├── test_analysis.py       # Test phân tích engine
│   ├── test_ros_service.py    # Test ROS integration
│   ├── test_shared_state.py   # Test shared state
│   └── test_signal.py         # Test signal handling
└── docs/
    └── ROS_INTEGRATION.md      # Tài liệu tích hợp ROS2
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