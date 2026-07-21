from extensions import oauth



def register_oauth_clients(app):
    oauth.init_app(app)

    oauth.register(
        name='google',
        client_id=app.config.get('OAUTH_CLIENT_ID'),
        client_secret=app.config.get('OAUTH_CLIENT_SECRET'),
        server_metadata_url=app.config.get('OAUTH_DISCOVERY_URL'),
        client_kwargs={'scope': 'openid email profile'}
    )

    return oauth
