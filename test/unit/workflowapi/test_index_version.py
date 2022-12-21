def test_index(test_client):
    print('GET /')
    response = test_client.http.get('/')
    assert response.body == b'{"hello":"world"}'

def test_version(test_client):
    print('GET /version')
    response = test_client.http.get('/version')
    assert response.body == b'{"ApiVersion":"3.0.0","FrameworkVersion":"v9.9.9"}'