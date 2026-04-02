import logging
import os
from datetime import datetime

def setup_logger(module_name: str) -> logging.Logger:
    """
    Creates and configures a dual-handler logger for a given module.

    Directory structure created:
        /logs
          └── /{module_name}/
               ├── latest_{module_name}.log          # Overwritten on every run (DEBUG level, full X-ray)
               └── /daily_{module_name}/
                    └── daily_{module_name}_YYYY-MM-DD.log  # Appended daily (INFO+ level, hybrid history)

    Developer conventions:
        - logger.debug()   → Transactional data: API responses, raw fields, timing, loop details.
        - logger.info()    → Crucial milestones only: run started, batch completed, file saved.
        - logger.warning() → Business-rule discards: language rejection, quota cap, missing field.
        - logger.error()   → Caught exceptions that caused a skip or partial failure.
        - logger.critical() → Circuit-breaker events (e.g., IP_BLOCKED) that halt the pipeline.
    """

    # ── Directory setup ──────────────────────────────────────────────────────
    base_log_dir   = os.path.join("logs", module_name)
    daily_log_dir  = os.path.join(base_log_dir, f"daily_{module_name}")
    os.makedirs(base_log_dir,  exist_ok=True)
    os.makedirs(daily_log_dir, exist_ok=True)

    latest_path = os.path.join(base_log_dir, f"latest_{module_name}.log")
    daily_path  = os.path.join(
        daily_log_dir,
        f"daily_{module_name}_{datetime.now().strftime('%Y-%m-%d')}.log"
    )

    # ── Formatter ────────────────────────────────────────────────────────────
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M"
    )

    # ── Logger instance ──────────────────────────────────────────────────────
    logger = logging.getLogger(module_name)
    logger.setLevel(logging.DEBUG)   # Root level: capture everything

    # Guard against duplicate handlers if setup_logger is called more than once
    if logger.handlers:
        return logger

    # ── Handler 1: Full X-Ray — latest_{module}.log (overwrite, DEBUG) ──────
    latest_handler = logging.FileHandler(latest_path, mode="w", encoding="utf-8")
    latest_handler.setLevel(logging.DEBUG)
    latest_handler.setFormatter(formatter)

    # ── Handler 2: Hybrid Daily History — daily_{module}_YYYY-MM-DD.log ─────
    # INFO  → Milestones (run started, N items saved)
    # WARNING → Business-rule discards (language filter, source cap)
    # ERROR / CRITICAL → Failures and circuit-breakers
    daily_handler = logging.FileHandler(daily_path, mode="a", encoding="utf-8")
    daily_handler.setLevel(logging.INFO)
    daily_handler.setFormatter(formatter)

    # ── Handler 3: Console — INFO+ only (human-readable run progress) ────────
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    logger.addHandler(latest_handler)
    logger.addHandler(daily_handler)
    logger.addHandler(console_handler)

    return logger


# ==============================================================================
# USAGE EXAMPLE
# ==============================================================================
if __name__ == "__main__":
    # ── Instantiate the logger for the scraping module ────────────────────────
    logger = setup_logger("scraping")

    # ── Milestone: run started ────────────────────────────────────────────────
    logger.info("Scraping run started for topic: 'Privatizações de Serviços'")

    # ── Debug: transactional data (only visible in latest_scraping.log) ───────
    video_title = "A privatização dos Correios — análise completa"
    video_id    = "dQw4w9WgXcQ"
    votes       = {"LangDetect": True, "Lingua": False, "FastText": True}
    
    logger.debug(f"Evaluating video id={video_id} | title='{video_title}' | votes={votes}")

    # ── Warning: business-rule discard — Lingua voted False ──────────────────
    # This will appear in BOTH latest_scraping.log AND daily_scraping_YYYY-MM-DD.log
    if not votes["Lingua"]:
        logger.warning(
            f"DISCARD | Lingua voted NOT Portuguese | "
            f"title='{video_title}' | votes={votes}"
        )

    # ── Info: milestone ───────────────────────────────────────────────────────
    logger.info("Batch #1 complete. 3 videos accepted, 1 discarded.")

    # ── Error: caught exception ───────────────────────────────────────────────
    logger.error("Caption extraction failed for video dQw4w9WgXcQ: JSONDecodeError")

    # ── Critical: circuit breaker ─────────────────────────────────────────────
    logger.critical("IP_BLOCKED signal detected. Halting pipeline immediately.")
