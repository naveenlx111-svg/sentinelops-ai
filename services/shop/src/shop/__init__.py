"""Demo shop: four small HTTP services that SentinelOps monitors.

One Python package, four processes. Each service is started separately with
``uvicorn shop.<service>.app:create_app --factory`` and configured only
through environment variables.
"""
