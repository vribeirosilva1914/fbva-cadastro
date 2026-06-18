import os
from flask import Flask, send_from_directory
from extensions import db, login_manager

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
SECRET_KEY_FILE = os.path.join(BASE_DIR, 'secret.key')
UPLOAD_DIR = os.path.join(BASE_DIR, 'instance', 'uploads')


def _get_secret_key():
    env_key = os.environ.get('SECRET_KEY')
    if env_key:
        return env_key
    if os.path.exists(SECRET_KEY_FILE):
        with open(SECRET_KEY_FILE, 'r') as f:
            return f.read().strip()
    key = os.urandom(32).hex()
    with open(SECRET_KEY_FILE, 'w') as f:
        f.write(key)
    return key


def _get_db_uri():
    url = os.environ.get('DATABASE_URL')
    if url:
        if url.startswith('postgres://'):
            url = url.replace('postgres://', 'postgresql://', 1)
        return url
    db_path = os.path.join(BASE_DIR, 'instance', 'fbva.db')
    return f'sqlite:///{db_path}'


def create_app():
    app = Flask(__name__, static_folder=None)

    app.config['SECRET_KEY']                  = _get_secret_key()
    app.config['SQLALCHEMY_DATABASE_URI']     = _get_db_uri()
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['WTF_CSRF_ENABLED']            = False
    app.config['SESSION_COOKIE_SAMESITE']     = 'Lax'
    app.config['SESSION_COOKIE_SECURE']       = os.environ.get('HTTPS', '0') == '1'
    app.config['PERMANENT_SESSION_LIFETIME']  = 86400 * 30
    app.config['UPLOAD_FOLDER']               = UPLOAD_DIR
    app.config['MAX_CONTENT_LENGTH']          = 16 * 1024 * 1024  # 16 MB

    os.makedirs(os.path.join(BASE_DIR, 'instance'), exist_ok=True)
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    db.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = None

    @login_manager.unauthorized_handler
    def unauthorized():
        from flask import jsonify
        return jsonify({'ok': False, 'error': 'Não autenticado.'}), 401

    from routes.api import api_bp
    app.register_blueprint(api_bp)

    @app.route('/')
    def index():
        return send_from_directory(BASE_DIR, 'index.html')

    @app.route('/logo.png')
    def logo():
        return send_from_directory(BASE_DIR, 'logo.png')

    with app.app_context():
        db.create_all()
        _migrate_db()
        _seed_admin()

    return app


def _migrate_db():
    """Add new columns to existing tables without dropping data."""
    from sqlalchemy import text, inspect
    try:
        with db.engine.connect() as conn:
            inspector = inspect(db.engine)
            if 'clubes' not in inspector.get_table_names():
                return
            existing = {c['name'] for c in inspector.get_columns('clubes')}
            new_cols = [
                ('data_nascimento_presidente', 'DATE'),
                ('data_fundacao', 'DATE'),
                ('site', 'VARCHAR(150)'),
                ('youtube', 'VARCHAR(150)'),
                ('tiktok', 'VARCHAR(150)'),
            ]
            for col_name, col_type in new_cols:
                if col_name not in existing:
                    conn.execute(text(f'ALTER TABLE clubes ADD COLUMN {col_name} {col_type}'))
            conn.commit()
    except Exception:
        pass


def _seed_admin():
    from models import Usuario
    from werkzeug.security import generate_password_hash
    senha_inicial = os.environ.get('ADMIN_PASSWORD', 'Admin@2024')
    email_admin   = os.environ.get('ADMIN_EMAIL',    'admin@fbva.org.br')
    if not Usuario.query.filter_by(email=email_admin).first():
        admin = Usuario(
            nome='Administrador',
            email=email_admin,
            senha_hash=generate_password_hash(senha_inicial),
            perfil='admin',
            ativo=True,
        )
        db.session.add(admin)
        db.session.commit()


if __name__ == '__main__':
    debug = os.environ.get('FLASK_DEBUG', '0') == '1'
    application = create_app()
    application.run(debug=debug, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
