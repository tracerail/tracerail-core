"""
Rules-Based Routing Engine for TraceRail

This module provides a concrete implementation of the `BaseRoutingEngine`
that makes routing decisions based on a predefined set of rules loaded
from a YAML file.
"""

import logging
import yaml
from typing import Any, Dict, List, Optional

from ..base import (
    BaseRoutingEngine,
    RoutingContext,
    RoutingDecision,
    RoutingResult,
    RoutingRule,
    RoutingRuleType,
    RoutingPriority
)
from ...exceptions import ConfigurationError

logger = logging.getLogger(__name__)

class RulesBasedRoutingEngine(BaseRoutingEngine):
    """
    A routing engine that uses a list of configurable rules to make decisions.

    The engine processes rules in order of priority (CRITICAL -> HIGH -> NORMAL -> LOW).
    The first rule that matches the context determines the routing outcome.
    """

    def __init__(self, engine_name: str, rules_file: Optional[str] = None, **kwargs):
        """
        Initializes the rules-based routing engine.

        Args:
            engine_name: The name of the engine instance.
            rules_file: The file path to the YAML file containing routing rules.
            **kwargs: Additional configuration parameters.
        """
        super().__init__(engine_name, **kwargs)
        self.rules_file = rules_file
        self.rules: List[RoutingRule] = []
        self._priority_map = {
            RoutingPriority.CRITICAL: 4,
            RoutingPriority.HIGH: 3,
            RoutingPriority.NORMAL: 2,
            RoutingPriority.LOW: 1,
        }

    async def initialize(self) -> None:
        """
        Loads and validates routing rules from the configured YAML file.
        """
        if not self.rules_file:
            logger.warning("No rules file provided for RulesBasedRoutingEngine. The engine will have no rules.")
            self.is_initialized = True
            return

        logger.info(f"Initializing RulesBasedRoutingEngine from file: {self.rules_file}")
        try:
            with open(self.rules_file, "r") as f:
                raw_rules = yaml.safe_load(f)
                if not isinstance(raw_rules, list):
                    raise TypeError("Rules file must contain a list of rule objects.")

            for rule_data in raw_rules:
                # Convert enums from strings
                rule_data["rule_type"] = RoutingRuleType(rule_data["rule_type"])
                rule_data["decision"] = RoutingDecision(rule_data["decision"])
                if "priority" in rule_data:
                    rule_data["priority"] = RoutingPriority(rule_data["priority"])

                rule = RoutingRule(**rule_data)
                self.rules.append(rule)

            # Sort rules by priority (descending)
            self.rules.sort(key=lambda r: self._priority_map.get(r.priority, 0), reverse=True)
            self.is_initialized = True
            logger.info(f"Successfully loaded and sorted {len(self.rules)} routing rules.")

        except FileNotFoundError:
            raise ConfigurationError(f"Routing rules file not found: {self.rules_file}")
        except (yaml.YAMLError, TypeError, KeyError) as e:
            raise ConfigurationError(f"Error parsing routing rules file {self.rules_file}: {e}")

    async def close(self) -> None:
        """Clears the loaded rules."""
        logger.info("Closing RulesBasedRoutingEngine.")
        self.rules = []
        self.is_initialized = False

    async def route(self, context: RoutingContext) -> RoutingResult:
        """
        Evaluates the context against the loaded rules and returns a decision.

        Args:
            context: The context for the routing decision.

        Returns:
            A RoutingResult object with the outcome.
        """
        if not self.is_initialized:
            raise RoutingError("Routing engine is not initialized.")

        for rule in self.rules:
            if not rule.is_enabled:
                continue

            if self._evaluate_rule(rule, context):
                logger.info(f"Context matched rule '{rule.name}'. Routing to '{rule.decision.value}'.")
                return RoutingResult(
                    decision=rule.decision,
                    reason=f"Matched rule: {rule.name}",
                    triggered_rules=[rule.name],
                    confidence=1.0 # Rule-based confidence is typically absolute
                )

        logger.info("No routing rules matched. Falling back to default human review.")
        return RoutingResult(
            decision=RoutingDecision.HUMAN,
            reason="No applicable routing rules were matched.",
            confidence=0.0
        )

    def _evaluate_rule(self, rule: RoutingRule, context: RoutingContext) -> bool:
        """
        Dispatches to the appropriate evaluation method based on rule type.
        """
        eval_method_name = f"_evaluate_{rule.rule_type.value}"
        eval_method = getattr(self, eval_method_name, None)

        if not eval_method:
            logger.warning(f"No evaluation method found for rule type '{rule.rule_type.value}'")
            return False

        return eval_method(rule.condition, context)

    def _evaluate_confidence_threshold(self, condition: Dict, context: RoutingContext) -> bool:
        """Evaluates a confidence threshold rule."""
        if not context.llm_response or context.llm_response.metadata.get('confidence') is None:
            return False

        confidence = context.llm_response.metadata.get('confidence', 0.0)
        operator = condition.get("operator", "lt") # lt, lte, gt, gte
        threshold = condition.get("threshold", 0.0)

        if operator == "lt":
            return confidence < threshold
        if operator == "lte":
            return confidence <= threshold
        if operator == "gt":
            return confidence > threshold
        if operator == "gte":
            return confidence >= threshold

        return False

    def _evaluate_keyword_match(self, condition: Dict, context: RoutingContext) -> bool:
        """Evaluates a keyword matching rule."""
        keywords = condition.get("keywords", [])
        case_sensitive = condition.get("case_sensitive", False)
        search_content = context.content if case_sensitive else context.content.lower()

        for keyword in keywords:
            search_keyword = keyword if case_sensitive else keyword.lower()
            if search_keyword in search_content:
                return True
        return False

    def _evaluate_content_filter(self, condition: Dict, context: RoutingContext) -> bool:
        """Evaluates a content filter rule from LLM response."""
        if not context.llm_response or not context.llm_response.metadata:
            return False

        filter_metadata = context.llm_response.metadata.get('content_filter', {})
        for category, details in condition.items():
            if filter_metadata.get(category, {}).get('filtered') == details.get('filtered'):
                return True
        return False

    async def health_check(self) -> Dict[str, Any]:
        """
        Checks if the engine is initialized and the rules file is accessible.
        """
        if not self.is_initialized:
            return {"status": "unhealthy", "reason": "Engine not initialized"}

        if self.rules_file:
            try:
                with open(self.rules_file, "r"):
                    pass
            except FileNotFoundError:
                return {"status": "unhealthy", "reason": f"Rules file not found: {self.rules_file}"}

        return {"status": "healthy", "rules_loaded": len(self.rules)}
