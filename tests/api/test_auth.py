"""
Auth route tests
================
"""

from httpx import AsyncClient

from proxy_manager.database.models.user import User


async def test_register_success(client: AsyncClient) -> None:
    """Register success (first-run, no auth needed)."""

    resp = await client.post('/auth/register', json={'email': 'new@example.com', 'name': 'New User', 'password': 'strongPassword1!'})
    assert resp.status_code == 200

    data = resp.json()
    assert 'access_token' in data
    assert data['user']['email'] == 'new@example.com'
    assert data['user']['name'] == 'New User'


async def test_register_duplicate_email(client: AsyncClient) -> None:
    """Register duplicate email (authenticated)."""

    first = await client.post('/auth/register', json={'email': 'dup@example.com', 'name': 'A', 'password': 'password123'})
    token = first.json()['access_token']

    resp = await client.post(
        '/auth/register',
        json={'email': 'dup@example.com', 'name': 'B', 'password': 'password456'},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert resp.status_code == 400
    assert 'already registered' in resp.json()['detail']


async def test_register_requires_auth_when_users_exist(client: AsyncClient) -> None:
    """Second registration without auth is forbidden."""

    await client.post('/auth/register', json={'email': 'first@example.com', 'name': 'First', 'password': 'password123'})
    resp = await client.post('/auth/register', json={'email': 'second@example.com', 'name': 'Second', 'password': 'password456'})
    assert resp.status_code == 403


async def test_register_with_auth_creates_user(client: AsyncClient) -> None:
    """Authenticated user can register new users."""

    first = await client.post('/auth/register', json={'email': 'admin@example.com', 'name': 'Admin', 'password': 'password123'})
    token = first.json()['access_token']

    resp = await client.post(
        '/auth/register',
        json={'email': 'new@example.com', 'name': 'New User', 'password': 'password456'},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert resp.status_code == 200
    assert resp.json()['user']['email'] == 'new@example.com'


async def test_login_success(client: AsyncClient) -> None:
    """Login success."""

    await client.post('/auth/register', json={'email': 'login@example.com', 'name': 'Login', 'password': 'mypassword'})
    resp = await client.post('/auth/login', json={'email': 'login@example.com', 'password': 'mypassword'})

    assert resp.status_code == 200
    assert 'access_token' in resp.json()


async def test_login_wrong_password(client: AsyncClient) -> None:
    """Login wrong password."""

    await client.post('/auth/register', json={'email': 'u@example.com', 'name': 'U', 'password': 'correctpassword'})
    resp = await client.post('/auth/login', json={'email': 'u@example.com', 'password': 'wrongpassword'})
    assert resp.status_code == 401


async def test_login_nonexistent_user(client: AsyncClient) -> None:
    """Login nonexistent user."""

    resp = await client.post('/auth/login', json={'email': 'nobody@example.com', 'password': 'whatever'})
    assert resp.status_code == 401


async def test_me_authenticated(auth_client: AsyncClient) -> None:
    """Me authenticated."""

    resp = await auth_client.get('/auth/me')
    assert resp.status_code == 200
    assert resp.json()['email'] == 'test@example.com'


async def test_me_unauthenticated(client: AsyncClient) -> None:
    """Me unauthenticated."""

    resp = await client.get('/auth/me')
    assert resp.status_code == 401


async def test_update_name(auth_client: AsyncClient) -> None:
    """Update name."""

    resp = await auth_client.patch('/auth/profile', json={'name': 'Updated Name'})
    assert resp.status_code == 200
    assert resp.json()['name'] == 'Updated Name'


async def test_update_password(auth_client: AsyncClient) -> None:
    """Update password."""

    resp = await auth_client.patch(
        '/auth/profile',
        json={
            'current_password': 'testpassword123',
            'new_password': 'newpassword456',
        },
    )
    assert resp.status_code == 200


async def test_update_password_wrong_current(auth_client: AsyncClient) -> None:
    """Update password wrong current."""

    resp = await auth_client.patch(
        '/auth/profile',
        json={
            'current_password': 'wrongpassword',
            'new_password': 'newpassword456',
        },
    )
    assert resp.status_code == 401


async def test_setup_required_no_users(client: AsyncClient) -> None:
    """Setup required when no users exist."""

    resp = await client.get('/auth/setup-required')
    assert resp.status_code == 200
    assert resp.json()['setup_required'] is True


async def test_setup_required_with_users(auth_client: AsyncClient) -> None:
    """Setup not required when users exist."""

    resp = await auth_client.get('/auth/setup-required')
    assert resp.status_code == 200
    assert resp.json()['setup_required'] is False


async def test_list_users(auth_client: AsyncClient) -> None:
    """List users returns current user."""

    resp = await auth_client.get('/auth/users')
    assert resp.status_code == 200
    users = resp.json()
    assert len(users) >= 1
    assert any(u['email'] == 'test@example.com' for u in users)


async def test_list_users_unauthenticated(client: AsyncClient) -> None:
    """List users requires authentication."""

    resp = await client.get('/auth/users')
    assert resp.status_code == 401


async def test_delete_user(auth_client: AsyncClient) -> None:
    """Delete another user."""

    # Create a second user via authenticated registration
    reg = await auth_client.post('/auth/register', json={'email': 'remove@example.com', 'name': 'Remove Me', 'password': 'pass123456'})
    assert reg.status_code == 200
    user_id = reg.json()['user']['id']

    resp = await auth_client.delete(f'/auth/users/{user_id}')
    assert resp.status_code == 200

    # Verify the user is removed
    users = (await auth_client.get('/auth/users')).json()
    assert not any(u['id'] == user_id for u in users)


async def test_delete_self_forbidden(auth_client: AsyncClient, user: User) -> None:
    """Cannot delete own account."""

    resp = await auth_client.delete(f'/auth/users/{user.id}')
    assert resp.status_code == 400


async def test_delete_user_unauthenticated(client: AsyncClient) -> None:
    """Delete user requires authentication."""

    resp = await client.delete('/auth/users/1')
    assert resp.status_code == 401


async def test_delete_user_not_found(auth_client: AsyncClient) -> None:
    """Delete nonexistent user."""

    resp = await auth_client.delete('/auth/users/99999')
    assert resp.status_code == 404
