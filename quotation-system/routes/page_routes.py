from flask import Blueprint, render_template, redirect, send_from_directory

bp = Blueprint('pages', __name__)

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/customers')
def customers():
    return render_template('customers.html')

@bp.route('/materials')
def materials():
    return render_template('materials.html')

@bp.route('/processes')
def processes():
    return render_template('processes.html')

@bp.route('/quotations')
def quotations():
    return redirect('/quotation_new')

@bp.route('/quotation_display/<int:quotation_id>')
def quotation_display(quotation_id):
    return render_template('quotation_display.html', quotation_id=quotation_id)

@bp.route('/test_standards')
def test_standards():
    return send_from_directory('.', 'test_standards_display.html')

@bp.route('/quotation_new')
def quotation_new():
    return render_template('quotation_new.html')

@bp.route('/price_breakdown')
def price_breakdown():
    return render_template('price_breakdown.html')

@bp.route('/graphics')
def graphics():
    return render_template('graphics.html')

# API接口 - 画面管理

@bp.route('/pricing_standards')
def pricing_standards():
    return render_template('pricing_standards.html')

@bp.route('/printing_standards_admin')
def printing_standards_admin():
    return render_template('printing_standards_admin.html')

# API接口 - 材料分类管理
