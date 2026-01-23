from dataclasses import dataclass
import os
from pathlib import Path
import tomllib


CONFIG_PATH = os.environ["CONFIG_PATH"]

@dataclass
class Config:
    username: str
    password: str
    base_url: str
    med_id: str
    office: str

    @classmethod
    def from_toml(cls, path: str = CONFIG_PATH) -> "Config":

        config_file = Path(path)
        required_fields = [
            "username",
            "password",
            "base_url",
            "med_id",
            "office",
        ]

        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found at {path}")

        with open(config_file, "rb") as file:
            config = tomllib.load(file)

        missing_or_empty_fields = [
            field
            for field in required_fields
            if field not in config or not config[field]
        ]

        if missing_or_empty_fields:
            raise ValueError(
                "Missing or empty required fields in config file: "
                f"{', '.join(missing_or_empty_fields)}"
            )

        try:
            return cls(
                username=config["username"],
                password=config["password"],
                base_url=config["base_url"],
                med_id=config["med_id"],
                office=config["office"],
            )
        except (KeyError, ValueError) as e:
            raise ValueError(f"Error parsing config file: {e}")
