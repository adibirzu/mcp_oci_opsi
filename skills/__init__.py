"""
OPSI Skills Package - Composable AI Agent Skills

This package provides intelligent, composable skills for Oracle Database
management and optimization, following the skillz pattern.

Reference: https://github.com/intellectronica/skillz

Available Skills:
- DatabaseDiscoverySkill: Fast database fleet discovery (Tier 1, Cache-based)
- PerformanceAnalysisSkill: Database performance analysis (Tier 2/3, API/DB)
- CostOptimizationSkill: Cost-saving opportunity identification (Tier 2, API)

Adapters:
- CacheManager: Wrapper for EnhancedDatabaseCache for skill use
- OPSIClient: Wrapper for OCI Operations Insights API for skill use
"""

from .database_discovery import DatabaseDiscoverySkill, DatabaseInfo
from .performance_analysis import (
    PerformanceAnalysisSkill,
    PerformanceMetrics,
    PerformanceAnalysis
)
from .cost_optimization import CostOptimizationSkill, CostOpportunity
from .adapters import CacheManager, OPSIClient

__all__ = [
    # Skills
    "DatabaseDiscoverySkill",
    "PerformanceAnalysisSkill",
    "CostOptimizationSkill",
    
    # Data classes
    "DatabaseInfo",
    "PerformanceMetrics",
    "PerformanceAnalysis",
    "CostOpportunity",
    
    # Adapters
    "CacheManager",
    "OPSIClient",
]

__version__ = "1.0.0"
__author__ = "Oracle DB Team"
