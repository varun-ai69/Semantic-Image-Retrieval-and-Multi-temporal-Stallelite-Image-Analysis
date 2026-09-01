# Intent Routing Agent (`backend/api/agent`)

This module houses the query-time intent classification agent (`intent_router.py`) that analyzes incoming analyst queries and dispatches execution to specific tools.

- `intent_router.py`: Classifies input intent into `semantic_search`, `change_query`, `similarity_discovery`, or `queue_query`.
- `tools/`: Specialized lookup execution tools called by the router agent.
