"""Stripe integration utilities.
Provides helper functions to configure and manage the Stripe client."""

from __future__ import annotations

import os
from typing import Optional

import stripe


def init_stripe(api_key: Optional[str] = None) -> None:
    """Configure the global Stripe client.

    Parameters
    ----------
    api_key: Optional[str]
        Stripe secret key. If not provided, the ``STRIPE_API_KEY`` environment
        variable is used.
    """
    key = api_key or os.getenv("STRIPE_API_KEY")
    if not key:
        raise ValueError("Stripe API key not provided")
    stripe.api_key = key


def create_customer(email: str, **kwargs):
    """Create a Stripe customer."""
    return stripe.Customer.create(email=email, **kwargs)


def create_subscription(customer_id: str, price_id: str, **kwargs):
    """Create a subscription for a customer."""
    return stripe.Subscription.create(
        customer=customer_id,
        items=[{"price": price_id}],
        **kwargs,
    )


def cancel_subscription(subscription_id: str):
    """Cancel a subscription."""
    return stripe.Subscription.delete(subscription_id)


def list_subscriptions(customer_id: str):
    """List subscriptions for a customer."""
    return stripe.Subscription.list(customer=customer_id)
