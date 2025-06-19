"""
Shared State Manager để chia sẻ thông tin giữa GUI và ROS service
"""
import threading
import time
from typing import Dict, Optional, Any
import json
import os


class SharedGameState:
    """
    Shared state singleton để chia sẻ thông tin game giữa các components
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return

        self._initialized = True
        self._data_lock = threading.RLock()

        # Game state data
        self._current_fen = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1"
        self._current_player = "red"
        self._move_history = []
        self._game_status = "playing"  # playing, checkmate, stalemate, draw

        # Engine results from main GUI
        self._engine_results = {}
        self._best_move = None
        self._last_analysis_time = 0

        # Metadata
        self._last_update_time = time.time()

        print("🔗 SharedGameState initialized")

    def update_position(self, fen: str, current_player: str = None, moves: list = None):
        """
        Cập nhật position từ main GUI

        Args:
            fen: FEN string hiện tại
            current_player: 'red' hoặc 'black'
            moves: List of moves history
        """
        with self._data_lock:
            self._current_fen = fen
            if current_player:
                self._current_player = current_player
            if moves is not None:
                self._move_history = moves.copy()
            self._last_update_time = time.time()

        print(f"🔄 SharedState: Position updated - {fen}")

    def update_engine_results(self, engine_results: Dict[str, Any]):
        """
        Cập nhật kết quả engine từ main GUI

        Args:
            engine_results: Dict chứa results từ các engines
        """
        with self._data_lock:
            self._engine_results = engine_results.copy()

            # Lấy best move từ engine đầu tiên có result
            self._best_move = None
            for engine_name, result in engine_results.items():
                bestmove = result.get('bestmove')
                if bestmove and bestmove != 'None':
                    self._best_move = bestmove
                    self._last_analysis_time = time.time()
                    break

        print(
            f"🧠 SharedState: Engine results updated - {len(engine_results)} engines")

    def get_current_fen(self) -> str:
        """Lấy FEN hiện tại"""
        with self._data_lock:
            return self._current_fen

    def get_current_player(self) -> str:
        """Lấy current player"""
        with self._data_lock:
            return self._current_player

    def get_move_history(self) -> list:
        """Lấy move history"""
        with self._data_lock:
            return self._move_history.copy()

    def get_best_move(self) -> Optional[str]:
        """Lấy best move từ engine"""
        with self._data_lock:
            return self._best_move

    def get_engine_results(self) -> Dict[str, Any]:
        """Lấy tất cả engine results"""
        with self._data_lock:
            return self._engine_results.copy()

    def get_game_info(self) -> Dict[str, Any]:
        """
        Lấy thông tin tổng hợp về game

        Returns:
            Dict chứa tất cả thông tin game
        """
        with self._data_lock:
            return {
                'fen': self._current_fen,
                'current_player': self._current_player,
                'move_count': len(self._move_history),
                'move_history': self._move_history.copy(),
                'game_status': self._game_status,
                'best_move': self._best_move,
                'last_update_time': self._last_update_time,
                'last_analysis_time': self._last_analysis_time,
                'engine_results': self._engine_results.copy()
            }

    def set_game_status(self, status: str):
        """Set game status"""
        with self._data_lock:
            self._game_status = status
            self._last_update_time = time.time()

    def is_data_fresh(self, max_age_seconds: float = 30.0) -> bool:
        """
        Kiểm tra data có còn fresh không

        Args:
            max_age_seconds: Max age in seconds

        Returns:
            bool: True nếu data còn fresh
        """
        with self._data_lock:
            return (time.time() - self._last_update_time) <= max_age_seconds


class SharedStateFile:
    """
    File-based shared state để communicate giữa processes
    """

    def __init__(self, file_path: str = None):
        if file_path is None:
            # Default path trong workspace
            self.file_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                'shared_game_state.json'
            )
        else:
            self.file_path = file_path

        self._lock = threading.Lock()

        # Ensure directory exists
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)

        print(f"📁 SharedStateFile: {self.file_path}")

    def write_state(self, state_data: Dict[str, Any]):
        """
        Write state to file

        Args:
            state_data: State data dict
        """
        try:
            with self._lock:
                # Add timestamp
                state_data['timestamp'] = time.time()

                # Write to temp file first, then rename (atomic operation)
                temp_path = self.file_path + '.tmp'
                with open(temp_path, 'w', encoding='utf-8') as f:
                    json.dump(state_data, f, indent=2, ensure_ascii=False)

                # Atomic rename
                os.rename(temp_path, self.file_path)

        except Exception as e:
            print(f"❌ Error writing shared state: {e}")

    def read_state(self) -> Optional[Dict[str, Any]]:
        """
        Read state from file

        Returns:
            Dict hoặc None nếu không đọc được
        """
        try:
            with self._lock:
                if not os.path.exists(self.file_path):
                    return None

                with open(self.file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)

        except Exception as e:
            print(f"❌ Error reading shared state: {e}")
            return None

    def is_file_fresh(self, max_age_seconds: float = 30.0) -> bool:
        """
        Kiểm tra file có còn fresh không

        Args:
            max_age_seconds: Max age in seconds

        Returns:
            bool: True nếu file còn fresh
        """
        try:
            if not os.path.exists(self.file_path):
                return False

            file_time = os.path.getmtime(self.file_path)
            return (time.time() - file_time) <= max_age_seconds

        except:
            return False


# Global instances
shared_game_state = SharedGameState()
shared_state_file = SharedStateFile()


def update_from_gui(fen: str, current_player: str, moves: list, engine_results: Dict[str, Any]):
    """
    Helper function để update shared state từ main GUI

    Args:
        fen: Current FEN
        current_player: Current player
        moves: Move history
        engine_results: Engine analysis results
    """
    # Update in-memory state
    shared_game_state.update_position(fen, current_player, moves)
    shared_game_state.update_engine_results(engine_results)

    # Update file state
    state_data = shared_game_state.get_game_info()
    shared_state_file.write_state(state_data)

    print(f"🔄 Shared state updated from GUI")


def get_for_ros() -> Dict[str, Any]:
    """
    Helper function để lấy data cho ROS service

    Returns:
        Dict chứa game info
    """
    # Try in-memory first
    game_info = shared_game_state.get_game_info()

    # If data is stale, try file
    if not shared_game_state.is_data_fresh():
        file_data = shared_state_file.read_state()
        if file_data and shared_state_file.is_file_fresh():
            print("📁 Using file-based shared state")
            return file_data

    return game_info
