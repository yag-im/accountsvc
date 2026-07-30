"""Shared pytest fixtures.

Integration-only fixtures (which require a running database and the
``.env``/``secrets.env`` files) live in ``tests/integration/conftest.py`` so
unit tests can be collected and run without those resources.
"""
