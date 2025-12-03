"""Skills loader for MCP OCI OPSI server.

This module provides skill discovery, loading, and serving capabilities.
Skills are dynamic instruction sets that teach Claude how to perform
specific DBA tasks with minimal token usage and maximum accuracy.

Skills can be used in two ways:
1. By clients that support the Anthropic Skills specification (skills API)
2. As prompts/context for clients that don't support skills directly

Reference: https://github.com/anthropics/skills
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml


class Skill:
    """Represents a single skill with its metadata and content."""

    def __init__(self, skill_dir: Path):
        """
        Initialize skill from a directory containing SKILL.md.

        Args:
            skill_dir: Path to the skill directory
        """
        self.skill_dir = skill_dir
        self.skill_file = skill_dir / "SKILL.md"
        self.name: str = ""
        self.description: str = ""
        self.allowed_tools: List[str] = []
        self.metadata: Dict[str, str] = {}
        self.content: str = ""
        self.raw_content: str = ""
        self._loaded = False

    def load(self) -> bool:
        """
        Load and parse the SKILL.md file.

        Returns:
            bool: True if loaded successfully, False otherwise
        """
        if not self.skill_file.exists():
            return False

        try:
            with open(self.skill_file, "r", encoding="utf-8") as f:
                self.raw_content = f.read()

            # Parse YAML frontmatter
            frontmatter_match = re.match(
                r"^---\s*\n(.*?)\n---\s*\n(.*)$",
                self.raw_content,
                re.DOTALL
            )

            if frontmatter_match:
                yaml_content = frontmatter_match.group(1)
                self.content = frontmatter_match.group(2).strip()

                # Parse YAML
                frontmatter = yaml.safe_load(yaml_content)
                if frontmatter:
                    self.name = frontmatter.get("name", self.skill_dir.name)
                    self.description = frontmatter.get("description", "")
                    self.allowed_tools = frontmatter.get("allowed-tools", [])
                    self.metadata = frontmatter.get("metadata", {})
            else:
                # No frontmatter, treat entire file as content
                self.content = self.raw_content
                self.name = self.skill_dir.name

            self._loaded = True
            return True

        except Exception as e:
            print(f"Error loading skill {self.skill_dir.name}: {e}")
            return False

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert skill to dictionary format for API responses.

        Returns:
            Dict containing skill metadata and content
        """
        return {
            "name": self.name,
            "description": self.description,
            "allowed_tools": self.allowed_tools,
            "metadata": self.metadata,
            "content": self.content,
        }

    def to_prompt_context(self) -> str:
        """
        Convert skill to prompt context for non-skill-aware clients.

        Returns:
            str: Formatted prompt context string
        """
        return f"""## Skill: {self.name}

{self.description}

### Instructions
{self.content}

### Recommended Tools
{', '.join(self.allowed_tools) if self.allowed_tools else 'Any applicable tools'}
"""

    @property
    def is_loaded(self) -> bool:
        """Check if skill is loaded."""
        return self._loaded


