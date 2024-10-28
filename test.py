
import time
import pytest
import requests

def test_register_user():
    response = requests.post(
        "http://127.0.0.1:8000/register",
        json={
            "email": "test@gmail.com",
            "username": "test",
            "password": "12345"
        }
    )
    assert response.status_code == 201

def test_login_user():
    global headers
    response = requests.post(
        "http://127.0.0.1:8000/login",
        json={
            "username": "test",
            "password": "12345"
        }
    )
    assert response.status_code == 200

    headers = {
        "Authorization": f"Bearer {response.json()['access_token']}"
    }
    
    assert len(response.json().get('access_token', False))

def test_create_post():
    global headers
    response = requests.post(
        "http://127.0.0.1:8000/posts",
        headers=headers,
        json={
            "title": "Test",
            "content": "Some data text",
        },
    )
    assert response.status_code == 201

def test_get_posts():
    response = requests.get(
        "http://127.0.0.1:8000/posts",
    )
    assert response.status_code == 200
    assert len(response.json()) > 0

def test_get_post():
    response = requests.get(
        "http://127.0.0.1:8000/posts/1",
    )
    assert response.status_code == 200
    assert response.json() != {}

def test_update_post():
    global headers
    response = requests.put(
        "http://127.0.0.1:8000/posts/1",
        headers=headers,
        json={
            "title": "Updated",
            "content": "Some text here"
        },
    )
    assert response.status_code == 200

def test_create_good_comment():
    response = requests.post(
        "http://127.0.0.1:8000/posts/1/comments",
        headers=headers,
        json={
            "content": "Some text here"
        },
    )
    assert response.status_code == 201

def test_create_bad_comment():
    response = requests.post(
        "http://127.0.0.1:8000/posts/1/comments",
        headers=headers,
        json={
            "content": "You're son of a bitch"
        },
    )
    assert response.status_code == 201

def test_get_comments():
    response = requests.get(
        "http://127.0.0.1:8000/posts/1/comments",
    )
    assert response.status_code == 200
    assert len(response.json()) > 0

def test_update_comment():
    response = requests.put(
        "http://127.0.0.1:8000/posts/1/comments/1",
        headers=headers,
        json={
            "content": "You're an ass"
        },
    )
    assert response.status_code == 403
    assert response.json() != {}

def test_daily_breakdown():
    response = requests.get(
        "http://127.0.0.1:8000/api/comments-daily-breakdown?date_from=2023-10-23&date_to=2025-10-29",
    )
    assert response.status_code == 200
    assert response.json()[0]["created_count"] == 1
    assert response.json()[0]["blocked_count"] == 1

def test_delete_comment():
    response = requests.delete(
        "http://127.0.0.1:8000/posts/1/comments/1",
        headers=headers
    )
    assert response.status_code == 200

def test_delete_second_comment():
    response = requests.delete(
        "http://127.0.0.1:8000/posts/1/comments/2",
        headers=headers
    )
    assert response.status_code == 200

def test_delete_post():
    response = requests.delete(
        "http://127.0.0.1:8000/posts/1",
        headers=headers
    )
    assert response.status_code == 200

def test_login_user():
    global headers
    response = requests.post(
        "http://127.0.0.1:8000/login",
        json={
            "username": "test",
            "password": "12345"
        }
    )
    assert response.status_code == 200

    headers = {
        "Authorization": f"Bearer {response.json()['access_token']}"
    }
    
    assert len(response.json().get('access_token', False))

def test_create_post():
    global headers
    response = requests.post(
        "http://127.0.0.1:8000/posts",
        headers=headers,
        json={
            "title": "Test",
            "content": "Some data text",
        },
    )
    assert response.status_code == 201

def test_auto_reply():
    response = requests.post(
        "http://127.0.0.1:8000/posts",
        headers=headers,
        json={
            "title": "Test",
            "content": "Do you know what is compiler?",
            "auto_reply_enabled": True,
            "auto_reply_delay": 0.5
        },
    )
    assert response.status_code == 201

    response = requests.post(
        "http://127.0.0.1:8000/posts/1/comments",
        headers=headers,
        json={
            "content": "Honestly, I don't know"
        },
    )
    assert response.status_code == 201

    response = requests.get(
        "http://127.0.0.1:8000/api/posts/comments",
    )

    assert response.status_code == 200

    results = len(response.json()[0]["1"])
    
    time.sleep(0.5 * 60 + 1)

    response = requests.get(
        "http://127.0.0.1:8000/api/posts/comments",
    )

    assert response.status_code == 200
    assert len(response.json()[0]["1"]) > results
