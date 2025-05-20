from http import HTTPStatus

from fast_zero.schemas import UserPublic


def test_get_token(client, user):
    response = client.post(
        '/token',
        data={'username': user.email, 'password': user.clean_password},
    )
    token = response.json()

    assert response.status_code == HTTPStatus.OK
    assert 'access_token' in token
    assert 'token_type' in token


def test_get_token_incorrect_user(client, user):
    response = client.post(
        '/token',
        data={'username': 'test@testi', 'password': user.clean_password},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {'detail': 'Incorrect email or password'}


def test_get_token_incorrect_password(client, user):
    response = client.post(
        '/token',
        data={'username': user.email, 'password': 'incorrect'},
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {'detail': 'Incorrect email or password'}


def test_root_retorna_certo(client):
    response = client.get('/')
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'message': 'Olá mundo!'}


def test_create_user(client):
    response = client.post(
        '/users/',
        json={
            'username': 'lucas',
            'email': 'lucas@exemplo.com',
            'password': 'secret',
        },
    )
    assert response.status_code == HTTPStatus.CREATED
    assert response.json() == {
        'username': 'lucas',
        'email': 'lucas@exemplo.com',
        'id': 1,
    }


def test_create_user_username_alredy_exists(client, user):
    response = client.post(
        '/users/',
        json={
            'username': 'Teste',
            'email': 'teste0@email.com',
            'password': 'secret',
        },
    )

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json() == {'detail': 'Username already exists'}


def test_create_user_email_alredy_exists(client, user):
    response = client.post(
        '/users/',
        json={
            'username': 'teste0',
            'email': 'teste@email.com',
            'password': 'secret',
        },
    )

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json() == {'detail': 'Email already exists'}


def test_read_users(client):
    response = client.get('/users/')

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'users': []}


def test_read_users_with_users(client, user):
    user_schema = UserPublic.model_validate(user).model_dump()
    response = client.get('/users/')

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'users': [user_schema]}


def test_get_one_user(client, user):
    user_schema = UserPublic.model_validate(user).model_dump()
    response = client.get('/users/1')

    assert response.status_code == HTTPStatus.OK
    assert response.json() == user_schema


def test_get_one_user_exception(client):
    response = client.get('/users/999')

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'User Not Found'}


def test_update_user(client, user, token):
    response = client.put(
        f'/users/{user.id}',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'username': 'henrique',
            'email': 'henrique@exemplo.com',
            'password': 'secret',
        },
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        'username': 'henrique',
        'email': 'henrique@exemplo.com',
        'id': user.id,
    }


def test_update_user_exception(client, token):
    response = client.put(
        '/users/999',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'username': 'henrique',
            'email': 'henrique@exemplo.com',
            'password': 'secret',
        },
    )

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json() == {'detail': 'Not enough permissions'}


def test_update_integraty_error(client, user, token):
    client.post(
        '/users',
        json={
            'username': 'henrique',
            'email': 'henrique@exemplo.com',
            'password': 'secret',
        },
    )

    response_update = client.put(
        f'/users/{user.id}',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'username': 'henrique',
            'email': 'silva@exemplo.com',
            'password': 'newsecret',
        },
    )

    assert response_update.status_code == HTTPStatus.CONFLICT
    assert response_update.json() == {
        'detail': 'Username or Email already exists'
    }


def test_delete_user(client, user, token):
    response = client.delete(
        f'/users/{user.id}',
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'message': 'User deleted'}


def test_delete_user_exception(client, token):
    response = client.delete(
        '/users/999',
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response.json() == {'detail': 'Not enough permissions'}
