"""
BST Utility Functions
=====================
Canonical accessors for Belief State Tracker data.

BST stores its state via setattr(agent, "_bst_store", {...}).
It does NOT use agent.set_data() / agent.get_data().
Access must go through getattr() — not agent.context.data or similar.

The belief state is nested TWO levels deep:
  agent._bst_store["__bst_belief_state__"]["domain"]

This two-level access has been written incorrectly three times (once
in each of: proactive supervisor, proactive supervisor injection hook,
and a third extension that only read the top level).

Use these functions instead of inlining the access pattern.
"""

_BST_STORE_KEY  = "_bst_store"
_BST_BELIEF_KEY = "__bst_belief_state__"


def get_bst_store(agent) -> dict:
    """Return the raw BST store dict, or {} if not yet populated."""
    return getattr(agent, _BST_STORE_KEY, {}) or {}


def get_bst_belief(agent) -> dict:
    """Return the belief state dict (primary + secondary domain, slots, etc.)."""
    return get_bst_store(agent).get(_BST_BELIEF_KEY, {}) or {}


def get_bst_domain(agent) -> str:
    """
    Return the current BST primary domain classification, or "" if not set.

    This is the canonical one-liner. Use it everywhere instead of the two-level
    getattr(agent, "_bst_store", {}).get("__bst_belief_state__", {}).get("domain", "")
    pattern — which has been written incorrectly three separate times.
    """
    return get_bst_belief(agent).get("domain", "") or ""


def get_bst_secondary_domain(agent) -> str:
    """Return the BST secondary domain, or "" if not set."""
    return get_bst_belief(agent).get("secondary_domain", "") or ""


def get_bst_momentum(agent) -> int:
    """Return the BST domain momentum counter, or 0 if not set."""
    return get_bst_belief(agent).get("momentum", 0) or 0


def get_bst_slots(agent) -> dict:
    """Return the BST slot resolution dict, or {} if not set."""
    return get_bst_belief(agent).get("slots", {}) or {}
