from datetime import datetime, timedelta

import pytest
from fastapi.security import OAuth2PasswordRequestForm
from freezegun import freeze_time
from pydantic import SecretStr, ValidationError

import fastapi_template.config as cfg
from fastapi_template import TokenStatus
from fastapi_template.adapters import handle_token, oauth2form_to_credentials
from fastapi_template.logic import create_token
from fastapi_template.models.input import UserCredentials


class TestAdapters:
    def test_oauth2form_to_credentials__common_case(
        self,
        oauth2_form: OAuth2PasswordRequestForm,
        user_email: str,
        user_password: SecretStr
    ) -> None:
        credentials = oauth2form_to_credentials(form_data=oauth2_form)

        assert credentials.email == user_email
        assert credentials.password == user_password

    @pytest.mark.parametrize(
        argnames="test_user_email,test_user_password",
        argvalues=[
            ("", "some_password"),
            ("invalid_email", "some_password"),
            ("user.email@template.xyz", ""),
            (None, "some_password"),
            ("user.email@template.xyz", None),
            (123, "some_password"),
            ("user.email@template.xyz", 123),
            ("", ""),
            (None, None),
            (123, 456),
        ],
        ids=[
            "empty-email",
            "invalid-email",
            "empty-password",
            "nul-email",
            "nul-password",
            "wrong-type-email",
            "wrong-type-password",
            "both-empty",
            "both-null",
            "both-wrong-type",
        ],
    )
    def test_oauth2form_to_credentials__invalid_credentials(
        self,
        test_user_email: str,
        test_user_password: str
    ) -> None:
        oauth2_form = OAuth2PasswordRequestForm(username=test_user_email, password=test_user_password)
        with pytest.raises((ValidationError, TypeError)):
            oauth2form_to_credentials(form_data=oauth2_form)

    def test_handle_token__common_case(self, user_credentials: UserCredentials) -> None:
        token = create_token(credentials=user_credentials)
        token_info = handle_token(token=token)

        assert token_info.status == TokenStatus.OK
        assert token_info.description == "Valid token."
        assert token_info.payload.get("sub") == user_credentials.email

        expiration_timestamp = token_info.payload.get("exp")
        assert isinstance(expiration_timestamp, int)

    def test_handle_token__expired_token(self, user_credentials: UserCredentials, frozen_time: datetime) -> None:
        with freeze_time(time_to_freeze=frozen_time):
            token = create_token(credentials=user_credentials)

        expired_time = frozen_time + timedelta(hours=1.1 * cfg.TOKEN_EXPIRATION_IN_HOURS)
        with freeze_time(time_to_freeze=expired_time):
            token_info = handle_token(token=token)

        assert token_info.status == TokenStatus.EXPIRED
        assert token_info.description.startswith("Expired token: ")
        assert token_info.payload == {}

    @pytest.mark.parametrize(
        argnames="token",
        argvalues=[
            "invalid_token",
            "",
            "invalid_token.invalid_token.invalid_token",
            123,
            None,
        ],
        ids=["short-token", "empty-token", "invalid-token", "wrong-type-token", "null-token"]
    )
    def test_handle_token__invalid_token(self, token: str) -> None:
        token_info = handle_token(token=token)

        assert token_info.status == TokenStatus.INVALID
        assert token_info.description.startswith("Invalid token: ")
        assert token_info.payload == {}
