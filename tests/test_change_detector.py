from pathlib import Path

from app.change_detector import detect_api_change


def test_detect_api_change_success(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "app").mkdir()
    (repo / "app" / "api.py").write_text("print('x')\n", encoding="utf-8")

    import subprocess

    subprocess.run(["git", "init"], cwd=str(repo), check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["git", "config", "user.name", "Tester"], cwd=str(repo), check=True)
    subprocess.run(["git", "config", "user.email", "tester@example.com"], cwd=str(repo), check=True)
    subprocess.run(["git", "add", "app/api.py"], cwd=str(repo), check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=str(repo), check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    (repo / "app" / "api.py").write_text("print('updated')\n", encoding="utf-8")

    result = detect_api_change(repo, repo / "app" / "api.py")
    assert result.status == "SUCCESS"
    assert result.changed is True


def test_detect_api_change_no_change(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "app").mkdir()
    source = repo / "app" / "api.py"
    source.write_text("print('same')\n", encoding="utf-8")

    import subprocess

    subprocess.run(["git", "init"], cwd=str(repo), check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["git", "config", "user.name", "Tester"], cwd=str(repo), check=True)
    subprocess.run(["git", "config", "user.email", "tester@example.com"], cwd=str(repo), check=True)
    subprocess.run(["git", "add", "app/api.py"], cwd=str(repo), check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=str(repo), check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    result = detect_api_change(repo, source)
    assert result.status == "NO CHANGE"
    assert result.changed is False
