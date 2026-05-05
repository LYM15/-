from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date

db = SQLAlchemy()


class Record(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(10), nullable=False)
    category = db.Column(db.String(20), nullable=False)
    note = db.Column(db.String(200), nullable=True)
    date = db.Column(db.Date, nullable=False)

    def __repr__(self):
        return f'<Record {self.id}: {self.type} {self.amount}>'


class Config(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f'<Config {self.key}: {self.value}>'


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, nullable=False)
    icon = db.Column(db.String(50), default='📦')
    color = db.Column(db.String(20), default='#3b82f6')
    is_default = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<Category {self.name}>'


class CategoryBudget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(20), nullable=False)
    budget_amount = db.Column(db.Float, nullable=False)
    month = db.Column(db.String(7), nullable=False)

    def __repr__(self):
        return f'<CategoryBudget {self.category}: {self.budget_amount}>'


class Reminder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20), nullable=False)
    day_of_month = db.Column(db.Integer, nullable=True)
    weekday = db.Column(db.Integer, nullable=True)
    category = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    note = db.Column(db.String(200), nullable=True)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<Reminder {self.type} {self.category}>'


class KeywordCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.String(50), unique=True, nullable=False)
    category = db.Column(db.String(20), nullable=False)

    def __repr__(self):
        return f'<KeywordCategory {self.keyword}: {self.category}>'


class Template(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    type = db.Column(db.String(10), nullable=False)
    category = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Float, nullable=True)
    note = db.Column(db.String(200), nullable=True)

    def __repr__(self):
        return f'<Template {self.name}>'


class Challenge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    target_category = db.Column(db.String(20), nullable=False)
    target_amount = db.Column(db.Float, nullable=False)
    month = db.Column(db.String(7), nullable=False)
    status = db.Column(db.String(20), default='active')
    completed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Challenge {self.target_category}: {self.target_amount}>'


def init_default_categories():
    default_categories = [
        {'name': '餐饮', 'icon': '🍜', 'color': '#ef4444', 'sort_order': 1},
        {'name': '购物', 'icon': '🛒', 'color': '#f97316', 'sort_order': 2},
        {'name': '交通', 'icon': '🚗', 'color': '#eab308', 'sort_order': 3},
        {'name': '娱乐', 'icon': '🎮', 'color': '#22c55e', 'sort_order': 4},
        {'name': '工资', 'icon': '💰', 'color': '#3b82f6', 'sort_order': 5},
        {'name': '其他', 'icon': '📦', 'color': '#8b5cf6', 'sort_order': 6},
    ]

    for cat_data in default_categories:
        existing = Category.query.filter_by(name=cat_data['name']).first()
        if not existing:
            category = Category(
                name=cat_data['name'],
                icon=cat_data['icon'],
                color=cat_data['color'],
                is_default=True,
                sort_order=cat_data['sort_order']
            )
            db.session.add(category)

    db.session.commit()


def get_categories():
    categories = Category.query.order_by(Category.sort_order).all()
    if not categories:
        init_default_categories()
        categories = Category.query.order_by(Category.sort_order).all()
    return [(c.name, c.icon, c.color) for c in categories]


def init_budget():
    config = Config.query.filter_by(key='monthly_budget').first()
    if not config:
        config = Config(key='monthly_budget', value='5000.0')
        db.session.add(config)
        db.session.commit()


def get_budget():
    config = Config.query.filter_by(key='monthly_budget').first()
    return float(config.value) if config else 5000.0


def set_budget(value):
    config = Config.query.filter_by(key='monthly_budget').first()
    if config:
        config.value = str(value)
    else:
        config = Config(key='monthly_budget', value=str(value))
        db.session.add(config)
    db.session.commit()
