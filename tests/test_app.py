"""Smoke tests for the Streamlit page, run offline with Streamlit's AppTest."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def run_app():
    app = AppTest.from_file(APP, default_timeout=30)
    app.run()
    assert not app.exception
    return app


def test_app_answers_a_request_offline():
    app = run_app()
    app.toggle[0].set_value(True).run()  # offline mode, so no API call
    request_box = [box for box in app.text_input if box.label == "Your request"][0]
    request_box.input("music for the gym")
    app.button[0].click().run()

    assert not app.exception
    shown = " ".join(block.value for block in app.text)
    assert "Storm Runner" in shown or "Gym Hero" in shown


def test_app_rejects_empty_request():
    app = run_app()
    app.toggle[0].set_value(True).run()
    app.button[0].click().run()
    assert any("describe what you want" in w.value for w in app.warning)
