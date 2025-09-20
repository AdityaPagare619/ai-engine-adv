# ai_engine/src/knowledge_tracing/config/settings.py
from pydantic import BaseSettings, Field

class KTSettings(BaseSettings):
    # Feature flags
    enable_sakt: bool = Field(default=False, description="Enable SAKT ensemble path")
    enable_bandit: bool = Field(default=True, description="Enable contextual bandit selection")
    enable_hlr: bool = Field(default=True, description="Enable half-life review scheduling")

    # Evaluation thresholds (blueprint-aligned)
    auc_target: float = Field(default=0.75, description="Minimum acceptable next-step AUC")
    brier_target: float = Field(default=0.20, description="Maximum acceptable Brier score")
    ece_target: float = Field(default=0.10, description="Maximum acceptable ECE")
    trajectory_validity_target: float = Field(default=0.60, description="Minimum acceptable trajectory validity")

    # Safety rails for context adjustments
    max_guess: float = Field(default=0.50)
    max_slip: float = Field(default=0.30)
    max_learn_rate: float = Field(default=0.50)

    class Config:
        env_prefix = "KT_"
        case_sensitive = False
