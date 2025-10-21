"""
Centralized SQL query management system.
Loads queries from external JSON configuration for maintainability.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class QueryManager:
    """Manages SQL queries loaded from external JSON configuration."""

    def __init__(self, queries_config_path: str):
        """
        Initialize QueryManager with path to queries configuration.
        
        Args:
            queries_config_path: Path to queries.json file
        """
        self.queries_config_path = Path(queries_config_path)
        self.queries: Dict[str, Dict[str, str]] = {}
        self.cache: Dict[str, str] = {}
        
        self._load_queries()

    def _load_queries(self) -> None:
        """Load queries from JSON configuration file."""
        try:
            if not self.queries_config_path.exists():
                logger.warning(
                    f"Queries config file not found: {self.queries_config_path}. "
                    "QueryManager will operate without queries."
                )
                self.queries = {}
                return
            
            with open(self.queries_config_path, 'r', encoding='utf-8') as f:
                self.queries = json.load(f)
            
            logger.info(
                f"Loaded {sum(len(v) for v in self.queries.values())} queries "
                f"from {self.queries_config_path}"
            )
            
        except json.JSONDecodeError as exc:
            logger.error(f"Invalid JSON in queries config: {exc}")
            self.queries = {}
        except Exception as exc:
            logger.error(f"Error loading queries config: {exc}", exc_info=True)
            self.queries = {}

    def get_query(self, category: str, query_name: str) -> str:
        """
        Get a SQL query by category and name.
        
        Args:
            category: Query category (e.g., 'data_feeds', 'users')
            query_name: Name of the query within the category
            
        Returns:
            SQL query string
            
        Raises:
            ValueError: If query not found
        """
        cache_key = f"{category}.{query_name}"
        
        # Check cache first
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Retrieve from loaded queries
        if category not in self.queries:
            raise ValueError(f"Query category not found: {category}")
        
        if query_name not in self.queries[category]:
            raise ValueError(
                f"Query not found: {category}.{query_name}. "
                f"Available queries in {category}: {list(self.queries[category].keys())}"
            )
        
        query = self.queries[category][query_name]
        
        # Cache for future use
        self.cache[cache_key] = query
        
        return query

    def get_query_safe(
        self,
        category: str,
        query_name: str,
        default: Optional[str] = None
    ) -> Optional[str]:
        """
        Get a query without raising an exception if not found.
        
        Args:
            category: Query category
            query_name: Query name
            default: Default value if query not found
            
        Returns:
            SQL query string or default value
        """
        try:
            return self.get_query(category, query_name)
        except ValueError:
            logger.warning(f"Query not found: {category}.{query_name}, using default")
            return default

    def reload(self) -> None:
        """Reload queries from configuration file and clear cache."""
        self.cache.clear()
        self._load_queries()
        logger.info("Queries reloaded from configuration")

    def list_categories(self) -> list[str]:
        """Get list of available query categories."""
        return list(self.queries.keys())

    def list_queries(self, category: str) -> list[str]:
        """
        Get list of query names in a category.
        
        Args:
            category: Query category
            
        Returns:
            List of query names
        """
        return list(self.queries.get(category, {}).keys())

    def get_all_queries(self, category: str) -> Dict[str, str]:
        """
        Get all queries in a category.
        
        Args:
            category: Query category
            
        Returns:
            Dictionary of query_name: query_sql
        """
        return self.queries.get(category, {}).copy()

    def query_exists(self, category: str, query_name: str) -> bool:
        """
        Check if a query exists.
        
        Args:
            category: Query category
            query_name: Query name
            
        Returns:
            True if query exists, False otherwise
        """
        return (
            category in self.queries and
            query_name in self.queries[category]
        )

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about loaded queries.
        
        Returns:
            Dictionary with statistics
        """
        return {
            "categories": len(self.queries),
            "total_queries": sum(len(v) for v in self.queries.values()),
            "cache_size": len(self.cache),
            "config_path": str(self.queries_config_path),
            "categories_list": self.list_categories(),
        }

