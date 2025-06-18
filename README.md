# Xiangqi GUI - Game Cờ Tướng

Game cờ tướng sử dụng PyQt5 với engine UCI/UCCI bên ngoài.

## Cấu trúc thư mục

```
xiangqi-gui/
├── main.py                 # Entry point của ứng dụng
├── requirements.txt        # Dependencies
├── config/
│   ├── __init__.py
│   ├── settings.py        # Cấu hình game (màu sắc, kích thước, đường dẫn engine)
│   └── engines.json       # Danh sách các engine có sẵn
├── src/
│   ├── __init__.py
│   ├── gui/
│   │   ├── __init__.py
│   │   ├── main_window.py      # Cửa sổ chính
│   │   ├── board_widget.py     # Widget hiển thị bàn cờ
│   │   ├── piece_widget.py     # Widget cho từng quân cờ
│   │   ├── game_info_widget.py # Widget thông tin game (thời gian, nước đi)
│   │   └── dialogs/
│   │       ├── __init__.py
│   │       ├── engine_settings.py  # Dialog cấu hình engine
│   │       ├── game_settings.py    # Dialog cài đặt game
│   │       └── about_dialog.py     # Dialog về ứng dụng
│   ├── core/
│   │   ├── __init__.py
│   │   ├── board.py           # Logic bàn cờ và trạng thái game
│   │   ├── pieces.py          # Định nghĩa các quân cờ
│   │   ├── moves.py           # Logic nước đi và validation
│   │   ├── game_state.py      # Quản lý trạng thái game
│   │   └── notation.py        # Xử lý ký hiệu cờ (FEN, PGN)
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── engine_manager.py  # Quản lý engine process
│   │   ├── ucci_protocol.py   # Giao thức UCCI cho cờ tướng
│   │   ├── uci_protocol.py    # Giao thức UCI (nếu engine hỗ trợ)
│   │   └── engine_wrapper.py  # Wrapper cho subprocess
│   └── utils/
│       ├── __init__.py
│       ├── constants.py       # Hằng số (kích thước bàn cờ, vị trí quân)
│       ├── helpers.py         # Các hàm tiện ích
│       └── logger.py          # Logging system
├── assets/
│   ├── images/
│   │   ├── pieces/           # Hình ảnh quân cờ
│   │   │   ├── red/          # Quân đỏ
│   │   │   │   ├── king.png, advisor.png, elephant.png,
│   │   │   │   ├── horse.png, chariot.png, cannon.png, soldier.png
│   │   │   └── black/        # Quân đen
│   │   │       └── (tương tự quân đỏ)
│   │   ├── board/
│   │   │   ├── board_bg.png  # Nền bàn cờ
│   │   │   ├── grid.png      # Lưới bàn cờ
│   │   │   └── palace.png    # Cung thành
│   │   └── ui/
│   │       ├── icons/        # Icons cho menu, toolbar
│   │       └── buttons/      # Hình ảnh nút bấm
│   ├── sounds/              # Âm thanh (tùy chọn)
│   │   ├── move.wav
│   │   ├── capture.wav
│   │   └── check.wav
│   └── fonts/               # Fonts đặc biệt (nếu cần)
├── engines/                 # Thư mục chứa engine executables
│   ├── README.md           # Hướng dẫn tải và cài đặt engine
│   └── (các engine executable sẽ được đặt ở đây)
├── tests/                   # Unit tests
│   ├── __init__.py
│   ├── test_board.py
│   ├── test_moves.py
│   ├── test_engine.py
│   └── test_gui.py
└── docs/                    # Documentation
    ├── INSTALLATION.md
    ├── USER_GUIDE.md
    └── DEVELOPER_GUIDE.md
```

## Tính năng chính

### GUI Components:
- **Bàn cờ tương tác**: Click để di chuyển, highlight nước đi có thể
- **Hiển thị thông tin**: Thời gian, nước đi, điểm số từ engine
- **Menu & Toolbar**: New game, load/save, settings, engine configuration
- **Status bar**: Hiển thị trạng thái kết nối engine

### Engine Integration:
- **Multi-engine support**: Hỗ trợ nhiều engine khác nhau
- **UCCI Protocol**: Giao tiếp với engine cờ tướng chuẩn
- **Subprocess management**: Quản lý tiến trình engine an toàn
- **Engine analysis**: Hiển thị đánh giá và biến thể từ engine

### Game Features:
- **Undo/Redo**: Quay lại nước đi
- **Game saving**: Lưu/load game với format PGN
- **Position setup**: Thiết lập vị trí tùy ý
- **Time control**: Quản lý thời gian cho từng bên

## Công nghệ sử dụng

- **PyQt5**: GUI framework
- **Subprocess**: Giao tiếp với engine
- **JSON**: Cấu hình và lưu trữ
- **Threading**: Xử lý engine không đồng bộ

## Engine được đề xuất

- **Pikafish**: Engine cờ tướng mạnh, hỗ trợ UCCI
- **ElephantEye**: Engine mã nguồn mở
- **Cyclone**: Engine cờ tướng nhanh

## Cài đặt

```bash
pip install -r requirements.txt
python main.py
``` 