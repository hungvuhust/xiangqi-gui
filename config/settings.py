# -*- coding: utf-8 -*-
"""
Settings cho Xiangqi GUI
Cấu hình các thông số của ứng dụng
"""

import json
import os
from configparser import ConfigParser


class Settings:
    """Class quản lý cấu hình ứng dụng"""

    def __init__(self):
        self.config_file = "config/settings.ini"
        self.engines_config_file = "config/engines.json"
        self.config = ConfigParser()
        self.load_settings()

    def load_settings(self):
        """Load cấu hình từ file"""
        # Tạo cấu hình mặc định
        self.create_default_config()

        # Load từ file nếu có
        if os.path.exists(self.config_file):
            self.config.read(self.config_file)

    def create_default_config(self):
        """Tạo cấu hình mặc định"""
        # UI Settings
        self.config['UI'] = {
            'board_size': '600',
            'piece_size': '50',
            'board_margin': '30',
            'theme': 'default',
            'language': 'vi'
        }

        # Game Settings
        self.config['GAME'] = {
            'auto_save': 'true',
            'sound_enabled': 'true',
            'animation_enabled': 'true',
            'show_coordinates': 'true',
            'highlight_moves': 'true'
        }

        # Engine Settings
        self.config['ENGINE'] = {
            'default_engine': 'Fairy-Stockfish',
            'default_depth': '10',
            'default_time': '5000',
            'auto_analysis': 'false'
        }

    def save_settings(self):
        """Lưu cấu hình ra file"""
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        with open(self.config_file, 'w') as f:
            self.config.write(f)

    def get(self, section, key, fallback=None):
        """Lấy giá trị cấu hình"""
        return self.config.get(section, key, fallback=fallback)

    def getint(self, section, key, fallback=0):
        """Lấy giá trị integer"""
        return self.config.getint(section, key, fallback=fallback)

    def getboolean(self, section, key, fallback=False):
        """Lấy giá trị boolean"""
        return self.config.getboolean(section, key, fallback=fallback)

    def set(self, section, key, value):
        """Thiết lập giá trị cấu hình"""
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, key, str(value))

    def load_engines_config(self):
        """Load cấu hình engines từ JSON"""
        if os.path.exists(self.engines_config_file):
            with open(self.engines_config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"engines": [], "default_engine": "", "engine_settings": {}}

    def save_engines_config(self, engines_data):
        """Lưu cấu hình engines"""
        os.makedirs(os.path.dirname(self.engines_config_file), exist_ok=True)
        with open(self.engines_config_file, 'w', encoding='utf-8') as f:
            json.dump(engines_data, f, indent=2, ensure_ascii=False)


# Global settings instance
settings = Settings()
