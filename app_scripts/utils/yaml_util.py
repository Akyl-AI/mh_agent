import yaml
from pathlib import Path

config_path = "app_scripts/utils/config.yaml"

def load_config(yaml_file: Path = config_path) -> dict:
    if isinstance(yaml_file, str):
        yaml_file = Path(yaml_file)

    if yaml_file.suffix != ".yaml":
        raise TypeError("Not a YAML file")
    
    # Load the config file
    with yaml_file.open('rt', encoding='utf-8') as f:
        config = yaml.safe_load(f.read())
        
    return config