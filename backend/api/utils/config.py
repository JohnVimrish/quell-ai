
from dataclasses import dataclass
from typing import Dict, Any
from dotenv import load_dotenv
import json, os
from pathlib import Path

@dataclass
class Config:
    """Application configuration container."""
    database_url: str
    providers: Dict[str, Any]
    policies: Dict[str, Any]
    queries: Dict[str, Any]
    debug: bool
    logging: Dict[str, Any]
    
    @staticmethod
    def load() -> "Config":
        load_dotenv()
        root = Path(__file__).resolve().parents[2]

        # Load provider/policy/query definitions
        with open(root/"config"/"providers.json", "r", encoding="utf-8") as f:
            providers = json.load(f)
        with open(root/"config"/"policies.json", "r", encoding="utf-8") as f:
            policies = json.load(f)
        with open(root/"config"/"queries.json", "r", encoding="utf-8") as f:
            queries = json.load(f)

        # Optional application config file
        app_cfg_path = os.getenv("APP_CONFIG_FILE", str(root/"config"/"app.json"))
        app_cfg = {}
        try:
            p = Path(app_cfg_path)
            if p.exists():
                with open(p, "r", encoding="utf-8") as f:
                    app_cfg = json.load(f)
        except Exception:
            app_cfg = {}

        # Resolve database URL
        db_url = (app_cfg.get("database", {}) or {}).get("url") or os.getenv("DATABASE_URL", "")
        if db_url and db_url.startswith("postgresql://"):
            db_url = "postgresql+psycopg://" + db_url[len("postgresql://") :]

        # Logging configuration
        log_cfg = app_cfg.get("logging") or {}

        # Environment overrides
        lvl = os.getenv("LOG_LEVEL")
        if lvl:
            log_cfg["level"] = lvl
        svc = os.getenv("SERVICE_NAME")
        if svc:
            log_cfg["service_name"] = svc

        # Graylog overrides
        gh = os.getenv("GRAYLOG_HOST")
        gp = os.getenv("GRAYLOG_PORT")
        if gh or gp:
            gray = log_cfg.get("graylog") or {}
            if gh:
                gray["host"] = gh
            if gp:
                try:
                    gray["port"] = int(gp)
                except ValueError:
                    gray["port"] = gp
            log_cfg["graylog"] = gray

        # Defaults
        if "level" not in log_cfg:
            log_cfg["level"] = "DEBUG" if bool(app_cfg.get("debug", False)) else "INFO"

        return Config(
            database_url=db_url,
            providers=providers,
            policies=policies,
            queries=queries,
            debug=bool(app_cfg.get("debug", False)),
            logging=log_cfg,
        )
