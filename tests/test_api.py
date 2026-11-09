import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database.db import get_all_videos, get_video_by_id

client = TestClient(app)

def test_api_videos_list():
    response = client.get("/api/videos")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "videos" in data
    assert len(data["videos"]) >= 5

def test_api_video_detail_siri1():
    response = client.get("/api/videos/sg2LSuC8ATQ")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    v = data["video"]
    assert v["video_id"] == "sg2LSuC8ATQ"
    assert v["series_no"] == 1
    assert "summary" in v
    assert len(v["summary"]["short"]) > 50
    assert len(v["summary"]["detailed"]) > 100
    assert len(v["summary"]["key_takeaways"]) >= 3
    assert len(v["topics"]) >= 5
    assert len(v["religious_references"]) >= 1
    assert len(v["faq"]) >= 2
    assert len(v["terminology"]) >= 2

def test_api_video_detail_siri2():
    response = client.get("/api/videos/n5Jx3LcYnHs")
    assert response.status_code == 200
    v = response.json()["video"]
    assert v["series_no"] == 2
    # Check that hadith reference has Arabic text
    refs = v["religious_references"]
    assert len(refs) >= 1
    assert any("الْبَحْرِ" in (r.get("text_ar") or "") or "البحر" in (r.get("text_ar") or "") for r in refs)

def test_api_search():
    response = client.get("/api/search?q=air")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert len(data["results"]) >= 1

def test_api_stats():
    response = client.get("/api/stats")
    assert response.status_code == 200
    stats = response.json()
    assert stats["total_videos"] >= 5
    assert stats["total_duration_hours"] > 0
    assert stats["total_hadith_references"] >= 5

def test_api_export_markdown():
    response = client.get("/api/videos/sg2LSuC8ATQ/export/markdown")
    assert response.status_code == 200
    text = response.text
    assert "# " in text
    assert "Ringkasan Pantas" in text
    assert "Dalil & Rujukan Agama" in text

def test_frontend_routes():
    res_index = client.get("/")
    assert res_index.status_code == 200
    assert "FahamCeramah" in res_index.text

    res_ceramah = client.get("/ceramah")
    assert res_ceramah.status_code == 200
    assert "FahamCeramah" in res_ceramah.text
