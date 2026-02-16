import pytest   # noqa: F401
from fastapi import status
from fastapi.testclient import TestClient

import fastapi_template.main as main
from fastapi_template.main import app
from fastapi_template.models.output import HealthStatus


client = TestClient(app=app)


class TestHealthCheck:
    def test_health_check_endpoint__general_case(self) -> None:
        expected_response = {"status": "ok"}

        response = client.get(url="/health-check")

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == expected_response

    def test_health_check_endpoint__invalid_output_field(self, monkeypatch) -> None:
        invalid_status_field = 123
        expected_response = {
            "error_count": 1,
            "errors": [
                {
                    "input": invalid_status_field,
                    "loc": ["status"],
                    "msg": "Input should be an instance of HealthStatus",
                    "type": "is_instance_of",
                    "url": "https://errors.pydantic.dev/2.12/v/is_instance_of"
                }
            ],
            "title": "HealthCheck"
        }

        monkeypatch.setattr(main, "health_check_params", {"status": invalid_status_field})
        response = client.get(url="/health-check")


        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.json() == expected_response

    def test_health_check_endpoint__additional_output_field(self, monkeypatch) -> None:
        additional_field = "Not existing on the output model"
        expected_response = {
            "error_count": 1,
            "errors": [
                {
                    "input": additional_field,
                    "loc": [
                        "additional_field"
                    ],
                    "msg": "Extra inputs are not permitted",
                    "type": "extra_forbidden",
                    "url": "https://errors.pydantic.dev/2.12/v/extra_forbidden"
                }
            ],
            "title": "HealthCheck"
        }

        monkeypatch.setattr(
            main,
            "health_check_params",
            {"status": HealthStatus.OK, "additional_field": additional_field}
        )
        response = client.get(url="/health-check")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.json() == expected_response
