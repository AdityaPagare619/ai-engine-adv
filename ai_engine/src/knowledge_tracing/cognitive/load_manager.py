# Thin alias shim to keep documentation path stable.
# Internally delegate to the existing implementation under 'congnitive'.
from ai_engine.src.knowledge_tracing.congnitive.load_manager import (
    CognitiveLoadManager,
    LoadAssessment,
    LoadType,
)
