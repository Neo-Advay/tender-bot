import yaml
import os

def load_config(config_path="config.yaml"):
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if os.getenv("SMTP_HOST"):
        config.setdefault("smtp", {})
        config["smtp"]["host"]         = os.getenv("SMTP_HOST")
        config["smtp"]["username"]     = os.getenv("SMTP_USERNAME")
        config["smtp"]["password"]     = os.getenv("SMTP_PASSWORD")
        config["smtp"]["from_address"] = os.getenv("SMTP_FROM")
        config["smtp"]["recipients"]   = os.getenv("SMTP_RECIPIENTS", "").split(",")

    return config

# Usage example
# config = load_config()
# print(config['relevance']['keywords_strong'])