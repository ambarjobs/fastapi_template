from datetime import datetime, timezone
from typing import NamedTuple

import pytest  # noqa: F401
from freezegun import freeze_time
from jose import jwt
from jose.exceptions import ExpiredSignatureError
from pydantic import SecretStr

import fastapi_template.config as cfg
from fastapi_template.exceptions import InvalidTokenKeyError
from fastapi_template.logic import calc_password_hash, check_password, create_token, extract_names
from fastapi_template.models.input import UserCredentials
from fastapi_template.models.internal import NameParts


class ExtractNamesParams(NamedTuple):
    """Parameters for names_extract testing."""

    full_name: str
    result: NameParts

    @classmethod
    def get_params_names(cls):
        return ','.join(cls._fields)


class TestAuthentication:
    def test_calc_password_hash__common_case(self, test_password: SecretStr, test_salt: bytes) -> None:
        expected_hash = (
            "874666f5c73f50ea7c36513f0469a40e8992f5aafa40acfda98508909c8adf7407dd7ad0777fa7e7b106eb2e29c0a8e0"
            "23fc6017a56a29a36d6efcab0fd635f1504181d1071a6fb0b56221a6843f7c03951940aa1f4b7e59aff52754e1ccf679"
        )

        calculated_hash = calc_password_hash(password=test_password, salt=test_salt)

        assert calculated_hash[:64] == test_salt.hex()
        assert calculated_hash == expected_hash

    def test_calc_password_hash__empty_password(self, test_salt: bytes) -> None:
        empty_password = SecretStr("")

        calculated_hash = calc_password_hash(password=empty_password, salt=test_salt)

        assert calculated_hash[:64] == test_salt.hex()

    def test_check_password__common_case(self, test_password: SecretStr, test_salt: bytes) -> None:
        password_hash = calc_password_hash(password=test_password, salt=test_salt)

        assert check_password(password=test_password, password_hash=password_hash)

    def test_check_password__empty_password(self, test_salt: bytes) -> None:
        empty_password = SecretStr("")
        password_hash = calc_password_hash(password=empty_password, salt=test_salt)

        assert check_password(password=empty_password, password_hash=password_hash)

    def test_check_password__invalid_password(self, test_password: SecretStr, test_salt: bytes) -> None:
        invalid_password = SecretStr("invalid_password")
        password_hash = calc_password_hash(password=test_password, salt=test_salt)

        assert not check_password(password=invalid_password, password_hash=password_hash)

    def test_create_token__common_case(self, user_credentials: UserCredentials, token_secret_key: str) -> None:
        # spell-checker: disable
        expected_token = (
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0X3VzZXJAZmFrZS5kb21haW4"
            "ueHl6IiwiZXhwIjoxNzcyOTk5OTA2fQ.2KYlWfixvFxVjMJl20eexBlPmzpAOho8D7H6MOp2k9E")
        # spell-checker: enable

        frozen_time = datetime(
            year=2026,
            month=3,
            day=8,
            hour=18,
            minute=58,
            second=26,
            tzinfo=timezone.utc
        )
        with freeze_time(time_to_freeze=frozen_time):
            token = create_token(credentials=user_credentials, key=token_secret_key, expiration_in_hours=1.0)
            token_data = jwt.decode(token=token, key=token_secret_key, algorithms=cfg.TOKEN_ALGORITHM)

        assert token == expected_token
        assert token_data == {'exp': 1772999906, 'sub': user_credentials.email}

    def test_create_token__expired_token(self, user_credentials: UserCredentials, token_secret_key: str) -> None:
        frozen_time = datetime(
            year=2026,
            month=3,
            day=8,
            hour=18,
            minute=58,
            second=26,
            tzinfo=timezone.utc
        )
        with freeze_time(time_to_freeze=frozen_time):
            token = create_token(credentials=user_credentials, key=token_secret_key, expiration_in_hours=-1.0)

        with pytest.raises(ExpiredSignatureError):
            jwt.decode(token=token, key=token_secret_key, algorithms=cfg.TOKEN_ALGORITHM)

    def test_create_token__no_key(self, user_credentials: UserCredentials, token_secret_key: str) -> None:
        with pytest.raises(InvalidTokenKeyError):
            create_token(credentials=user_credentials, key=None, expiration_in_hours=1.0)


class TestGenericUtils:
    @pytest.mark.parametrize(
        argnames=ExtractNamesParams.get_params_names(),
        argvalues=[
            ExtractNamesParams(
                full_name="First Middle Last", result=NameParts(first="First", middle="Middle", last="Last")
            ),
            ExtractNamesParams(
                full_name="First Many Middle Names Last",
                result=NameParts(first="First", middle="Many Middle Names", last="Last")
            ),
            ExtractNamesParams(
                full_name="First Last", result=NameParts(first="First", middle="", last="Last")
            ),
            ExtractNamesParams(
                full_name="First", result=NameParts(first="First", middle="", last="")
            ),
            ExtractNamesParams(
                full_name="", result=NameParts(first="", middle="", last="")
            ),
        ]
    )
    def test_extract_names__common_cases(self, full_name, result) -> None:
        assert extract_names(full_name=full_name) == result

    @pytest.mark.parametrize(
        argnames=ExtractNamesParams.get_params_names(),
        argvalues=[
            ExtractNamesParams(
                full_name="   First Middle Last", result=NameParts(first="First", middle="Middle", last="Last")
            ),
            ExtractNamesParams(
                full_name="First      Middle Last", result=NameParts(first="First", middle="Middle", last="Last")
            ),
            ExtractNamesParams(
                full_name="First Middle      Last", result=NameParts(first="First", middle="Middle", last="Last")
            ),
            ExtractNamesParams(
                full_name="First Middle Last     ", result=NameParts(first="First", middle="Middle", last="Last")
            ),
            ExtractNamesParams(
                full_name="    First    Middle Last", result=NameParts(first="First", middle="Middle", last="Last")
            ),
            ExtractNamesParams(
                full_name="   First Middle       Last", result=NameParts(first="First", middle="Middle", last="Last")
            ),
            ExtractNamesParams(
                full_name="    First    Middle    Last  ", result=NameParts(first="First", middle="Middle", last="Last")
            ),
            ExtractNamesParams(
                full_name="\t   First  \t  Middle   \t   Last  \t  ",
                result=NameParts(first="First", middle="Middle", last="Last")
            ),
            ExtractNamesParams(
                full_name="    First  \t  Many   Middle   \t  Names   Last   ",
                result=NameParts(first="First", middle="Many Middle Names", last="Last")
            ),
        ]
    )
    def test_extract_names__with_spaces(self, full_name, result) -> None:
        assert extract_names(full_name=full_name) == result
