from main import app
from api import api

def test_status_200():
    app.blueprint(api)
    _, response = app.test_client.get('/api/status')
    assert response.status == 200