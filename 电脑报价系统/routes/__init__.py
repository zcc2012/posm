from .page_routes import bp as page_bp
from .customer_routes import bp as customer_bp
from .material_routes import bp as material_bp
from .process_routes import bp as process_bp
from .pricing_standard_routes import bp as pricing_standard_bp
from .quotation_routes import bp as quotation_bp
from .graphics_routes import bp as graphics_bp


def register_routes(app):
    app.register_blueprint(page_bp)
    app.register_blueprint(customer_bp)
    app.register_blueprint(material_bp)
    app.register_blueprint(process_bp)
    app.register_blueprint(pricing_standard_bp)
    app.register_blueprint(quotation_bp)
    app.register_blueprint(graphics_bp)
