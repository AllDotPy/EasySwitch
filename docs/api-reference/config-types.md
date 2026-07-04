# Configuration Models (`easyswitch.conf`)

This module defines the configuration system for EasySwitch. It provides Pydantic-based models with strict validation, and a `ConfigManager` that aggregates configuration from multiple sources.

---

## RootConfig

The **root configuration** for EasySwitch. Passed to the `EasySwitch` client.

```python
class RootConfig(BaseConfigModel):
    environment: str = "sandbox"                        # "sandbox" | "production"
    timeout: int = 30                                   # Default timeout in seconds
    debug: bool = False
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    default_currency: str = "XOF"
    providers: Dict[Provider, ProviderConfig] = Field(default_factory=dict)
    default_provider: Optional[Provider] = None
```

**Fields:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `environment` | `str` | `"sandbox"` | Global environment for all providers |
| `timeout` | `int` | `30` | Default HTTP timeout (seconds) |
| `debug` | `bool` | `False` | Enable debug logging |
| `logging` | `LoggingConfig` | — | Logging configuration |
| `default_currency` | `str` | `"XOF"` | Default currency for transactions |
| `providers` | `Dict[Provider, ProviderConfig]` | `{}` | Enabled providers and their configs |
| `default_provider` | `Optional[Provider]` | `None` | Provider used when none is specified |

**Validations:**
- `default_provider` (if set) must be present in `providers` and a valid `Provider` enum member
- `default_currency` must be a valid `Currency` enum member

---

## ProviderConfig

Configuration for a **single payment provider**.

```python
class ProviderConfig(BaseConfigModel):
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    token: Optional[str] = None
    base_url: Optional[str] = None
    callback_url: Optional[str] = None
    return_url: Optional[str] = None
    timeout: int = 30              # Overrides global timeout for this provider
    environment: str = "sandbox"   # "sandbox" | "production"
    extra: Dict[str, Any] = {}     # Provider-specific settings
```

**Validations:**
- `environment` must be `"sandbox"` or `"production"`
- At least one of `api_key` or `api_secret` must be provided

---

## LoggingConfig

```python
class LoggingConfig(BaseModel):
    enabled: bool = False
    level: LogLevel = LogLevel.INFO
    file: Optional[str] = None
    console: bool = True
    max_size: int = 10     # MB before rotation
    backups: int = 5
    compress: bool = True
    format: LogFormat = LogFormat.PLAIN   # "plain" | "json"
    rotate: bool = True
```

---

## ConfigManager

Loads and merges configuration from multiple sources, validates against `RootConfig`.

```python
manager = ConfigManager()
manager.add_source('env', env_file=".env")
manager.add_source('json', file_path="config.json")
config = manager.load().get_config()   # Returns RootConfig
```

Client shortcuts:

```python
EasySwitch.from_env(".env")
EasySwitch.from_json("config.json")
EasySwitch.from_yaml("config.yaml")
EasySwitch.from_dict({"providers": {...}})
EasySwitch.from_multi_sources(env_file=".env", json_file="config.json")
```

---

## Custom Configuration Sources

Implement `BaseConfigSource` and register with `@register_source`:

```python
from easyswitch.conf import register_source, BaseConfigSource

@register_source('toml')
class TomlConfigSource(BaseConfigSource):
    def __init__(self, path: str):
        self.path = path

    def is_valid(self) -> bool:
        return Path(self.path).exists()

    def load(self) -> Dict[str, Any]:
        import toml
        return toml.load(self.path)
```

Then use it:

```python
manager = ConfigManager()
manager.add_source('toml', path="config.toml")
```
