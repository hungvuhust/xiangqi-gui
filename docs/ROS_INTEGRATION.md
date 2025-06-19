# ROS2 Integration cho Xiangqi GUI

## 📋 Tổng quan

Xiangqi GUI hiện đã tích hợp ROS2 service để expose FEN (Forsyth-Edwards Notation) của bàn cờ hiện tại. Điều này cho phép các ứng dụng ROS2 khác có thể lấy trạng thái bàn cờ theo thời gian thực.

## 🛠️ Cài đặt

### Yêu cầu hệ thống:
- ROS2 (Humble/Iron/Rolling)
- Python 3.8+
- PyQt5

### Cài đặt dependencies:
```bash
# Cài đặt ROS2 dependencies
sudo apt install ros-$ROS_DISTRO-rclpy ros-$ROS_DISTRO-std-msgs ros-$ROS_DISTRO-std-srvs

# Source ROS2
source /opt/ros/$ROS_DISTRO/setup.bash

# Cài đặt Python dependencies  
pip install -r requirements.txt
```

## 🚀 Sử dụng

### 1. Khởi động GUI với ROS service:

```bash
# Terminal 1: Chạy GUI
python main.py

# Trong GUI: ROS > Start ROS Service
```

### 2. Gọi service từ command line:

```bash
# Terminal 2: Gọi service để lấy FEN
ros2 service call /get_xiangqi_fen std_srvs/srv/Trigger
```

### 3. Sử dụng test client:

```bash
# Terminal 2: Chạy test client
python test_ros_service.py
```

## 📡 ROS Service API

### Service Name: `/get_xiangqi_fen`

**Type**: `std_srvs/srv/Trigger`

**Request**: Empty (Trigger request)

**Response**:
```yaml
bool success        # True nếu thành công
string message      # FEN string hoặc error message
```

### Ví dụ Response:
```yaml
success: True
message: "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1"
```

## 🔄 Đồng bộ hóa

- **GUI → ROS**: Khi có nước đi mới trong GUI, position tự động được sync với ROS service
- **ROS → GUI**: Có thể cập nhật position từ ROS (future feature)

## 💡 Use Cases

1. **AI Training**: Lấy position để train AI models
2. **Analysis Tools**: Phân tích position bằng external tools
3. **Tournament Systems**: Tích hợp với hệ thống giải đấu
4. **Data Collection**: Thu thập dữ liệu game để nghiên cứu
5. **Remote Monitoring**: Theo dõi game từ xa

## 🐛 Troubleshooting

### ROS2 không khởi động được:
```bash
# Kiểm tra ROS2 environment
echo $ROS_DISTRO

# Source lại ROS2
source /opt/ros/$ROS_DISTRO/setup.bash
```

### Service không available:
```bash
# Kiểm tra service list
ros2 service list | grep xiangqi

# Kiểm tra service type
ros2 service type /get_xiangqi_fen
```

### Permission errors:
```bash
# Thêm user vào dialout group
sudo usermod -a -G dialout $USER

# Logout và login lại
```

## 📚 API Documentation

### FEN Format
FEN string có format chuẩn theo FIDE:
```
<board> <active_color> <castling> <en_passant> <halfmove> <fullmove>
```

**Ví dụ**:
- Starting position: `rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1`
- Active color: `w` (white/red) hoặc `b` (black)

### Integration với Python:
```python
import rclpy
from rclpy.node import Node
from std_srvs.srv import Trigger

class XiangqiClient(Node):
    def __init__(self):
        super().__init__('xiangqi_client')
        self.cli = self.create_client(Trigger, 'get_xiangqi_fen')
        
    def get_fen(self):
        req = Trigger.Request()
        future = self.cli.call_async(req)
        rclpy.spin_until_future_complete(self, future)
        return future.result()
```

## 🔮 Future Features

- [ ] Bidirectional sync (ROS → GUI position updates)
- [ ] Custom message types với detailed position info
- [ ] Move history service
- [ ] Game analysis service
- [ ] Tournament management integration 