"""Pricing tiers and feature gating for Autho.R."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta


class PricingTier(Enum):
    """Available pricing tiers."""
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"


@dataclass
class TierLimits:
    """Limits for a pricing tier."""
    tasks_per_month: int
    workflows_per_month: int
    api_calls_per_day: int
    max_file_size_mb: int
    max_concurrent_workflows: int
    data_retention_days: int
    support_level: str
    custom_integrations: bool = False
    sso_enabled: bool = False
    audit_logs: bool = False
    dedicated_support: bool = False
    sla_guarantee: bool = False
    white_label: bool = False


@dataclass
class TierFeatures:
    """Features available in a pricing tier."""
    modules: Set[str]
    scheduling: bool = False
    webhooks: bool = False
    api_access: bool = False
    team_collaboration: bool = False
    priority_execution: bool = False
    custom_branding: bool = False


@dataclass
class PricingPlan:
    """Complete pricing plan definition."""
    tier: PricingTier
    name: str
    description: str
    monthly_price_usd: float
    annual_price_usd: float  # Per year (with discount)
    limits: TierLimits
    features: TierFeatures
    marketplace_sku: str  # For Azure/IBM marketplace
    popular: bool = False


# Define all available modules
ALL_MODULES = {
    "spreadsheet", "files", "pdf", "docs", "scraper",
    "api", "database", "desktop", "workflow", "email"
}

BASIC_MODULES = {"spreadsheet", "files", "pdf", "docs"}
STANDARD_MODULES = BASIC_MODULES | {"scraper", "api", "database"}
ADVANCED_MODULES = STANDARD_MODULES | {"workflow", "email", "desktop"}


# Pricing Plans Definition
PRICING_PLANS: Dict[PricingTier, PricingPlan] = {
    PricingTier.FREE: PricingPlan(
        tier=PricingTier.FREE,
        name="Free",
        description="Get started with basic automation",
        monthly_price_usd=0.00,
        annual_price_usd=0.00,
        marketplace_sku="author-free",
        limits=TierLimits(
            tasks_per_month=100,
            workflows_per_month=5,
            api_calls_per_day=50,
            max_file_size_mb=10,
            max_concurrent_workflows=1,
            data_retention_days=7,
            support_level="community",
        ),
        features=TierFeatures(
            modules=BASIC_MODULES,
            scheduling=False,
            webhooks=False,
            api_access=False,
        ),
    ),

    PricingTier.STARTER: PricingPlan(
        tier=PricingTier.STARTER,
        name="Starter",
        description="For individuals and small projects",
        monthly_price_usd=29.00,
        annual_price_usd=290.00,  # ~17% discount
        marketplace_sku="author-starter",
        limits=TierLimits(
            tasks_per_month=1000,
            workflows_per_month=25,
            api_calls_per_day=500,
            max_file_size_mb=50,
            max_concurrent_workflows=3,
            data_retention_days=30,
            support_level="email",
        ),
        features=TierFeatures(
            modules=STANDARD_MODULES,
            scheduling=True,
            webhooks=False,
            api_access=True,
        ),
    ),

    PricingTier.PROFESSIONAL: PricingPlan(
        tier=PricingTier.PROFESSIONAL,
        name="Professional",
        description="For growing teams and businesses",
        monthly_price_usd=79.00,
        annual_price_usd=790.00,  # ~17% discount
        marketplace_sku="author-professional",
        popular=True,
        limits=TierLimits(
            tasks_per_month=10000,
            workflows_per_month=100,
            api_calls_per_day=5000,
            max_file_size_mb=200,
            max_concurrent_workflows=10,
            data_retention_days=90,
            support_level="priority",
            audit_logs=True,
        ),
        features=TierFeatures(
            modules=ADVANCED_MODULES,
            scheduling=True,
            webhooks=True,
            api_access=True,
            team_collaboration=True,
        ),
    ),

    PricingTier.BUSINESS: PricingPlan(
        tier=PricingTier.BUSINESS,
        name="Business",
        description="For organizations with advanced needs",
        monthly_price_usd=199.00,
        annual_price_usd=1990.00,  # ~17% discount
        marketplace_sku="author-business",
        limits=TierLimits(
            tasks_per_month=50000,
            workflows_per_month=500,
            api_calls_per_day=25000,
            max_file_size_mb=500,
            max_concurrent_workflows=25,
            data_retention_days=365,
            support_level="dedicated",
            custom_integrations=True,
            sso_enabled=True,
            audit_logs=True,
        ),
        features=TierFeatures(
            modules=ALL_MODULES,
            scheduling=True,
            webhooks=True,
            api_access=True,
            team_collaboration=True,
            priority_execution=True,
        ),
    ),

    PricingTier.ENTERPRISE: PricingPlan(
        tier=PricingTier.ENTERPRISE,
        name="Enterprise",
        description="Custom solutions for large organizations",
        monthly_price_usd=499.00,  # Starting price
        annual_price_usd=4990.00,
        marketplace_sku="author-enterprise",
        limits=TierLimits(
            tasks_per_month=-1,  # Unlimited
            workflows_per_month=-1,
            api_calls_per_day=-1,
            max_file_size_mb=2000,
            max_concurrent_workflows=100,
            data_retention_days=-1,  # Unlimited
            support_level="dedicated",
            custom_integrations=True,
            sso_enabled=True,
            audit_logs=True,
            dedicated_support=True,
            sla_guarantee=True,
            white_label=True,
        ),
        features=TierFeatures(
            modules=ALL_MODULES,
            scheduling=True,
            webhooks=True,
            api_access=True,
            team_collaboration=True,
            priority_execution=True,
            custom_branding=True,
        ),
    ),
}


@dataclass
class Subscription:
    """User subscription state."""
    tier: PricingTier
    started_at: datetime
    expires_at: Optional[datetime]
    is_annual: bool
    tasks_used: int = 0
    workflows_used: int = 0
    api_calls_today: int = 0
    last_reset: datetime = field(default_factory=datetime.now)

    def get_plan(self) -> PricingPlan:
        """Get the pricing plan for this subscription."""
        return PRICING_PLANS[self.tier]

    def is_active(self) -> bool:
        """Check if subscription is active."""
        if self.tier == PricingTier.FREE:
            return True
        if self.expires_at is None:
            return True
        return datetime.now() < self.expires_at

    def can_execute_task(self) -> bool:
        """Check if user can execute another task."""
        plan = self.get_plan()
        if plan.limits.tasks_per_month == -1:
            return True
        return self.tasks_used < plan.limits.tasks_per_month

    def can_create_workflow(self) -> bool:
        """Check if user can create another workflow."""
        plan = self.get_plan()
        if plan.limits.workflows_per_month == -1:
            return True
        return self.workflows_used < plan.limits.workflows_per_month

    def can_make_api_call(self) -> bool:
        """Check if user can make another API call today."""
        plan = self.get_plan()
        if plan.limits.api_calls_per_day == -1:
            return True
        # Reset daily counter if needed
        if datetime.now().date() > self.last_reset.date():
            self.api_calls_today = 0
            self.last_reset = datetime.now()
        return self.api_calls_today < plan.limits.api_calls_per_day

    def has_module_access(self, module: str) -> bool:
        """Check if user has access to a module."""
        plan = self.get_plan()
        return module in plan.features.modules

    def has_feature(self, feature: str) -> bool:
        """Check if user has access to a feature."""
        plan = self.get_plan()
        return getattr(plan.features, feature, False)

    def increment_task(self) -> None:
        """Record a task execution."""
        self.tasks_used += 1

    def increment_workflow(self) -> None:
        """Record a workflow creation."""
        self.workflows_used += 1

    def increment_api_call(self) -> None:
        """Record an API call."""
        self.api_calls_today += 1

    def get_usage_summary(self) -> Dict:
        """Get usage summary."""
        plan = self.get_plan()
        return {
            "tier": self.tier.value,
            "plan_name": plan.name,
            "tasks": {
                "used": self.tasks_used,
                "limit": plan.limits.tasks_per_month,
                "unlimited": plan.limits.tasks_per_month == -1,
            },
            "workflows": {
                "used": self.workflows_used,
                "limit": plan.limits.workflows_per_month,
                "unlimited": plan.limits.workflows_per_month == -1,
            },
            "api_calls_today": {
                "used": self.api_calls_today,
                "limit": plan.limits.api_calls_per_day,
                "unlimited": plan.limits.api_calls_per_day == -1,
            },
            "is_active": self.is_active(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }


class PricingManager:
    """Manage pricing and subscriptions."""

    @staticmethod
    def get_all_plans() -> List[PricingPlan]:
        """Get all available pricing plans."""
        return list(PRICING_PLANS.values())

    @staticmethod
    def get_plan(tier: PricingTier) -> PricingPlan:
        """Get a specific pricing plan."""
        return PRICING_PLANS[tier]

    @staticmethod
    def get_plan_by_sku(sku: str) -> Optional[PricingPlan]:
        """Get plan by marketplace SKU."""
        for plan in PRICING_PLANS.values():
            if plan.marketplace_sku == sku:
                return plan
        return None

    @staticmethod
    def create_subscription(
        tier: PricingTier,
        is_annual: bool = False,
    ) -> Subscription:
        """Create a new subscription."""
        now = datetime.now()

        if tier == PricingTier.FREE:
            expires_at = None
        elif is_annual:
            expires_at = now + timedelta(days=365)
        else:
            expires_at = now + timedelta(days=30)

        return Subscription(
            tier=tier,
            started_at=now,
            expires_at=expires_at,
            is_annual=is_annual,
        )

    @staticmethod
    def upgrade_subscription(
        subscription: Subscription,
        new_tier: PricingTier,
        is_annual: bool = False,
    ) -> Subscription:
        """Upgrade a subscription to a higher tier."""
        return PricingManager.create_subscription(new_tier, is_annual)

    @staticmethod
    def get_pricing_table() -> List[Dict]:
        """Get pricing table for display."""
        plans = []
        for plan in PRICING_PLANS.values():
            plans.append({
                "tier": plan.tier.value,
                "name": plan.name,
                "description": plan.description,
                "monthly_price": plan.monthly_price_usd,
                "annual_price": plan.annual_price_usd,
                "annual_monthly_equivalent": round(plan.annual_price_usd / 12, 2),
                "popular": plan.popular,
                "marketplace_sku": plan.marketplace_sku,
                "limits": {
                    "tasks_per_month": plan.limits.tasks_per_month,
                    "workflows_per_month": plan.limits.workflows_per_month,
                    "api_calls_per_day": plan.limits.api_calls_per_day,
                    "max_file_size_mb": plan.limits.max_file_size_mb,
                    "data_retention_days": plan.limits.data_retention_days,
                    "support_level": plan.limits.support_level,
                    "sso_enabled": plan.limits.sso_enabled,
                    "audit_logs": plan.limits.audit_logs,
                },
                "features": {
                    "modules": list(plan.features.modules),
                    "scheduling": plan.features.scheduling,
                    "webhooks": plan.features.webhooks,
                    "api_access": plan.features.api_access,
                    "team_collaboration": plan.features.team_collaboration,
                    "priority_execution": plan.features.priority_execution,
                },
            })
        return plans


# Export for easy access
def get_pricing_table():
    """Helper to get pricing table."""
    return PricingManager.get_pricing_table()


def check_feature_access(subscription: Subscription, feature: str) -> bool:
    """Check if subscription has access to a feature."""
    return subscription.has_feature(feature)


def check_module_access(subscription: Subscription, module: str) -> bool:
    """Check if subscription has access to a module."""
    return subscription.has_module_access(module)
