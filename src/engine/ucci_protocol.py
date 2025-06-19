# -*- coding: utf-8 -*-
"""
UCCI Protocol Implementation
Giao thức UCCI (Universal Chinese Chess Interface) cho cờ tướng
"""

import subprocess
import threading
import queue
import time
import traceback
from typing import Optional, List, Callable


class UCCIEngine:
    """Class để giao tiếp với engine cờ tướng qua giao thức UCCI"""

    def __init__(self, engine_path: str, protocol: str = "ucci"):
        """
        Khởi tạo engine

        Args:
            engine_path: Đường dẫn đến file executable của engine
            protocol: "ucci" cho cờ tướng, "uci" cho cờ vua
        """
        self.engine_path = engine_path
        self.protocol = protocol.lower()
        self.process = None
        self.input_queue = queue.Queue()
        self.output_queue = queue.Queue()
        self.is_running = False
        self.engine_thread = None

        # Callback functions
        self.on_bestmove: Optional[Callable[[str], None]] = None
        self.on_info: Optional[Callable[[str], None]] = None

    def start(self) -> bool:
        """
        Khởi động engine

        Returns:
            True nếu khởi động thành công, False nếu thất bại
        """
        try:
            self.process = subprocess.Popen(
                self.engine_path,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=0
            )

            self.is_running = True
            self.engine_thread = threading.Thread(
                target=self._engine_communication)
            self.engine_thread.daemon = True
            self.engine_thread.start()

            # Gửi lệnh khởi tạo theo protocol
            if self.protocol == "ucci":
                self.send_command("ucci")
            else:  # UCI
                self.send_command("uci")
            return True

        except Exception as e:
            print(f"Lỗi khởi động engine: {e}")
            return False

    def stop(self):
        """Dừng engine"""
        if self.is_running:
            self.send_command("quit")
            self.is_running = False

            if self.process:
                self.process.terminate()
                self.process.wait(timeout=5)
                self.process = None

    def send_command(self, command: str):
        """
        Gửi lệnh đến engine

        Args:
            command: Lệnh UCCI cần gửi
        """
        if self.process and self.is_running:
            try:
                self.process.stdin.write(command + "\n")
                self.process.stdin.flush()
                print(f"Gửi: {command}")
            except Exception as e:
                print(f"Lỗi gửi lệnh: {e}")

    def new_game(self):
        """Bắt đầu ván cờ mới"""
        if self.protocol == "ucci":
            self.send_command("uccinewgame")
        else:  # UCI
            self.send_command("ucinewgame")

    def set_position(self, fen: str, moves: List[str] = None):
        """
        Thiết lập vị trí bàn cờ

        Args:
            fen: Chuỗi FEN mô tả vị trí
            moves: Danh sách nước đi từ vị trí FEN
        """
        command = f"position fen {fen}"
        if moves:
            command += " moves " + " ".join(moves)
        self.send_command(command)

    def go(self, depth: int = None, time_ms: int = None):
        """
        Yêu cầu engine tìm nước đi tốt nhất

        Args:
            depth: Độ sâu tìm kiếm
            time_ms: Thời gian suy nghĩ (milliseconds)
        """
        command = "go"
        if depth:
            command += f" depth {depth}"
        if time_ms:
            command += f" movetime {time_ms}"

        self.send_command(command)

    def go_infinite(self):
        """
        Yêu cầu engine phân tích liên tục (infinite analysis)
        """
        self.send_command("go infinite")

    def stop_search(self):
        """Dừng tìm kiếm"""
        self.send_command("stop")

    def make_move(self, move: str):
        """
        Thông báo cho engine về nước đi vừa thực hiện

        Args:
            move: Nước đi dạng UCCI (e.g., "h2e2")
        """
        # Engine sẽ nhận thông tin này qua set_position với moves history
        pass

    def get_hint(self, depth: int = 8):
        """
        Yêu cầu engine gợi ý nước đi

        Args:
            depth: Độ sâu tìm kiếm để gợi ý
        """
        self.go(depth=depth)

    def _engine_communication(self):
        """Thread xử lý giao tiếp với engine"""
        while self.is_running and self.process:
            try:
                if self.process.poll() is not None:
                    # Engine đã thoát
                    print("Engine process đã kết thúc")
                    break

                line = self.process.stdout.readline()
                if not line:
                    continue

                line = line.strip()
                if line:
                    print(f"Nhận: {line}")
                    self._process_engine_output(line)

            except Exception as e:
                print(f"Lỗi giao tiếp engine: {e}")
                print(f"Traceback: {traceback.format_exc()}")
                break

        print("Engine communication thread kết thúc")
        self.is_running = False

    def _process_engine_output(self, line: str):
        """
        Xử lý output từ engine

        Args:
            line: Dòng output từ engine
        """
        parts = line.split()
        if not parts:
            return

        command = parts[0]

        if command == "ucciok" or command == "uciok":
            print("Engine đã sẵn sàng")

        elif command == "readyok":
            print("Engine đã ready")

        elif command == "bestmove":
            if len(parts) >= 2:
                # Gửi toàn bộ dòng bestmove để parse cả bestmove và ponder
                if self.on_bestmove:
                    try:
                        # Gửi toàn bộ dòng thay vì chỉ move
                        self.on_bestmove(line)
                    except Exception as e:
                        print(f"Lỗi trong callback on_bestmove: {e}")
                        print(f"Traceback: {traceback.format_exc()}")

        elif command == "info":
            if self.on_info:
                try:
                    self.on_info(line)
                except Exception as e:
                    print(f"Lỗi trong callback on_info: {e}")
                    print(f"Traceback: {traceback.format_exc()}")

        elif command == "id":
            print(f"Engine info: {' '.join(parts[1:])}")


class UCCIEngineManager:
    """Manager để quản lý nhiều engine"""

    def __init__(self):
        self.engines = {}
        self.current_engine = None
        self.protocol = "ucci"  # Mặc định UCCI cho cờ tướng

    def set_protocol(self, protocol: str):
        """
        Đặt protocol sử dụng

        Args:
            protocol: "ucci" cho cờ tướng, "uci" cho cờ vua
        """
        self.protocol = protocol.lower()
        print(f"Protocol đã được đặt thành: {self.protocol.upper()}")

    def get_protocol(self) -> str:
        """Lấy protocol hiện tại"""
        return self.protocol

    def add_engine(self, name: str, path: str) -> bool:
        """
        Thêm engine mới

        Args:
            name: Tên engine
            path: Đường dẫn đến engine

        Returns:
            True nếu thành công
        """
        engine = UCCIEngine(path, self.protocol)
        if engine.start():
            self.engines[name] = engine
            return True
        return False

    def set_current_engine(self, name: str) -> bool:
        """
        Chọn engine hiện tại

        Args:
            name: Tên engine

        Returns:
            True nếu thành công
        """
        if name in self.engines:
            self.current_engine = self.engines[name]
            return True
        return False

    def get_current_engine(self) -> Optional[UCCIEngine]:
        """Lấy engine hiện tại"""
        return self.current_engine

    def stop_all_engines(self):
        """Dừng tất cả engine"""
        for engine in self.engines.values():
            engine.stop()
        self.engines.clear()
        self.current_engine = None
