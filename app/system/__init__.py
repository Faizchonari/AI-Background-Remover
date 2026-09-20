"""System inspection, recommendation, and dependency management package."""

from app.system.system_info import SystemInfo, get_system_info
from app.system.recommendation import ModelRecommendationEngine, RecommendationResult, ModelProfile
from app.system.dependency_manager import DependencyManager, DependencyInfo

__all__ = [
    "SystemInfo",
    "get_system_info",
    "ModelRecommendationEngine",
    "RecommendationResult",
    "ModelProfile",
    "DependencyManager",
    "DependencyInfo",
]
