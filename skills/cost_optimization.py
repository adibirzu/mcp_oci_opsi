"""
Cost Optimization Skill - Identifies cost-saving opportunities
Tier 2 (API-based, 1-5s)

This skill analyzes database utilization patterns to find rightsizing,
scheduling, and resource optimization opportunities, following the skillz
pattern for composable AI agent skills.

Reference: https://github.com/intellectronica/skillz
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class CostOpportunity:
    """Cost-saving opportunity"""
    database_id: str
    database_name: str
    opportunity_type: str  # 'rightsize', 'schedule', 'storage', 'unused'
    estimated_monthly_savings: float  # USD
    confidence: str  # 'high', 'medium', 'low'
    recommendation: str
    action_required: str
    current_monthly_cost: float
    potential_monthly_cost: float


class CostOptimizationSkill:
    """
    Skill: Identify cost-saving opportunities
    
    Analyzes utilization patterns to find rightsizing,
    scheduling, and resource optimization opportunities.
    
    Tier: 2 (API-based, 1-5s)
    Category: Optimization
    """
    
    def __init__(self, opsi_client, cost_client=None):
        """
        Initialize the cost optimization skill
        
        Args:
            opsi_client: OPSI API client instance
            cost_client: Optional cost/billing API client
        """
        self.opsi = opsi_client
        self.cost = cost_client
        self.tier = 2
        self.category = "optimization"
        self.name = "cost_optimization"
        self.description = "Identify database cost-saving opportunities"
        
        # Default cost estimates (USD per month)
        self.default_cost_per_ocpu = 200.0
        self.default_cost_per_gb_storage = 0.025
    
    def find_opportunities(
        self,
        compartment_id: Optional[str] = None,
        min_savings_usd: float = 50.0
    ) -> List[CostOpportunity]:
        """
        Find cost-saving opportunities
        
        Args:
            compartment_id: Filter by compartment (None = all)
            min_savings_usd: Minimum monthly savings to report (default: $50)
        
        Returns:
            List of CostOpportunity objects, sorted by savings
        """
        logger.info(f"Finding cost opportunities in compartment: {compartment_id}")
        
        opportunities = []
        
        # Get all databases
        databases = self._get_databases(compartment_id)
        logger.info(f"Analyzing {len(databases)} databases for cost optimization")
        
        for db in databases:
            try:
                # Check for rightsizing opportunities
                if opp := self._check_rightsizing(db):
                    if opp.estimated_monthly_savings >= min_savings_usd:
                        opportunities.append(opp)
                
                # Check for scheduling opportunities
                if opp := self._check_scheduling(db):
                    if opp.estimated_monthly_savings >= min_savings_usd:
                        opportunities.append(opp)
                
                # Check for storage optimization
                if opp := self._check_storage(db):
                    if opp.estimated_monthly_savings >= min_savings_usd:
                        opportunities.append(opp)
                
                # Check for unused resources
                if opp := self._check_unused(db):
                    if opp.estimated_monthly_savings >= min_savings_usd:
                        opportunities.append(opp)
            
            except Exception as e:
                logger.warning(f"Error analyzing database {db.get('name', 'unknown')}: {e}")
                continue
        
        # Sort by estimated savings
        opportunities.sort(
            key=lambda x: x.estimated_monthly_savings,
            reverse=True
        )
        
        total_savings = sum(o.estimated_monthly_savings for o in opportunities)
        logger.info(
            f"Found {len(opportunities)} opportunities with potential "
            f"savings of ${total_savings:,.2f}/month"
        )
        
        return opportunities
    
    def get_savings_summary(
        self,
        compartment_id: Optional[str] = None
    ) -> Dict:
        """
        Get summary of all cost-saving opportunities
        
        Args:
            compartment_id: Filter by compartment (None = all)
        
        Returns:
            Dict containing savings summary by type and total
        """
        opportunities = self.find_opportunities(compartment_id)
        
        summary = {
            "total_opportunities": len(opportunities),
            "total_monthly_savings": sum(o.estimated_monthly_savings for o in opportunities),
            "by_type": {},
            "by_confidence": {
                "high": [],
                "medium": [],
                "low": []
            },
            "top_opportunities": []
        }
        
        # Group by type
        for opp in opportunities:
            opp_type = opp.opportunity_type
            if opp_type not in summary["by_type"]:
                summary["by_type"][opp_type] = {
                    "count": 0,
                    "total_savings": 0.0
                }
            summary["by_type"][opp_type]["count"] += 1
            summary["by_type"][opp_type]["total_savings"] += opp.estimated_monthly_savings
            
            # Group by confidence
            summary["by_confidence"][opp.confidence].append({
                "database": opp.database_name,
                "type": opp.opportunity_type,
                "savings": opp.estimated_monthly_savings
            })
        
        # Top 10 opportunities
        summary["top_opportunities"] = [
            {
                "database": opp.database_name,
                "type": opp.opportunity_type,
                "savings": opp.estimated_monthly_savings,
                "recommendation": opp.recommendation
            }
            for opp in opportunities[:10]
        ]
        
        logger.info(
            f"Cost summary: {len(opportunities)} opportunities, "
            f"${summary['total_monthly_savings']:,.2f}/month potential savings"
        )
        
        return summary
    
    def _get_databases(self, compartment_id: Optional[str]) -> List[Dict]:
        """Get list of databases to analyze"""
        # This would typically call the OPSI API or use cached data
        # For now, return placeholder
        databases = self.opsi.list_databases(compartment_id)
        return databases
    
    def _check_rightsizing(self, db: Dict) -> Optional[CostOpportunity]:
        """Check if database is over-provisioned"""
        try:
            # Get utilization metrics (last 30 days)
            cpu_usage = self._get_avg_cpu_usage(db["id"], days=30)
            
            if cpu_usage is None:
                logger.debug(f"No CPU metrics for {db['name']}")
                return None
            
            # Over-provisioned if average CPU < 30%
            if cpu_usage < 30:
                current_cpu = db.get("cpu_count", 1)
                
                # Calculate recommended CPU (at least 1 OCPU)
                recommended_cpu = max(1, int(current_cpu * 0.5))
                
                # Calculate costs
                current_cost = self._estimate_monthly_cost(db)
                reduction_pct = (current_cpu - recommended_cpu) / current_cpu
                potential_savings = current_cost * reduction_pct * 0.8  # 80% of CPU cost
                
                return CostOpportunity(
                    database_id=db["id"],
                    database_name=db["name"],
                    opportunity_type="rightsize",
                    estimated_monthly_savings=potential_savings,
                    confidence="high",
                    recommendation=f"Reduce CPU from {current_cpu} to {recommended_cpu} OCPUs",
                    action_required="Scale down database resources",
                    current_monthly_cost=current_cost,
                    potential_monthly_cost=current_cost - potential_savings
                )
        
        except Exception as e:
            logger.warning(f"Error checking rightsizing for {db.get('name')}: {e}")
        
        return None
    
    def _check_scheduling(self, db: Dict) -> Optional[CostOpportunity]:
        """Check if database can be scheduled (dev/test)"""
        try:
            # Check activity patterns (last 7 days)
            activity = self._get_activity_pattern(db["id"], days=7)
            
            if not activity:
                logger.debug(f"No activity data for {db['name']}")
                return None
            
            # Candidate for scheduling if low weekend/night usage
            weekend_usage = activity.get("weekend_usage", 100)
            night_usage = activity.get("night_usage", 100)
            
            if weekend_usage < 10 and night_usage < 10:
                current_cost = self._estimate_monthly_cost(db)
                
                # Savings from stopping 16 hours/day + weekends
                # Approximate: 60% of time stopped = 60% cost savings
                potential_savings = current_cost * 0.6
                
                return CostOpportunity(
                    database_id=db["id"],
                    database_name=db["name"],
                    opportunity_type="schedule",
                    estimated_monthly_savings=potential_savings,
                    confidence="medium",
                    recommendation="Enable auto-stop: weekdays 6pm-8am, all day weekends",
                    action_required="Configure database schedule",
                    current_monthly_cost=current_cost,
                    potential_monthly_cost=current_cost - potential_savings
                )
        
        except Exception as e:
            logger.warning(f"Error checking scheduling for {db.get('name')}: {e}")
        
        return None
    
    def _check_storage(self, db: Dict) -> Optional[CostOpportunity]:
        """Check for storage optimization"""
        try:
            # Get storage usage
            storage_info = self._get_storage_usage(db["id"])
            
            if not storage_info:
                logger.debug(f"No storage data for {db['name']}")
                return None
            
            used_pct = storage_info.get("used_percent", 100)
            allocated_gb = storage_info.get("allocated_gb", 0)
            used_gb = storage_info.get("used_gb", 0)
            
            # Over-allocated if < 40% used
            if used_pct < 40 and allocated_gb > 100:
                # Recommend sizing to 150% of current usage (headroom)
                recommended_gb = max(100, int(used_gb * 1.5))
                reduction_gb = allocated_gb - recommended_gb
                
                # Calculate storage cost savings
                current_storage_cost = allocated_gb * self.default_cost_per_gb_storage
                potential_savings = reduction_gb * self.default_cost_per_gb_storage
                
                if potential_savings >= 10:  # At least $10/month savings
                    current_cost = self._estimate_monthly_cost(db)
                    
                    return CostOpportunity(
                        database_id=db["id"],
                        database_name=db["name"],
                        opportunity_type="storage",
                        estimated_monthly_savings=potential_savings,
                        confidence="low",
                        recommendation=f"Reduce storage from {allocated_gb} GB to {recommended_gb} GB",
                        action_required="Resize storage to match actual usage",
                        current_monthly_cost=current_cost,
                        potential_monthly_cost=current_cost - potential_savings
                    )
        
        except Exception as e:
            logger.warning(f"Error checking storage for {db.get('name')}: {e}")
        
        return None
    
    def _check_unused(self, db: Dict) -> Optional[CostOpportunity]:
        """Check if database appears unused"""
        try:
            # Get connection and activity metrics (last 7 days)
            connections = self._get_connection_count(db["id"], days=7)
            
            if connections is None:
                logger.debug(f"No connection data for {db['name']}")
                return None
            
            max_connections = connections.get("max", 1)
            avg_connections = connections.get("avg", 1)
            
            # Unused if no connections in past week
            if max_connections == 0:
                current_cost = self._estimate_monthly_cost(db)
                
                return CostOpportunity(
                    database_id=db["id"],
                    database_name=db["name"],
                    opportunity_type="unused",
                    estimated_monthly_savings=current_cost,
                    confidence="high",
                    recommendation="Database appears unused - consider deletion or backup",
                    action_required="Review with owner and decommission if confirmed",
                    current_monthly_cost=current_cost,
                    potential_monthly_cost=0.0
                )
            
            # Rarely used if average < 1 connection
            elif avg_connections < 1:
                current_cost = self._estimate_monthly_cost(db)
                potential_savings = current_cost * 0.3  # Could be scheduled or downsized
                
                return CostOpportunity(
                    database_id=db["id"],
                    database_name=db["name"],
                    opportunity_type="unused",
                    estimated_monthly_savings=potential_savings,
                    confidence="medium",
                    recommendation="Database rarely used - consider scheduling or downsizing",
                    action_required="Review usage patterns and optimize",
                    current_monthly_cost=current_cost,
                    potential_monthly_cost=current_cost - potential_savings
                )
        
        except Exception as e:
            logger.warning(f"Error checking unused for {db.get('name')}: {e}")
        
        return None
    
    def _get_avg_cpu_usage(self, database_id: str, days: int = 30) -> Optional[float]:
        """Get average CPU usage percentage"""
        try:
            metrics = self.opsi.get_avg_cpu_usage(database_id, days=days)
            return metrics
        except Exception as e:
            logger.debug(f"Could not get CPU usage for {database_id}: {e}")
            return None
    
    def _get_activity_pattern(self, database_id: str, days: int = 7) -> Optional[Dict]:
        """Get activity pattern (weekend/night usage)"""
        try:
            pattern = self.opsi.get_activity_pattern(database_id, days=days)
            return pattern
        except Exception as e:
            logger.debug(f"Could not get activity pattern for {database_id}: {e}")
            return None
    
    def _get_storage_usage(self, database_id: str) -> Optional[Dict]:
        """Get storage usage information"""
        try:
            storage = self.opsi.get_storage_usage(database_id)
            return storage
        except Exception as e:
            logger.debug(f"Could not get storage usage for {database_id}: {e}")
            return None
    
    def _get_connection_count(self, database_id: str, days: int = 7) -> Optional[Dict]:
        """Get connection statistics"""
        try:
            connections = self.opsi.get_connection_count(database_id, days=days)
            return connections
        except Exception as e:
            logger.debug(f"Could not get connection count for {database_id}: {e}")
            return None
    
    def _estimate_monthly_cost(self, db: Dict) -> float:
        """Estimate monthly cost for a database"""
        try:
            # Try to get actual cost from cost client
            if self.cost:
                return self.cost.get_monthly_cost(db["id"])
        except Exception as e:
            logger.debug(f"Could not get actual cost, using estimate: {e}")
        
        # Fallback to estimation
        cpu_count = db.get("cpu_count", 1)
        storage_gb = db.get("storage_gb", 100)
        
        cpu_cost = cpu_count * self.default_cost_per_ocpu
        storage_cost = storage_gb * self.default_cost_per_gb_storage
        
        return cpu_cost + storage_cost
    
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
