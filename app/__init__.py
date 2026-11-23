import os
from flask import Flask, render_template, jsonify
from flask_cors import CORS
from .config import config_by_name
from .models import db

def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'default')

    app = Flask(__name__, 
                static_folder='static',
                template_folder='templates')
    
    app.config.from_object(config_by_name[config_name])

    # Enable Cross-Origin Resource Sharing for separate frontend-backend deployments
    CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

    # Initialize extensions
    db.init_app(app)

    # Register API Blueprints
    from .routes.auth_routes import auth_bp
    from .routes.destination_routes import destination_bp
    from .routes.recommendation_routes import recommendation_bp
    from .routes.flight_routes import flight_bp
    from .routes.hotel_routes import hotel_bp
    from .routes.travel_doc_routes import travel_doc_bp
    from .routes.itinerary_routes import itinerary_bp
    from .routes.admin_routes import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(destination_bp)
    app.register_blueprint(recommendation_bp)
    app.register_blueprint(flight_bp)
    app.register_blueprint(hotel_bp)
    app.register_blueprint(travel_doc_bp)
    app.register_blueprint(itinerary_bp)
    app.register_blueprint(admin_bp)

    # Root route serves the single page React application
    @app.route('/')
    @app.route('/explore')
    @app.route('/planner')
    @app.route('/compare')
    @app.route('/hotels')
    @app.route('/docs')
    @app.route('/itineraries')
    @app.route('/admin')
    def index():
        return render_template('index.html')

    # API health check
    @app.route('/api/health')
    def health():
        return jsonify({
            'status': 'healthy',
            'app': 'JBD Travels AI Planning & Management System',
            'version': '2.0.0'
        })

    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'error': 'Resource not found'}), 404

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({'error': 'Internal server error'}), 500

    return app
