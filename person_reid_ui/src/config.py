"""
Configuration management for Person ReID UI
Loads from root .env file and environment variables
"""

import os
from pathlib import Path
from typing import Any, Dict
from dataclasses import dataclass
import streamlit as st

# Load .env from root project directory
try:
    from dotenv import load_dotenv
    # Find .env in root project (parent of person_reid_ui)
    root_dir = Path(__file__).parent.parent.parent
    env_path = root_dir / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Loaded .env from: {env_path}")
    else:
        print(f"⚠️  .env not found at: {env_path}")
except ImportError:
    print("⚠️  python-dotenv not installed, using system environment only")
except Exception as e:
    print(f"⚠️  Error loading .env: {e}")


@dataclass
class APIConfig:
    """API configuration"""
    base_url: str = ""
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
    """Main configuration class - reads from .env file"""

    def __init__(self):
        """Initialize configuration from environment variables"""
        # Initialize sub-configs
        self.api = self._init_api_config()
        self.ui = self._init_ui_config()
        self.features = self._init_features_config()
        self.display = self._init_display_config()
        self.charts = self._init_charts_config()
        self.alerts = self._init_alerts_config()

    def _get_env(self, env_var: str, default: Any) -> Any:
        """Get value from environment variable with type conversion"""
        env_value = os.getenv(env_var)
        if env_value is not None:
            # Convert to appropriate type
            if isinstance(default, bool):
                return env_value.lower() in ('true', '1', 'yes', 'on')
            elif isinstance(default, int):
                try:
                    return int(env_value)
                except ValueError:
                    return default
            return env_value
        return default
    
    def _init_api_config(self) -> APIConfig:
        """Initialize API configuration"""
        return APIConfig(
            base_url=self._get_env('API_HOST', "http://localhost") + ":" +
                     str(self._get_env('API_PORT', 8000)),
            timeout=self._get_env('API_TIMEOUT', 30),
            retry_attempts=self._get_env('API_RETRY_ATTEMPTS', 3),
            retry_delay=self._get_env('API_RETRY_DELAY', 1)
        )
    
    def _init_ui_config(self) -> UIConfig:
        """Initialize UI configuration"""
        return UIConfig(
            title=self._get_env('UI_TITLE', "Person ReID System"),
            page_icon=self._get_env('UI_PAGE_ICON', "👤"),
            layout=self._get_env('UI_LAYOUT', "wide"),
            port=self._get_env('UI_PORT', 8501),
            theme=self._get_env('UI_THEME', "light")
        )

    def _init_features_config(self) -> FeaturesConfig:
        """Initialize features configuration"""
        return FeaturesConfig(
            auto_refresh=self._get_env('UI_AUTO_REFRESH', True),
            auto_refresh_interval=self._get_env('UI_REFRESH_INTERVAL', 5),
            enable_charts=self._get_env('UI_ENABLE_CHARTS', True),
            enable_export=self._get_env('UI_ENABLE_EXPORT', True),
            debug_mode=self._get_env('DEBUG_MODE', False)
        )

    def _init_display_config(self) -> DisplayConfig:
        """Initialize display configuration"""
        return DisplayConfig(
            max_users_per_page=self._get_env('UI_MAX_USERS_PER_PAGE', 100),
            max_zones_per_page=self._get_env('UI_MAX_ZONES_PER_PAGE', 100),
            max_messages=self._get_env('UI_MAX_MESSAGES', 500),
            date_format=self._get_env('UI_DATE_FORMAT', "%Y-%m-%d %H:%M:%S")
        )

    def _init_charts_config(self) -> ChartsConfig:
        """Initialize charts configuration"""
        return ChartsConfig(
            color_scheme=self._get_env('UI_CHART_COLOR_SCHEME', "plotly"),
            default_height=self._get_env('UI_CHART_HEIGHT', 500),
            animation=self._get_env('UI_CHART_ANIMATION', True)
        )

    def _init_alerts_config(self) -> AlertsConfig:
        """Initialize alerts configuration"""
        return AlertsConfig(
            show_notifications=self._get_env('UI_SHOW_NOTIFICATIONS', True),
            sound_enabled=self._get_env('UI_SOUND_ENABLED', False),
            desktop_notifications=self._get_env('UI_DESKTOP_NOTIFICATIONS', False)
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