class SkillsLoader:
    """Loads and manages skills from the skills directory."""

    def __init__(self, skills_dir: Optional[str] = None):
        """
        Initialize the skills loader.

        Args:
            skills_dir: Path to skills directory. If not provided, uses
                       default location relative to this module.
        """
        if skills_dir:
            self.skills_dir = Path(skills_dir)
        else:
            # Default to ../skills relative to this module
            module_dir = Path(__file__).parent
            self.skills_dir = module_dir.parent / "skills"

        self.skills: Dict[str, Skill] = {}
        self._loaded = False

    def discover_skills(self) -> List[str]:
        """
        Discover available skills in the skills directory.

        Returns:
            List of skill names
        """
        skill_names = []

        if not self.skills_dir.exists():
            return skill_names

        for item in self.skills_dir.iterdir():
            if item.is_dir():
                skill_file = item / "SKILL.md"
                if skill_file.exists():
                    skill_names.append(item.name)

        return skill_names

    def load_all_skills(self) -> Dict[str, Skill]:
        """
        Load all discovered skills.

        Returns:
            Dict mapping skill names to Skill objects
        """
        skill_names = self.discover_skills()

        for name in skill_names:
            skill_dir = self.skills_dir / name
            skill = Skill(skill_dir)
            if skill.load():
                self.skills[skill.name] = skill

        self._loaded = True
        return self.skills

    def get_skill(self, name: str) -> Optional[Skill]:
        """
        Get a specific skill by name.

        Args:
            name: Skill name

        Returns:
            Skill object or None if not found
        """
        if not self._loaded:
            self.load_all_skills()
        return self.skills.get(name)

    def list_skills(self) -> List[Dict[str, Any]]:
        """
        List all available skills with metadata.

        Returns:
            List of skill info dictionaries
        """
        if not self._loaded:
            self.load_all_skills()

        return [
            {
                "name": skill.name,
                "description": skill.description,
                "tools_count": len(skill.allowed_tools),
            }
            for skill in self.skills.values()
        ]

    def get_skill_for_query(self, query: str) -> Optional[Skill]:
        """
        Find the most relevant skill for a user query.

        This method analyzes the query to determine which skill
        would be most helpful for answering it.

        Args:
            query: User's natural language query

        Returns:
            Most relevant Skill or None
        """
        if not self._loaded:
            self.load_all_skills()

        query_lower = query.lower()

        # Skill matching patterns
        skill_patterns = {
            "fleet-overview": [
                "how many database", "fleet", "inventory", "count",
                "databases in", "database list", "all databases",
            ],
            "sql-performance": [
                "slow query", "slow queries", "sql performance", "top sql", "sql tuning",
                "query performance", "sql degrading", "execution plan", "sql statistic",
                "consuming cpu", "consuming memory", "top cpu", "sql analysis",
            ],
            "capacity-planning": [
                "forecast", "capacity", "run out", "storage full",
                "cpu usage", "memory usage", "trend", "predict",
            ],
            "database-diagnostics": [
                "addm", "diagnos", "performance problem", "slow database",
                "what's wrong", "bottleneck", "alert", "error",
            ],
            "awr-analysis": [
                "awr", "snapshot", "wait event", "system stat",
                "parameter change", "workload",
            ],
            "host-monitoring": [
                "host", "server", "cpu", "memory", "disk", "network",
                "process", "top process",
            ],
            "storage-management": [
                "tablespace", "storage", "data file", "space",
                "disk full", "extend",
            ],
            "security-audit": [
                "user", "privilege", "role", "security", "permission",
                "audit", "access", "proxy",
            ],
            "sql-watch-management": [
                "sql watch", "enable monitor", "disable monitor",
                "sql collection",
            ],
            "sql-plan-baselines": [
                "plan baseline", "spm", "plan management", "plan stability",
                "plan regression",
            ],
            "multi-tenancy": [
                "profile", "tenancy", "switch", "account", "credential",
            ],
            "exadata-monitoring": [
                "exadata", "rack", "cell", "storage server", "compute server",
            ],
        }

        # Score each skill
        scores: Dict[str, int] = {}
        for skill_name, patterns in skill_patterns.items():
            score = sum(1 for pattern in patterns if pattern in query_lower)
            if score > 0:
                scores[skill_name] = score

        if not scores:
            return None

        # Return skill with highest score
        best_skill_name = max(scores, key=scores.get)
        return self.skills.get(best_skill_name)

    def get_combined_context(self, skill_names: Optional[List[str]] = None) -> str:
        """
        Get combined context from multiple skills for prompt injection.

        Args:
            skill_names: List of skill names to include. If None, includes all.

        Returns:
            Combined context string
        """
        if not self._loaded:
            self.load_all_skills()

        skills_to_include = []
        if skill_names:
            for name in skill_names:
                skill = self.skills.get(name)
                if skill:
                    skills_to_include.append(skill)
        else:
            skills_to_include = list(self.skills.values())

        if not skills_to_include:
            return ""

        context_parts = [
            "# DBA Skills Context",
            "",
            "The following skills provide guidance for common DBA tasks:",
            "",
        ]

        for skill in skills_to_include:
            context_parts.append(skill.to_prompt_context())
            context_parts.append("")

        return "\n".join(context_parts)


# Global loader instance
_skills_loader: Optional[SkillsLoader] = None


def get_skills_loader() -> SkillsLoader:
    """
    Get the global skills loader instance.

    Returns:
        SkillsLoader instance
    """
    global _skills_loader
    if _skills_loader is None:
        _skills_loader = SkillsLoader()
        _skills_loader.load_all_skills()
    return _skills_loader


def get_skill_context_for_query(query: str) -> str:
    """
    Get relevant skill context for a user query.

    This function finds the most relevant skill for the query
    and returns its context for prompt injection.

    Args:
        query: User's natural language query

    Returns:
        Skill context string or empty string if no match
    """
    loader = get_skills_loader()
    skill = loader.get_skill_for_query(query)

    if skill:
        return skill.to_prompt_context()
    return ""
