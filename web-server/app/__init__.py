from flask import Flask

def create_app():
    app = Flask(__name__, static_folder='static', static_url_path='')

    from .routes import distance, voice_result, state
    app.register_blueprint(distance.bp)
    app.register_blueprint(voice_result.bp)
    app.register_blueprint(state.api_bp)   # /api/state
    app.register_blueprint(state.web_bp)   # /

    return app
