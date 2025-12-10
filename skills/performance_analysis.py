"""
Performance Analysis Skill - AWR and OPSI metrics analysis
Tier 2/3 (API/Database, 1-30s)

This skill analyzes database performance using AWR reports and OPSI metrics,
following the skillz pattern for composable AI agent skills.

Reference: https://github.com/intellectronica/skillz
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics data"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    io_throughput_mbps: float
    active_sessions: int


@dataclass
class PerformanceAnalysis:
    """Performance analysis results"""
    current_usage: float
    average_usage: float
    peak_usage: float
    trend: str  # "increasing", "decreasing", "stable"
    recommendations: List[str]
    metrics: List[PerformanceMetrics]


class PerformanceAnalysisSkill:
    """
    Skill: Database performance analysis
    
    Analyzes AWR reports, OPSI metrics, and provides insights.
    Uses intelligent caching to minimize API calls.
    
    Tier: 2/3 (API/Database-based, 1-30s)
    Category: Analysis
    """
    
    def __init__(self, opsi_client, cache_manager):
        """
        Initialize the performance analysis skill
        
        Args:
            opsi_client: OPSI API client instance
            cache_manager: Cache manager for performance data
        """
        self.opsi = opsi_client
        self.cache = cache_manager
        self.tier = 2  # API-based operation
        self.category = "analysis"
        self.name = "performance_analysis"
        self.description = "Database performance analysis using OPSI metrics"
    
    def analyze_cpu_usage(
        self,
        database_id: str,
        hours_back: int = 24
    ) -> PerformanceAnalysis:
        """
        Analyze CPU usage trends
        
        Args:
            database_id: Database OCID
            hours_back: Number of hours to analyze (default: 24)
        
        Returns:
            PerformanceAnalysis object with CPU analysis results
        """
        logger.info(f"Analyzing CPU usage for {database_id} over {hours_back} hours")
        
        # Get OPSI metrics
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours_back)
        
        metrics = self._get_cpu_metrics(database_id, start_time, end_time)
        
        if not metrics:
            logger.warning(f"No CPU metrics found for {database_id}")
            return PerformanceAnalysis(
                current_usage=0.0,
                average_usage=0.0,
                peak_usage=0.0,
                trend="insufficient_data",
                recommendations=["No metrics available - check OPSI configuration"],
                metrics=[]
            )
        
        # Analyze trends
        current_usage = metrics[-1].cpu_percent if metrics else 0.0
        average_usage = sum(m.cpu_percent for m in metrics) / len(metrics)
        peak_usage = max(m.cpu_percent for m in metrics)
        trend = self._detect_trend([m.cpu_percent for m in metrics])
        
        analysis = PerformanceAnalysis(
            current_usage=current_usage,
            average_usage=average_usage,
            peak_usage=peak_usage,
            trend=trend,
            recommendations=[],
            metrics=metrics
        )
        
        # Generate recommendations
        analysis.recommendations = self._generate_cpu_recommendations(analysis)
        
        logger.info(
            f"CPU analysis complete: current={current_usage:.1f}%, "
            f"avg={average_usage:.1f}%, peak={peak_usage:.1f}%, trend={trend}"
        )
        
        return analysis
    
    def analyze_memory_usage(
        self,
        database_id: str,
        hours_back: int = 24
    ) -> PerformanceAnalysis:
        """
        Analyze memory usage trends
        
        Args:
            database_id: Database OCID
            hours_back: Number of hours to analyze (default: 24)
        
        Returns:
            PerformanceAnalysis object with memory analysis results
        """
        logger.info(f"Analyzing memory usage for {database_id} over {hours_back} hours")
        
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours_back)
        
        metrics = self._get_memory_metrics(database_id, start_time, end_time)
        
        if not metrics:
            logger.warning(f"No memory metrics found for {database_id}")
            return PerformanceAnalysis(
                current_usage=0.0,
                average_usage=0.0,
                peak_usage=0.0,
                trend="insufficient_data",
                recommendations=["No metrics available - check OPSI configuration"],
                metrics=[]
            )
        
        current_usage = metrics[-1].memory_percent if metrics else 0.0
        average_usage = sum(m.memory_percent for m in metrics) / len(metrics)
        peak_usage = max(m.memory_percent for m in metrics)
        trend = self._detect_trend([m.memory_percent for m in metrics])
        
        analysis = PerformanceAnalysis(
            current_usage=current_usage,
            average_usage=average_usage,
            peak_usage=peak_usage,
            trend=trend,
            recommendations=[],
            metrics=metrics
        )
        
        analysis.recommendations = self._generate_memory_recommendations(analysis)
        
        logger.info(
            f"Memory analysis complete: current={current_usage:.1f}%, "
            f"avg={average_usage:.1f}%, peak={peak_usage:.1f}%, trend={trend}"
        )
        
        return analysis
    
    def analyze_io_performance(
        self,
        database_id: str,
        hours_back: int = 24
    ) -> PerformanceAnalysis:
        """
        Analyze I/O performance trends
        
        Args:
            database_id: Database OCID
            hours_back: Number of hours to analyze (default: 24)
        
        Returns:
            PerformanceAnalysis object with I/O analysis results
        """
        logger.info(f"Analyzing I/O performance for {database_id} over {hours_back} hours")
        
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours_back)
        
        metrics = self._get_io_metrics(database_id, start_time, end_time)
        
        if not metrics:
            logger.warning(f"No I/O metrics found for {database_id}")
            return PerformanceAnalysis(
                current_usage=0.0,
                average_usage=0.0,
                peak_usage=0.0,
                trend="insufficient_data",
                recommendations=["No metrics available - check OPSI configuration"],
                metrics=[]
            )
        
        current_usage = metrics[-1].io_throughput_mbps if metrics else 0.0
        average_usage = sum(m.io_throughput_mbps for m in metrics) / len(metrics)
        peak_usage = max(m.io_throughput_mbps for m in metrics)
        trend = self._detect_trend([m.io_throughput_mbps for m in metrics])
        
        analysis = PerformanceAnalysis(
            current_usage=current_usage,
            average_usage=average_usage,
            peak_usage=peak_usage,
            trend=trend,
            recommendations=[],
            metrics=metrics
        )
        
        analysis.recommendations = self._generate_io_recommendations(analysis)
        
        logger.info(
            f"I/O analysis complete: current={current_usage:.1f} MB/s, "
            f"avg={average_usage:.1f} MB/s, peak={peak_usage:.1f} MB/s, trend={trend}"
        )
        
        return analysis
    
    def get_performance_summary(
        self,
        database_id: str,
        hours_back: int = 24
    ) -> Dict:
        """
        Get comprehensive performance summary
        
        Args:
            database_id: Database OCID
            hours_back: Number of hours to analyze (default: 24)
        
        Returns:
            Dict containing all performance metrics and analysis
        """
        logger.info(f"Getting performance summary for {database_id}")
        
        cpu_analysis = self.analyze_cpu_usage(database_id, hours_back)
        memory_analysis = self.analyze_memory_usage(database_id, hours_back)
        io_analysis = self.analyze_io_performance(database_id, hours_back)
        
        summary = {
            "database_id": database_id,
            "time_range_hours": hours_back,
            "timestamp": datetime.utcnow().isoformat(),
            "cpu": {
                "current": cpu_analysis.current_usage,
                "average": cpu_analysis.average_usage,
                "peak": cpu_analysis.peak_usage,
                "trend": cpu_analysis.trend
            },
            "memory": {
                "current": memory_analysis.current_usage,
                "average": memory_analysis.average_usage,
                "peak": memory_analysis.peak_usage,
                "trend": memory_analysis.trend
            },
            "io": {
                "current": io_analysis.current_usage,
                "average": io_analysis.average_usage,
                "peak": io_analysis.peak_usage,
                "trend": io_analysis.trend
            },
            "recommendations": (
                cpu_analysis.recommendations +
                memory_analysis.recommendations +
                io_analysis.recommendations
            )
        }
        
        logger.info("Performance summary complete")
        return summary
    
    def _get_cpu_metrics(
        self,
        database_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[PerformanceMetrics]:
        """Get CPU metrics from OPSI"""
        # Check cache first
        cache_key = f"cpu_metrics_{database_id}_{start_time.isoformat()}"
        cached = self.cache.get(cache_key)
        
        if cached and not self.cache.is_stale(cached):
            logger.debug(f"Using cached CPU metrics for {database_id}")
            return cached
        
        # Fetch from OPSI API
        logger.debug(f"Fetching CPU metrics from OPSI for {database_id}")
        raw_metrics = self.opsi.get_cpu_metrics(database_id, start_time, end_time)
        
        # Convert to PerformanceMetrics objects
        metrics = [
            PerformanceMetrics(
                timestamp=m.get("timestamp"),
                cpu_percent=m.get("cpu_percent", 0.0),
                memory_percent=0.0,
                io_throughput_mbps=0.0,
                active_sessions=m.get("active_sessions", 0)
            )
            for m in raw_metrics
        ]
        
        # Cache results
        self.cache.set(cache_key, metrics)
        
        return metrics
    
    def _get_memory_metrics(
        self,
        database_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[PerformanceMetrics]:
        """Get memory metrics from OPSI"""
        cache_key = f"memory_metrics_{database_id}_{start_time.isoformat()}"
        cached = self.cache.get(cache_key)
        
        if cached and not self.cache.is_stale(cached):
            return cached
        
        raw_metrics = self.opsi.get_memory_metrics(database_id, start_time, end_time)
        
        metrics = [
            PerformanceMetrics(
                timestamp=m.get("timestamp"),
                cpu_percent=0.0,
                memory_percent=m.get("memory_percent", 0.0),
                io_throughput_mbps=0.0,
                active_sessions=m.get("active_sessions", 0)
            )
            for m in raw_metrics
        ]
        
        self.cache.set(cache_key, metrics)
        return metrics
    
    def _get_io_metrics(
        self,
        database_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[PerformanceMetrics]:
        """Get I/O metrics from OPSI"""
        cache_key = f"io_metrics_{database_id}_{start_time.isoformat()}"
        cached = self.cache.get(cache_key)
        
        if cached and not self.cache.is_stale(cached):
            return cached
        
        raw_metrics = self.opsi.get_io_metrics(database_id, start_time, end_time)
        
        metrics = [
            PerformanceMetrics(
                timestamp=m.get("timestamp"),
                cpu_percent=0.0,
                memory_percent=0.0,
                io_throughput_mbps=m.get("io_throughput_mbps", 0.0),
                active_sessions=0
            )
            for m in raw_metrics
        ]
        
        self.cache.set(cache_key, metrics)
        return metrics
    
    def _detect_trend(self, values: List[float]) -> str:
        """Detect usage trend (simple linear regression)"""
        if len(values) < 2:
            return "insufficient_data"
        
        # Simple trend detection: compare first half vs second half
        mid = len(values) // 2
        first_half_avg = sum(values[:mid]) / mid
        second_half_avg = sum(values[mid:]) / (len(values) - mid)
        
        diff = second_half_avg - first_half_avg
        
        if diff > 5:
            return "increasing"
        elif diff < -5:
            return "decreasing"
        else:
            return "stable"
    
    def _generate_cpu_recommendations(self, analysis: PerformanceAnalysis) -> List[str]:
        """Generate CPU-specific recommendations"""
        recommendations = []
        
        if analysis.peak_usage > 90:
            recommendations.append(
                "CRITICAL: CPU peak usage >90% - immediate scaling recommended"
            )
        elif analysis.peak_usage > 80:
            recommendations.append(
                "WARNING: CPU peak usage >80% - consider scaling CPU resources"
            )
        
        if analysis.average_usage > 70:
            recommendations.append(
                "Review top SQL for optimization opportunities"
            )
        
        if analysis.trend == "increasing":
            recommendations.append(
                "CPU usage trending upward - monitor closely and plan capacity"
            )
        
        if analysis.average_usage < 30:
            recommendations.append(
                "Low CPU utilization - consider rightsizing to reduce costs"
            )
        
        return recommendations
    
    def _generate_memory_recommendations(self, analysis: PerformanceAnalysis) -> List[str]:
        """Generate memory-specific recommendations"""
        recommendations = []
        
        if analysis.peak_usage > 90:
            recommendations.append(
                "CRITICAL: Memory peak usage >90% - check for memory leaks"
            )
        elif analysis.peak_usage > 80:
            recommendations.append(
                "WARNING: Memory usage >80% - review memory configuration"
            )
        
        if analysis.trend == "increasing":
            recommendations.append(
                "Memory usage trending upward - investigate potential memory leaks"
            )
        
        return recommendations
    
    def _generate_io_recommendations(self, analysis: PerformanceAnalysis) -> List[str]:
        """Generate I/O-specific recommendations"""
        recommendations = []
        
        if analysis.peak_usage > 1000:  # > 1 GB/s
            recommendations.append(
                "High I/O throughput detected - consider storage optimization"
            )
        
        if analysis.trend == "increasing":
            recommendations.append(
                "I/O throughput trending upward - review query patterns"
            )
        
        return recommendations
    
    def get_metadata(self) -> Dict:
        """
        Get skill metadata
        
        Returns:
            Dict containing skill metadata
        """
        return {
            "name": self.name,
            "description": self.description,
            "tier": self.tier,
            "category": self.category,
            "version": "1.0.0",
            "author": "Oracle DB Team"
        }
