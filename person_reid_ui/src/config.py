"""
Configuration management for Person ReID UI
Loads from config.yaml and environment variables
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass
import streamlit as st


@dataclass
class APIConfig:
    """API configuration"""
    base_url: str = "http://localhost:8000"
    timeout: int = 30
    retry_attempts: int = 3
    retry_delay: int = 1


@dataclass
class UIConfig:
    """UI configuration"""
    title: str = "Person ReID System"
    page_icon: str = "👤"
    layout: str = "wide"
    port: int = 8501
    theme: str = "light"


@dataclass
class FeaturesConfig:
    """Feature flags"""
    auto_refresh: bool = True
    auto_refresh_interval: int = 5
    enable_charts: bool = True
    enable_export: bool = True
    debug_mode: bool = False


@dataclass
class DisplayConfig:
    """Display settings"""
    max_users_per_page: int = 100
    max_zones_per_page: int = 100
    max_messages: int = 500
    date_format: str = "%Y-%m-%d %H:%M:%S"


@dataclass
class ChartsConfig:
    """Chart settings"""
    color_scheme: str = "plotly"
    default_height: int = 500
    animation: bool = True


@dataclass
class AlertsConfig:
    """Alert settings"""
    show_notifications: bool = True
    sound_enabled: bool = False
    desktop_notifications: bool = False


class Config:
    """Main configuration class"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration
        
        Args:
            config_file: Path to config.yaml file
        """
        self.config_file = config_file or self._find_config_file()
        self._config_data = self._load_config()
        
        # Initialize sub-configs
        self.api = self._init_api_config()
        self.ui = self._init_ui_config()
        self.features = self._init_features_config()
        self.display = self._init_display_config()
        self.charts = self._init_charts_config()
        self.alerts = self._init_alerts_config()
    
    def _find_config_file(self) -> str:
        """Find config.yaml in current or parent directories"""
        current = Path(__file__).parent
        
        # Try current directory
        config_path = current / "config.yaml"
        if config_path.exists():
            return str(config_path)
        
        # Try parent directory
        config_path = current.parent / "config.yaml"
        if config_path.exists():
            return str(config_path)
        
        # Use default
        return str(current / "config.yaml")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            print(f"⚠️  Config file not found: {self.config_file}")
            print("   Using default configuration")
            return {}
        except Exception as e:
            print(f"⚠️  Error loading config: {e}")
            print("   Using default configuration")
            return {}
    
    def _get_env_or_config(self, env_var: str, config_path: list, default: Any) -> Any:
        """Get value from environment variable or config file"""
        # Try environment variable first
        env_value = os.getenv(env_var)
        if env_value is not None:
            # Convert to appropriate type
            if isinstance(default, bool):
                return env_value.lower() in ('true', '1', 'yes', 'on')
            elif isinstance(default, int):
                try:
                    return int(env_value)
                except ValueError:
                    pass
            return env_value
        
        # Try config file
        value = self._config_data
        for key in config_path:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return default
        
        return value if value is not None else default
    
    def _init_api_config(self) -> APIConfig:
        """Initialize API configuration"""
        return APIConfig(
            base_url=self._get_env_or_config(
                'PERSON_REID_API_URL',
                ['api', 'base_url'],
                "http://localhost:8000"
            ),
            timeout=self._get_env_or_config(
                'PERSON_REID_API_TIMEOUT',
                ['api', 'timeout'],
                30
            ),
            retry_attempts=self._get_env_or_config(
                'PERSON_REID_API_RETRY',
                ['api', 'retry_attempts'],
                3
            ),
            retry_delay=self._get_env_or_config(
                'PERSON_REID_API_RETRY_DELAY',
                ['api', 'retry_delay'],
                1
            )
        )
    
    def _init_ui_config(self) -> UIConfig:
        """Initialize UI configuration"""
        return UIConfig(
            title=self._get_env_or_config(
                'PERSON_REID_UI_TITLE',
                ['ui', 'title'],
                "Person ReID System"
            ),
            page_icon=self._get_env_or_config(
                'PERSON_REID_UI_ICON',
                ['ui', 'page_icon'],
                "👤"
            ),
            layout=self._get_env_or_config(
                'PERSON_REID_UI_LAYOUT',
                ['ui', 'layout'],
                "wide"
            ),
            port=self._get_env_or_config(
                'PERSON_REID_UI_PORT',
                ['ui', 'port'],
                8501
            ),
            theme=self._get_env_or_config(
                'PERSON_REID_UI_THEME',
                ['ui', 'theme'],
                "light"
            )
        )
    
    def _init_features_config(self) -> FeaturesConfig:
        """Initialize features configuration"""
        return FeaturesConfig(
            auto_refresh=self._get_env_or_config(
                'PERSON_REID_AUTO_REFRESH',
                ['features', 'auto_refresh'],
                True
            ),
            auto_refresh_interval=self._get_env_or_config(
                'PERSON_REID_REFRESH_INTERVAL',
                ['features', 'auto_refresh_interval'],
                5
            ),
            enable_charts=self._get_env_or_config(
                'PERSON_REID_ENABLE_CHARTS',
                ['features', 'enable_charts'],
                True
            ),
            enable_export=self._get_env_or_config(
                'PERSON_REID_ENABLE_EXPORT',
                ['features', 'enable_export'],
                True
            ),
            debug_mode=self._get_env_or_config(
                'PERSON_REID_DEBUG',
                ['features', 'debug_mode'],
                False
            )
        )
    
    def _init_display_config(self) -> DisplayConfig:
        """Initialize display configuration"""
        return DisplayConfig(
            max_users_per_page=self._get_env_or_config(
                'PERSON_REID_MAX_USERS',
                ['display', 'max_users_per_page'],
                100
            ),
            max_zones_per_page=self._get_env_or_config(
                'PERSON_REID_MAX_ZONES',
                ['display', 'max_zones_per_page'],
                100
            ),
            max_messages=self._get_env_or_config(
                'PERSON_REID_MAX_MESSAGES',
                ['display', 'max_messages'],
                500
            ),
            date_format=self._get_env_or_config(
                'PERSON_REID_DATE_FORMAT',
                ['display', 'date_format'],
                "%Y-%m-%d %H:%M:%S"
            )
        )
    
    def _init_charts_config(self) -> ChartsConfig:
        """Initialize charts configuration"""
        return ChartsConfig(
            color_scheme=self._get_env_or_config(
                'PERSON_REID_CHART_COLORS',
                ['charts', 'color_scheme'],
                "plotly"
            ),
            default_height=self._get_env_or_config(
                'PERSON_REID_CHART_HEIGHT',
                ['charts', 'default_height'],
                500
            ),
            animation=self._get_env_or_config(
                'PERSON_REID_CHART_ANIMATION',
                ['charts', 'animation'],
                True
            )
        )
    
    def _init_alerts_config(self) -> AlertsConfig:
        """Initialize alerts configuration"""
        return AlertsConfig(
            show_notifications=self._get_env_or_config(
                'PERSON_REID_SHOW_NOTIFICATIONS',
                ['alerts', 'show_notifications'],
                True
            ),
            sound_enabled=self._get_env_or_config(
                'PERSON_REID_SOUND',
                ['alerts', 'sound_enabled'],
                False
            ),
            desktop_notifications=self._get_env_or_config(
                'PERSON_REID_DESKTOP_NOTIFY',
                ['alerts', 'desktop_notifications'],
                False
            )
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'api': {
                'base_url': self.api.base_url,
                'timeout': self.api.timeout,
                'retry_attempts': self.api.retry_attempts,
                'retry_delay': self.api.retry_delay
            },
            'ui': {
                'title': self.ui.title,
                'page_icon': self.ui.page_icon,
                'layout': self.ui.layout,
                'port': self.ui.port,
                'theme': self.ui.theme
            },
            'features': {
                'auto_refresh': self.features.auto_refresh,
                'auto_refresh_interval': self.features.auto_refresh_interval,
                'enable_charts': self.features.enable_charts,
                'enable_export': self.features.enable_export,
                'debug_mode': self.features.debug_mode
            },
            'display': {
                'max_users_per_page': self.display.max_users_per_page,
                'max_zones_per_page': self.display.max_zones_per_page,
                'max_messages': self.display.max_messages,
                'date_format': self.display.date_format
            },
            'charts': {
                'color_scheme': self.charts.color_scheme,
                'default_height': self.charts.default_height,
                'animation': self.charts.animation
            },
            'alerts': {
                'show_notifications': self.alerts.show_notifications,
                'sound_enabled': self.alerts.sound_enabled,
                'desktop_notifications': self.alerts.desktop_notifications
            }
        }


# Singleton instance with caching
@st.cache_resource
def get_config() -> Config:
    """Get cached configuration instance"""
    return Config()


# Convenience function for direct import
def load_config(config_file: Optional[str] = None) -> Config:
    """Load configuration"""
    return Config(config_file)
