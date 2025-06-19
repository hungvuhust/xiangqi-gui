"""
Multi-Engine Manager với threading tách biệt cho mỗi engine
"""
import os
import threading
import time
import queue
from typing import Dict, List, Optional, Callable
from PyQt5.QtCore import QObject, pyqtSignal

from .ucci_protocol import UCCIEngine


class EngineWorker(threading.Thread):
    """Worker thread riêng cho mỗi engine"""

    def __init__(self, engine_name: str, engine_path: str, result_callback: Callable):
        super().__init__(daemon=True)
        self.engine_name = engine_name
        self.engine_path = engine_path
        self.result_callback = result_callback

        # Thread control
        self.running = True
        self.command_queue = queue.Queue()

        # Engine instance
        self.engine = None

        # Results storage
        self.last_result = {
            'bestmove': None,
            'ponder': None,
            'evaluation': 0.0,
            'depth': 0,
            'nodes': 0,
            'pv': [],
            'protocol': 'detecting...',
            'status': 'initializing',
            # Flag để ignore engine info cũ (giống single engine)
            'ignore_old_info': False
        }

        # Lock for thread-safe access
        self.result_lock = threading.Lock()

        print(f"📱 Created worker for engine: {engine_name}")

    def run(self):
        """Main thread loop"""
        try:
            # Initialize engine
            self.engine = UCCIEngine(self.engine_path, "auto")

            # Setup callbacks
            self.engine.on_bestmove = self._handle_bestmove
            self.engine.on_info = self._handle_info

            # Start engine
            if self.engine.start():
                with self.result_lock:
                    self.last_result['status'] = 'ready'
                print(f"✅ Engine {self.engine_name} started successfully")

                # Send startup status
                self._send_result_update()

                # Wait for protocol detection
                print(f"🔍 {self.engine_name}: Detecting protocol...")
                time.sleep(2)
                detected_protocol = self.engine.get_detected_protocol()

                with self.result_lock:
                    self.last_result['protocol'] = detected_protocol

                print(
                    f"📡 {self.engine_name}: Protocol detected = {detected_protocol}")

                # Send protocol update
                self._send_result_update()
            else:
                with self.result_lock:
                    self.last_result['status'] = 'failed'
                print(f"❌ Failed to start engine: {self.engine_name}")
                self._send_result_update()
                return

            # Main command processing loop
            while self.running:
                try:
                    # Get command with timeout
                    command = self.command_queue.get(timeout=0.5)
                    self._process_command(command)
                except queue.Empty:
                    continue
                except Exception as e:
                    print(
                        f"❌ Error processing command for {self.engine_name}: {e}")

        except Exception as e:
            print(f"❌ Fatal error in engine worker {self.engine_name}: {e}")
        finally:
            self._cleanup()

    def _process_command(self, command: dict):
        """Process command từ main thread"""
        cmd_type = command.get('type')

        try:
            if cmd_type == 'set_position':
                fen = command.get('fen')
                moves = command.get('moves', [])
                if self.engine:
                    # Kiểm tra nếu đang analyzing
                    was_analyzing = self.last_result.get(
                        'status') == 'analyzing'

                    # Nếu đang analyzing, dừng trước khi set position mới
                    if was_analyzing:
                        print(
                            f"⏹️ {self.engine_name}: Stopping analysis before position change")
                        self.engine.stop_search()
                        # Set flag để ignore engine info cũ (giống single engine)
                        with self.result_lock:
                            self.last_result['ignore_old_info'] = True

                    # Set position mới
                    self.engine.set_position(fen, moves)
                    print(f"📍 {self.engine_name}: Set position")

                    # Restart analysis với delay nếu trước đó đang analyzing (giống single engine)
                    if was_analyzing:
                        print(
                            f"🔄 {self.engine_name}: Scheduling analysis restart with delay")
                        # Sử dụng threading.Timer để delay 100ms giống single engine
                        import threading

                        def delayed_restart():
                            try:
                                # Reset flag để nhận engine info mới
                                with self.result_lock:
                                    self.last_result['ignore_old_info'] = False
                                # Set position lại (giống single engine)
                                self.engine.set_position(fen, moves)
                                # Bắt đầu analysis mới
                                self.engine.go_infinite()
                                print(
                                    f"🔍 {self.engine_name}: Started new analysis after delay")
                            except Exception as e:
                                print(
                                    f"❌ Error in delayed restart for {self.engine_name}: {e}")

                        restart_timer = threading.Timer(
                            0.1, delayed_restart)  # 100ms delay
                        restart_timer.start()

            elif cmd_type == 'get_hint':
                depth = command.get('depth', 8)
                if self.engine:
                    with self.result_lock:
                        self.last_result['status'] = 'thinking'
                    self.engine.get_hint(depth)
                    print(
                        f"🤖 {self.engine_name}: Requested hint (depth {depth})")

            elif cmd_type == 'start_analysis':
                if self.engine:
                    with self.result_lock:
                        self.last_result['status'] = 'analyzing'
                    self.engine.go_infinite()
                    print(f"🔍 {self.engine_name}: Started analysis")

            elif cmd_type == 'stop_analysis':
                if self.engine:
                    self.engine.stop_search()
                    with self.result_lock:
                        self.last_result['status'] = 'ready'
                    print(f"⏹️ {self.engine_name}: Stopped analysis")

            elif cmd_type == 'stop':
                self.running = False

        except Exception as e:
            print(
                f"❌ Error executing command {cmd_type} for {self.engine_name}: {e}")

    def _handle_bestmove(self, bestmove_line: str):
        """Handle bestmove từ engine"""
        try:
            # Kiểm tra nếu đang ignore old info (giống single engine)
            with self.result_lock:
                if self.last_result.get('ignore_old_info', False):
                    return

            # Parse bestmove line: "bestmove e2e4 ponder d7d5"
            parts = bestmove_line.strip().split()
            bestmove = None
            ponder = None

            # Tìm cả bestmove và ponder trong cùng một vòng lặp
            for i, part in enumerate(parts):
                if part == "bestmove" and i + 1 < len(parts):
                    bestmove = parts[i + 1]
                elif part == "ponder" and i + 1 < len(parts):
                    ponder = parts[i + 1]

            if bestmove and bestmove != "none":
                with self.result_lock:
                    self.last_result['bestmove'] = bestmove
                    self.last_result['ponder'] = ponder
                    self.last_result['status'] = 'ready'

                print(
                    f"🎯 {self.engine_name}: Bestmove = {bestmove}, Ponder = {ponder}")
                self._send_result_update()

        except Exception as e:
            print(f"❌ Error handling bestmove for {self.engine_name}: {e}")

    def _handle_info(self, info_line: str):
        """Handle info từ engine"""
        try:
            # Kiểm tra nếu đang ignore old info (giống single engine)
            with self.result_lock:
                if self.last_result.get('ignore_old_info', False):
                    return

            # Parse info line
            parts = info_line.split()
            if not parts or parts[0] != "info":
                return

            updated = False
            with self.result_lock:
                i = 1
                while i < len(parts):
                    key = parts[i]

                    if key == "depth" and i + 1 < len(parts):
                        self.last_result['depth'] = int(parts[i + 1])
                        updated = True
                        i += 2

                    elif key == "score" and i + 2 < len(parts):
                        score_type = parts[i + 1]
                        score_value = parts[i + 2]

                        if score_type == "cp":
                            # Centipawn to pawn
                            self.last_result['evaluation'] = int(
                                score_value) / 100.0
                        elif score_type == "mate":
                            mate_moves = int(score_value)
                            if mate_moves > 0:
                                self.last_result['evaluation'] = float('inf')
                            else:
                                self.last_result['evaluation'] = float('-inf')
                        updated = True
                        i += 3

                    elif key == "nodes" and i + 1 < len(parts):
                        self.last_result['nodes'] = int(parts[i + 1])
                        updated = True
                        i += 2

                    elif key == "pv":
                        # Principal variation
                        pv_moves = parts[i + 1:]
                        self.last_result['pv'] = pv_moves

                        # Trong chế độ analysis, sử dụng PV để tạo bestmove và ponder
                        if self.last_result.get('status') == 'analyzing' and pv_moves:
                            if len(pv_moves) >= 1:
                                self.last_result['bestmove'] = pv_moves[0]
                                print(
                                    f"🔍 {self.engine_name}: Analysis bestmove from PV = {pv_moves[0]}")
                            if len(pv_moves) >= 2:
                                self.last_result['ponder'] = pv_moves[1]
                                print(
                                    f"🔍 {self.engine_name}: Analysis ponder from PV = {pv_moves[1]}")

                        updated = True
                        break

                    else:
                        i += 1

            if updated:
                self._send_result_update()

        except Exception as e:
            print(f"❌ Error handling info for {self.engine_name}: {e}")

    def _send_result_update(self):
        """Send result update to main thread"""
        if self.result_callback:
            with self.result_lock:
                result_copy = self.last_result.copy()
            self.result_callback(self.engine_name, result_copy)

    def send_command(self, command: dict):
        """Send command to engine thread"""
        try:
            self.command_queue.put(command, timeout=1.0)
        except queue.Full:
            print(f"⚠️ Command queue full for {self.engine_name}")

    def get_result(self) -> dict:
        """Get current result (thread-safe)"""
        with self.result_lock:
            return self.last_result.copy()

    def stop(self):
        """Stop engine worker"""
        self.running = False
        self.send_command({'type': 'stop'})

    def _cleanup(self):
        """Cleanup resources"""
        if self.engine:
            try:
                self.engine.stop()
            except:
                pass
        print(f"🧹 Cleaned up worker for {self.engine_name}")


