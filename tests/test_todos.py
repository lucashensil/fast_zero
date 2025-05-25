from http import HTTPStatus

import pytest
from sqlalchemy import select

from fast_zero.models import Todo, TodoState


def test_create_todo(client, token, mock_db_time):
    with mock_db_time(model=Todo) as time:
        response = client.post(
            '/todos/',
            headers={'Authorization': f'Bearer {token}'},
            json={
                'title': 'Test Todo',
                'description': 'Test todo description',
                'state': 'draft',
            },
        )
    assert response.json() == {
        'title': 'Test Todo',
        'description': 'Test todo description',
        'state': 'draft',
        'id': 1,
        'created_at': time.isoformat(),
        'updated_at': time.isoformat(),
    }


@pytest.mark.asyncio
async def test_create_todo_error(session, user, todo):
    todo = todo.create(user_id=user.id, state='wrong')
    session.add(todo)
    await session.commit()

    with pytest.raises(LookupError):
        await session.scalar(select(Todo))


# ruff: noqa: PLR0913, PLR0917
@pytest.mark.asyncio
async def test_get_todo(client, token, mock_db_time, todo, user, session):
    with mock_db_time(model=Todo) as time:
        todo = todo.create(user_id=user.id)
        session.add(todo)
        await session.commit()

    await session.refresh(todo)
    response = client.get(
        '/todos/', headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json()['todos'] == [
        {
            'created_at': time.isoformat(),
            'updated_at': time.isoformat(),
            'title': todo.title,
            'description': todo.description,
            'state': todo.state,
            'id': todo.id,
        }
    ]


@pytest.mark.asyncio
async def test_list_todos_should_return_5_todos(
    session, client, user, token, todo
):
    expected_todos = 5
    session.add_all(todo.create_batch(5, user_id=user.id))
    await session.commit()

    response = client.get(
        '/todos/',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert len(response.json()['todos']) == expected_todos


@pytest.mark.asyncio
async def test_list_todos_pagination(session, client, user, token, todo):
    expected_todos = 2
    session.add_all(todo.create_batch(5, user_id=user.id))
    await session.commit()

    response = client.get(
        '/todos/?offset=1&limit=2',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert len(response.json()['todos']) == expected_todos


@pytest.mark.asyncio
async def test_list_todos_filter_title(session, client, user, token, todo):
    expected_todos = 5
    session.add_all(todo.create_batch(5, user_id=user.id, title='Test Title'))
    await session.commit()

    response = client.get(
        '/todos/?title=Test Title',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert len(response.json()['todos']) == expected_todos


@pytest.mark.asyncio
async def test_list_todos_filter_description(
    session, client, user, token, todo
):
    expected_todos = 5
    session.add_all(
        todo.create_batch(5, user_id=user.id, description='description')
    )
    await session.commit()

    response = client.get(
        '/todos/?description=description',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert len(response.json()['todos']) == expected_todos


@pytest.mark.asyncio
async def test_list_todos_filter_state(session, client, user, token, todo):
    expected_todos = 5
    session.add_all(
        todo.create_batch(5, user_id=user.id, state=TodoState.draft)
    )
    await session.commit()

    response = client.get(
        '/todos/?state=draft',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert len(response.json()['todos']) == expected_todos


@pytest.mark.asyncio
async def test_list_todos_filter_combination(
    session, client, user, token, todo
):
    expected_todos = 5
    session.add_all(
        todo.create_batch(
            5,
            user_id=user.id,
            title='Test todo combined',
            description='combined',
            state=TodoState.done,
        )
    )

    session.add_all(
        todo.create_batch(
            3,
            user_id=user.id,
            title='other title',
            description='other description',
            state=TodoState.todo,
        )
    )

    await session.commit()

    response = client.get(
        '/todos/?title=Test todo combined&?description=combined&?state=done',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert len(response.json()['todos']) == expected_todos


@pytest.mark.asyncio
async def test_patch_todo(session, client, user, token, todo):
    todo = todo.create(user_id=user.id)
    session.add(todo)
    await session.commit()
    response = client.patch(
        f'/todos/{todo.id}',
        json={'title': 'Test!!!'},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json()['title'] == 'Test!!!'


def test_patch_todo_error(client, token):
    response = client.patch(
        '/todos/999', json={}, headers={'Authorization': f'Bearer {token}'}
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'Task not found'}


@pytest.mark.asyncio
async def test_delete_todo(client, session, token, todo, user):
    todo = todo.create(user_id=user.id)
    session.add(todo)
    await session.commit()

    response = client.delete(
        f'/todos/{todo.id}', headers={'Authorization': f'Bearer {token}'}
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'message': 'Task has been deleted successfuly'}


def test_delete_todo_error(client, token):
    response = client.delete(
        '/todos/999', headers={'Authorization': f'Bearer {token}'}
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'Task not found'}
