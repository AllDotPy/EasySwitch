"""
EasySwitch - Env config source loader.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

from easyswitch.conf import register_source
from easyswitch.conf.base import BaseConfigSource


####
##      ENVIRONMENT CONFIGURATION SOURSE CLASS
#####
@register_source('env')
class EnvConfigSource(BaseConfigSource):
    """Loads EasySwitch configurations from environment variables."""

    def __init__(self, env_file: Optional[str] = None):
        self.env_file = Path(env_file) if env_file else None

    def load(self) -> Dict[str, Any]:
        """Loads configs from .env file."""

        # Load env first
        load_dotenv(self.env_file)
        
        config = {
            'environment': os.getenv('EASYSWITCH_ENVIRONMENT', 'sandbox').lower(),
            'timeout': self._parse_int('EASYSWITCH_TIMEOUT', 30),
            'debug': self._parse_bool('EASYSWITCH_DEBUG', False),
            'default_currency': os.getenv('EASYSWITCH_DEFAULT_CURRENCY', 'XOF'),
            'logging': self._load_logging_config(),
            'providers': self._load_providers_config()
        }
        
        # Set default provider if specified
        if default_provider := os.getenv('EASYSWITCH_DEFAULT_PROVIDER'):
            config['default_provider'] = default_provider.upper()
        
        return config
    
    def _load_logging_config(self) -> Dict[str, Any]:
        """Loads Logging configurations."""
        if not self._parse_bool('EASYSWITCH_LOGGING', False):
            return {}
            
        return {
            'enabled': True,
            'level': os.getenv('EASYSWITCH_LOG_LEVEL', 'info').lower(),
            'file': os.getenv('EASYSWITCH_LOG_FILE'),
            'console': self._parse_bool('EASYSWITCH_CONSOLE_LOGGING', True),
            'max_size': self._parse_int('EASYSWITCH_LOG_MAX_SIZE', 10),
            'backups': self._parse_int('EASYSWITCH_LOG_BACKUPS', 5),
            'compress': self._parse_bool('EASYSWITCH_LOG_COMPRESS', True),
            'format': os.getenv('EASYSWITCH_LOG_FORMAT', 'plain').lower(),
            'rotate': self._parse_bool('EASYSWITCH_LOG_ROTATE', True)
        }
    
    def _load_providers_config(self) -> Dict[str, Dict[str, Any]]:
        """Load providers configurations."""
        
        providers_config = {}
        enabled_providers = self._parse_list('EASYSWITCH_ENABLED_PROVIDERS')
        
        for provider in enabled_providers:
            provider_key = provider.upper()
            prefix = f"EASYSWITCH_{provider_key}_"
            extra_attrs_prefix = f"{prefix}X_"
            
            # Collect all variables for this provider
            provider_vars = {}
            provider_vars['extra'] = {}
            for key, value in os.environ.items():
                if key.startswith(prefix):
                    # It's an extra attribute?
                    if key.startswith(extra_attrs_prefix):
                        # Then add it to extra attr
                        provider_vars['extra'][key[len(extra_attrs_prefix):].lower()] = value

                    else:
                        config_key = key[len(prefix):].lower()
                        provider_vars[config_key] = self._parse_value(value)
            
            if provider_vars:
                providers_config[provider_key] = provider_vars
        
        return providers_config

    def _parse_bool(self, var_name: str, default: bool = False) -> bool:
        """Parse a variable into bollean"""
        value = os.getenv(var_name)
        if value is None:
            return default
        return value.lower() in ('true', '1', 'yes', 'y', 't')

    def _parse_int(self, var_name: str, default: int) -> int:
        """Parse a variable into int"""
        try:
            return int(os.getenv(var_name, str(default)))
        except ValueError:
            return default

    def _parse_float(self, var_name: str, default: float) -> float:
        """Parse a variable into float"""
        try:
            return float(os.getenv(var_name, str(default)))
        except ValueError:
            return default

    def _parse_list(self, var_name: str, sep: str = ',') -> List[str]:
        """Parse a variable into list"""
        value = os.getenv(var_name, '')
        return [item.strip().lower() for item in value.split(sep) if item.strip()]

    def _parse_value(self, value: str) -> Any:
        """Try to convert automaticaly a variable type"""
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        try:
            return int(value)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                return value

    def is_valid(self) -> bool:
        """check if .env exists and is valid valide"""
        if self.env_file and not self.env_file.exists():
            return False
        return True