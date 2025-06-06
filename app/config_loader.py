from pathlib import Path
import yaml


def load_settings() -> dict:
    """Load configuration from configs/settings.yaml.

    Returns:
        dict: Parsed settings dictionary.

    Raises:
        FileNotFoundError: If the configuration file does not exist.
        RuntimeError: If the YAML content cannot be parsed.
        ValueError: If the configuration is empty or invalid.
    """
    settings_path = Path(__file__).resolve().parent.parent / "configs" / "settings.yaml"

    if not settings_path.exists():
        raise FileNotFoundError(f"Configuration file not found at {settings_path}")

    try:
        with settings_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        raise RuntimeError(f"Error parsing YAML configuration: {exc}") from exc

    if data is None:
        raise ValueError("Configuration file is empty")
    if not isinstance(data, dict):
        raise ValueError("Configuration format must be a mapping")

    return data
