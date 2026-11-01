"""Lightweight smoke checks for the API module and model metadata."""
from app.models import Base, User, Complaint, Role, Status, Priority


def test_core_models_are_registered():
    assert "users" in Base.metadata.tables
    assert "complaints" in Base.metadata.tables


def test_roles_and_statuses_are_defined():
    assert Role.student.value == "student"
    assert Role.admin.value == "admin"
    assert Status.submitted.value == "submitted"
    assert Status.resolved.value == "resolved"
    assert Priority.urgent.value == "urgent"
