"""Configuration loader for Memory Board.

Loads all system constants exclusively from config/config.yaml.
Strictly disallows ad-hoc hardcoded magic numbers.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict
import yaml

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = ROOT_DIR / "config" / "config.yaml"
DATA_DIR = ROOT_DIR / "data"
PHOTOS_DIR = DATA_DIR / "photos"
THUMBS_DIR = DATA_DIR / "thumbs"
DB_PATH = DATA_DIR / "app.db"
EMBEDDINGS_PATH = DATA_DIR / "embeddings.npy"


@dataclass
class BoardConfig:
    cards_min: int
    cards_max: int
    min_support: float
    max_support: float
    mmr_lambda: float
    max_card_overlap: float
    min_library_for_board: int


@dataclass
class GroupsConfig:
    candidate_pool: int
    group_min: int
    group_max: int
    groups_shown: int


@dataclass
class BandsConfig:
    highest: float
    good: float
    possible: float


@dataclass
class ConfidenceConfig:
    w_match: float
    w_exclusion: float
    w_tight: float
    w_prior: float
    evidence_clues_for_full: int
    bands: BandsConfig
    tie_margin: float
    show_percentages: bool


@dataclass
class ClueWeightsConfig:
    cue: float
    answer: float
    source: float
    sentence: float
    almost: float


@dataclass
class QuestionsConfig:
    max_questions: int
    min_gain_bits: float
    min_option_share: float


@dataclass
class NudgeConfig:
    seconds: int
    scroll_gap_ms: int
    reversals: int
    months_scrolled: int
    rows_scrolled: int
    per_session_max: int
    dismiss_window_days: int
    dismiss_limit: int
    suppress_days: int
    quiet_after_found_s: int


@dataclass
class BehaviourConfig:
    top_share: float
    not_opened_days: int
    prior_weights: Dict[str, float]


@dataclass
class PerformanceConfig:
    step_server_ms_p95: int
    step_total_ms: int


@dataclass
class SimConfig:
    p_know: Dict[str, float]
    p_pick: float
    p_wrong: float
    p_recognise: float
    sessions: int


@dataclass
class AppConfig:
    board: BoardConfig
    groups: GroupsConfig
    confidence: ConfidenceConfig
    clue_weights: ClueWeightsConfig
    questions: QuestionsConfig
    nudge: NudgeConfig
    behaviour: BehaviourConfig
    performance: PerformanceConfig
    sim: SimConfig


def load_config(path: Path = CONFIG_PATH) -> AppConfig:
    """Load and validate config.yaml into strongly-typed AppConfig."""
    if not path.exists():
        raise FileNotFoundError(f"Configuration file missing at {path}")

    with open(path, "r", encoding="utf-8") as f:
        data: Dict[str, Any] = yaml.safe_load(f)

    conf_bands = data["confidence"]["bands"]
    bands = BandsConfig(
        highest=conf_bands["highest"],
        good=conf_bands["good"],
        possible=conf_bands["possible"],
    )

    conf_data = data["confidence"]
    confidence = ConfidenceConfig(
        w_match=conf_data["w_match"],
        w_exclusion=conf_data["w_exclusion"],
        w_tight=conf_data["w_tight"],
        w_prior=conf_data["w_prior"],
        evidence_clues_for_full=conf_data["evidence_clues_for_full"],
        bands=bands,
        tie_margin=conf_data["tie_margin"],
        show_percentages=conf_data["show_percentages"],
    )

    return AppConfig(
        board=BoardConfig(**data["board"]),
        groups=GroupsConfig(**data["groups"]),
        confidence=confidence,
        clue_weights=ClueWeightsConfig(**data["clue_weights"]),
        questions=QuestionsConfig(**data["questions"]),
        nudge=NudgeConfig(**data["nudge"]),
        behaviour=BehaviourConfig(**data["behaviour"]),
        performance=PerformanceConfig(**data["performance"]),
        sim=SimConfig(**data["sim"]),
    )


# Singleton config instance
CONFIG = load_config()
