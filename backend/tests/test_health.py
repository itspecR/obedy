from unittest.mock import patch

import pytest
from django.test import Client


@pytest.mark.django_db
def test_health_reports_ok_when_database_is_available():
    response = Client().get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_health_reports_unavailable_database():
    with patch("config.api.database_is_available", return_value=False):
        response = Client().get("/api/health")

    assert response.status_code == 503
    assert response.json() == {"status": "error", "database": "unavailable"}
