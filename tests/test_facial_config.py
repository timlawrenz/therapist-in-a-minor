import pytest
import yaml

def test_config_has_facial_settings():
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
    
    assert "facial" in config["enrichment"]
    assert config["enrichment"]["facial"]["enabled"] is True
    assert config["enrichment"]["facial"]["model_name"] == "buffalo_l"
