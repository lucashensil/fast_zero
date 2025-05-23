from http import HTTPStatus

from freezegun import freeze_time


def test_get_token(client, user):
    response = client.post(
        '/auth/token',
        data={'username': user.email, 'password': user.clean_password},
    )
    token = response.json()

    assert response.status_code == HTTPStatus.OK
    assert 'access_token' in token
    assert 'token_type' in token


def test_get_token_incorrect_user(client, user):
    response = client.post(
        '/auth/token',
        data={'username': 'test@testi', 'password': user.clean_password},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {'detail': 'Incorrect email or password'}


def test_get_token_incorrect_password(client, user):
    response = client.post(
        '/auth/token',
        data={'username': user.email, 'password': 'incorrect'},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {'detail': 'Incorrect email or password'}


def test_token_expired_after_time(client, user):
    with freeze_time('2025-01-01 12:00:00'):
        response = client.post(
            '/auth/token',
            data={'username': user.email, 'password': user.clean_password},
        )
        assert response.status_code == HTTPStatus.OK
        token = response.json()['access_token']

        with freeze_time('2025-01-01 12:31:00'):
            response = client.put(
                f'/users/{user.id}',
                headers={'Authorization': f'Bearer {token}'},
                json={
                    'username': 'wrongwo',
                    'email': 'wrong@wrong.com',
                    'password': 'wrong123',
                },
            )
            assert response.status_code == HTTPStatus.UNAUTHORIZED
            assert response.json() == {
                'detail': 'Could not validate credentials'
            }


def test_token_inexistent_user(client):
    response = client.post(
        '/auth/token',
        data={'username': 'inexistent@user.com', 'password': 'inex123'},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {'detail': 'Incorrect email or password'}


def test_token_wrong_password(client, user):
    response = client.post(
        '/auth/token',
        data={'username': f'{user.email}', 'password': 'inex123'},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {'detail': 'Incorrect email or password'}


def test_refresh_token(client, user, token):
    response = client.post(
        '/auth/refresh_token', headers={'Authorization': f'Bearer {token}'}
    )
    data = response.json()

    assert response.status_code == HTTPStatus.OK
    assert 'access_token' in data
    assert 'token_type' in data
    assert data['token_type'] == 'bearer'


def test_token_expired_dont_refresh(client, user):
    with freeze_time('2025-01-01 12:00:00'):
        response = client.post(
            '/auth/token',
            data={'username': user.email, 'password': user.clean_password},
        )
        assert response.status_code == HTTPStatus.OK
        token = response.json()['access_token']

        with freeze_time('2025-01-01 12:31:00'):
            response = client.post(
                '/auth/refresh_token',
                headers={'Authorization': f'Bearer {token}'},
            )

            assert response.status_code == HTTPStatus.UNAUTHORIZED
            assert response.json() == {
                'detail': 'Could not validate credentials'
            }