class MultiEngineManager(QObject):
    """Manager để quản lý nhiều engine với threading riêng biệt"""

    # Signals for UI updates
    engine_result_updated = pyqtSignal(str, dict)  # engine_name, result

    def __init__(self):
        super().__init__()
        self.workers: Dict[str, EngineWorker] = {}
        self.worker_lock = threading.Lock()

        print("🚀 MultiEngineManager initialized")

    def add_engine(self, name: str, path: str) -> bool:
        """
        Thêm engine mới với worker thread riêng

        Args:
            name: Tên engine
            path: Đường dẫn engine

        Returns:
            bool: True nếu thành công
        """
        if name in self.workers:
            print(f"⚠️ Engine {name} already exists")
            return False

        if not os.path.exists(path):
            print(f"❌ Engine path does not exist: {path}")
            return False

        try:
            # Create worker với callback
            worker = EngineWorker(name, path, self._on_engine_result)

            with self.worker_lock:
                self.workers[name] = worker

            # Start worker thread
            worker.start()

            print(f"✅ Added engine: {name}")
            return True

        except Exception as e:
            print(f"❌ Failed to add engine {name}: {e}")
            return False

    def remove_engine(self, name: str):
        """Xóa engine"""
        with self.worker_lock:
            if name in self.workers:
                worker = self.workers[name]
                worker.stop()

                # Wait for thread to finish
                if worker.is_alive():
                    worker.join(timeout=2.0)

                del self.workers[name]
                print(f"✅ Removed engine: {name}")

    def get_active_engines(self) -> List[str]:
        """Lấy danh sách engine đang hoạt động"""
        with self.worker_lock:
            return list(self.workers.keys())

    def set_position_all(self, fen: str, moves: List[str] = None):
        """Đặt position cho tất cả engines"""
        command = {
            'type': 'set_position',
            'fen': fen,
            'moves': moves or []
        }

        with self.worker_lock:
            for worker in self.workers.values():
                worker.send_command(command)

        print(f"📍 Set position for {len(self.workers)} engines")

    def get_hint_all(self, depth: int = 8):
        """Yêu cầu hint từ tất cả engines"""
        command = {
            'type': 'get_hint',
            'depth': depth
        }

        with self.worker_lock:
            for worker in self.workers.values():
                worker.send_command(command)

        print(
            f"🤖 Requested hints from {len(self.workers)} engines (depth {depth})")

    def start_analysis_all(self):
        """Bắt đầu analysis cho tất cả engines"""
        command = {'type': 'start_analysis'}

        with self.worker_lock:
            for worker in self.workers.values():
                worker.send_command(command)

        print(f"🔍 Started analysis for {len(self.workers)} engines")

    def stop_analysis_all(self):
        """Dừng analysis cho tất cả engines"""
        command = {'type': 'stop_analysis'}

        with self.worker_lock:
            for worker in self.workers.values():
                worker.send_command(command)

        print(f"⏹️ Stopped analysis for {len(self.workers)} engines")

    def get_results(self) -> Dict[str, dict]:
        """Lấy kết quả từ tất cả engines"""
        results = {}

        with self.worker_lock:
            for name, worker in self.workers.items():
                results[name] = worker.get_result()

        return results

    def stop_all(self):
        """Dừng tất cả engines"""
        with self.worker_lock:
            workers_to_stop = list(self.workers.values())
            engine_names = list(self.workers.keys())

        # Stop all workers
        for worker in workers_to_stop:
            worker.stop()

        # Wait for all threads to finish
        for worker in workers_to_stop:
            if worker.is_alive():
                worker.join(timeout=2.0)

        with self.worker_lock:
            self.workers.clear()

        print(f"🛑 Stopped all engines: {engine_names}")

    def _on_engine_result(self, engine_name: str, result: dict):
        """Callback khi có kết quả từ engine (thread-safe)"""
        # Emit signal để update UI
        self.engine_result_updated.emit(engine_name, result)

        # Debug log
        if result.get('bestmove'):
            print(f"📊 {engine_name}: {result.get('bestmove')} "
                  f"(eval: {result.get('evaluation', 0):.2f}, "
                  f"depth: {result.get('depth', 0)})")
