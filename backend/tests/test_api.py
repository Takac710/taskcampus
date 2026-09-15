from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    res = client.get("/health")
    assert res.status_code == 200


def test_course_and_task_crud():
    res = client.post("/courses", json={"name": "テスト科目", "color": "#ff0000"})
    assert res.status_code == 201
    course = res.json()

    res = client.post(
        "/tasks",
        json={"title": "第1回レポート", "course_id": course["id"], "type": "report", "memo": ""},
    )
    assert res.status_code == 201
    task = res.json()
    assert task["status"] == "open"

    res = client.get("/tasks")
    assert res.status_code == 200
    assert any(t["id"] == task["id"] for t in res.json())

    res = client.patch(f"/tasks/{task['id']}", json={"status": "done"})
    assert res.status_code == 200
    assert res.json()["status"] == "done"

    res = client.get("/tasks/views/deadline-buckets")
    assert res.status_code == 200
    assert set(res.json().keys()) == {"overdue", "today", "this_week", "later", "no_due_date"}


def test_paste_registration_flow():
    res = client.post("/courses", json={"name": "統計学", "color": "#00ff00"})
    assert res.status_code == 201

    res = client.post("/extract", json={"raw_text": "統計学の課題を来週の金曜日までに提出してください"})
    assert res.status_code == 200
    body = res.json()
    fields = body["fields"]
    assert fields["course_name_guess"] == "統計学"
    assert fields["type"] == "report"

    res = client.post(
        "/extract/confirm",
        json={"extraction_log_id": body["extraction_log_id"], "fields": fields},
    )
    assert res.status_code == 201
    task = res.json()
    assert task["source"] == "paste"
    assert task["title"] == fields["title"]
