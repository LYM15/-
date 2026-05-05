from flask import Flask, render_template, request, redirect, url_for, flash, make_response, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, timedelta
import csv
import io
import json

from models import (
    db, Record, Config, Category, CategoryBudget, Reminder,
    KeywordCategory, Template, Challenge,
    init_default_categories, get_categories, init_budget, get_budget, set_budget
)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///accounting.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'accounting_secret_key_2024'

db.init_app(app)

LARGE_EXPENSE_THRESHOLD = 500
DUPLICATE_CHECK_MINUTES = 5


def get_month_stats(for_date=None):
    if for_date is None:
        for_date = date.today()
    first_day_of_month = date(for_date.year, for_date.month, 1)
    month_records = Record.query.filter(Record.date >= first_day_of_month).all()

    total_income = sum(r.amount for r in month_records if r.type == 'income')
    total_expense = sum(r.amount for r in month_records if r.type == 'expense')
    balance = total_income - total_expense
    budget = get_budget()
    budget_percentage = (total_expense / budget * 100) if budget > 0 else 0

    return {
        'total_income': total_income,
        'total_expense': total_expense,
        'balance': balance,
        'budget': budget,
        'budget_percentage': budget_percentage
    }


def get_category_budgets(month=None):
    if month is None:
        month = date.today().strftime('%Y-%m')
    budgets = CategoryBudget.query.filter_by(month=month).all()
    return {b.category: b.budget_amount for b in budgets}


def get_category_spending(category, month=None):
    if month is None:
        month = date.today().strftime('%Y-%m')
    first_day = datetime.strptime(month + '-01', '%Y-%m-%d').date()
    if month == date.today().strftime('%Y-%m'):
        last_day = date.today()
    else:
        if int(month.split('-')[1]) == 12:
            last_day = date(int(month.split('-')[0]) + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = date(int(month.split('-')[0]), int(month.split('-')[1]) + 1, 1) - timedelta(days=1)

    records = Record.query.filter(
        Record.date >= first_day,
        Record.date <= last_day,
        Record.category == category,
        Record.type == 'expense'
    ).all()
    return sum(r.amount for r in records)


def get_quick_templates():
    thirty_days_ago = date.today() - timedelta(days=30)
    records = Record.query.filter(Record.date >= thirty_days_ago).all()

    template_count = {}
    for r in records:
        key = (r.type, r.category, r.note or '')
        template_count[key] = template_count.get(key, 0) + 1

    sorted_templates = sorted(template_count.items(), key=lambda x: x[1], reverse=True)[:3]
    return [{'type': t[0], 'category': t[1], 'note': t[2], 'count': c} for t, c in sorted_templates]


def get_today_reminders():
    today = date.today()
    reminders = []

    monthly_reminders = Reminder.query.filter_by(type='monthly', is_active=True).all()
    for r in monthly_reminders:
        if today.day == r.day_of_month:
            reminders.append(r)

    weekly_reminders = Reminder.query.filter_by(type='weekly', is_active=True).all()
    for r in weekly_reminders:
        if today.weekday() == r.weekday:
            reminders.append(r)

    return reminders


def check_duplicate(amount, category, note):
    five_minutes_ago = datetime.now() - timedelta(minutes=DUPLICATE_CHECK_MINUTES)
    recent_records = Record.query.filter(
        Record.amount == amount,
        Record.category == category,
        Record.date == date.today()
    ).all()

    for r in recent_records:
        if r.note == note:
            return True
    return False


def get_recommended_category(note):
    if not note:
        return None
    keywords = KeywordCategory.query.all()
    note_lower = note.lower()
    for kw in keywords:
        if kw.keyword.lower() in note_lower:
            return kw.category
    return None


def learn_keyword(note, category):
    if not note:
        return
    words = note.strip().split()
    if words:
        keyword = words[0][:10]
        existing = KeywordCategory.query.filter_by(keyword=keyword).first()
        if not existing:
            new_kw = KeywordCategory(keyword=keyword, category=category)
            db.session.add(new_kw)
            db.session.commit()


def get_week_range(weeks_ago=0):
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday() + weeks_ago * 7)
    end_of_week = start_of_week + timedelta(days=6)
    return start_of_week, end_of_week


def get_week_spending(weeks_ago=0):
    start, end = get_week_range(weeks_ago)
    records = Record.query.filter(
        Record.date >= start,
        Record.date <= end,
        Record.type == 'expense'
    ).all()
    return sum(r.amount for r in records)


def get_common_combinations():
    today = date.today()
    thirty_days_ago = today - timedelta(days=30)

    records = Record.query.filter(Record.date >= thirty_days_ago).order_by(Record.date).all()

    day_records = {}
    for r in records:
        if r.date not in day_records:
            day_records[r.date] = []
        day_records[r.date].append(r.category)

    combination_count = {}
    for day, cats in day_records.items():
        cats_set = tuple(sorted(set(cats)))
        if len(cats_set) >= 2:
            combination_count[cats_set] = combination_count.get(cats_set, 0) + 1

    if combination_count:
        most_common = max(combination_count.items(), key=lambda x: x[1])
        if most_common[1] >= 2:
            return list(most_common[0])
    return None


@app.route('/')
def index():
    today = date.today().isoformat()
    stats = get_month_stats()
    quick_templates = get_quick_templates()
    user_templates = Template.query.all()
    reminders = get_today_reminders()
    categories = get_categories()
    challenges = Challenge.query.filter_by(status='active').all()

    cat_budgets = get_category_budgets()
    cat_spending = {}
    for cat_name, _, _ in categories:
        if cat_name in cat_budgets:
            cat_spending[cat_name] = get_category_spending(cat_name)

    return render_template('index.html', today=today, categories=categories,
                           stats=stats, quick_templates=quick_templates,
                           user_templates=user_templates, reminders=reminders,
                           challenges=challenges, cat_budgets=cat_budgets,
                           cat_spending=cat_spending)


@app.route('/add_record', methods=['POST'])
def add_record():
    amount = float(request.form['amount'])
    record_type = request.form['type']
    category = request.form['category']
    note = request.form.get('note', '')
    record_date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()

    if record_type == 'expense' and amount > LARGE_EXPENSE_THRESHOLD:
        return render_template('confirm_large_expense.html',
                               amount=amount, type=record_type, category=category,
                               note=note, date=record_date.strftime('%Y-%m-%d'))

    if check_duplicate(amount, category, note):
        return render_template('confirm_duplicate.html',
                               amount=amount, type=record_type, category=category,
                               note=note, date=record_date.strftime('%Y-%m-%d'))

    learn_keyword(note, category)

    record = Record(
        amount=amount,
        type=record_type,
        category=category,
        note=note,
        date=record_date
    )
    db.session.add(record)
    db.session.commit()
    flash('记账成功！', 'success')
    return redirect(url_for('records'))


@app.route('/confirm_record', methods=['POST'])
def confirm_record():
    amount = float(request.form['amount'])
    record_type = request.form['type']
    category = request.form['category']
    note = request.form.get('note', '')
    record_date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()

    learn_keyword(note, category)

    record = Record(
        amount=amount,
        type=record_type,
        category=category,
        note=note,
        date=record_date
    )
    db.session.add(record)
    db.session.commit()
    flash('记账成功！', 'success')
    return redirect(url_for('records'))


@app.route('/confirm_large_expense', methods=['POST'])
def confirm_large_expense():
    amount = float(request.form['amount'])
    record_type = request.form['type']
    category = request.form['category']
    note = request.form.get('note', '')
    record_date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()

    learn_keyword(note, category)

    record = Record(
        amount=amount,
        type=record_type,
        category=category,
        note=note,
        date=record_date
    )
    db.session.add(record)
    db.session.commit()
    flash('大额支出已添加！', 'success')
    return redirect(url_for('records'))


@app.route('/cancel_record', methods=['GET'])
def cancel_record():
    flash('已取消添加', 'info')
    return redirect(url_for('index'))


@app.route('/get_recommendation')
def get_recommendation():
    note = request.args.get('note', '')
    category = get_recommended_category(note)
    return jsonify({'category': category})


@app.route('/records')
def records():
    filter_type = request.args.get('filter', 'all')
    date_range = request.args.get('range', 'all')
    search = request.args.get('search', '').strip()
    min_amount = request.args.get('min', type=float)
    max_amount = request.args.get('max', type=float)
    specific_date = request.args.get('date', '')

    query = Record.query

    if filter_type == 'expense':
        query = query.filter_by(type='expense')
    elif filter_type == 'income':
        query = query.filter_by(type='income')

    today = date.today()

    if specific_date:
        query = query.filter(Record.date == datetime.strptime(specific_date, '%Y-%m-%d').date())
    else:
        if date_range == 'today':
            query = query.filter(Record.date == today)
        elif date_range == 'week':
            start_of_week = today - timedelta(days=today.weekday())
            query = query.filter(Record.date >= start_of_week)
        elif date_range == 'month':
            first_day = date(today.year, today.month, 1)
            query = query.filter(Record.date >= first_day)
        elif date_range == 'last_month':
            if today.month == 1:
                first_day = date(today.year - 1, 12, 1)
            else:
                first_day = date(today.year, today.month - 1, 1)
            if today.month == 1:
                last_day = date(today.year - 1, 12, 31)
            else:
                last_day = date(today.year, today.month - 1, 28)
            query = query.filter(Record.date >= first_day, Record.date <= last_day)

    if search:
        query = query.filter(Record.note.ilike(f'%{search}%'))

    if min_amount is not None:
        query = query.filter(Record.amount >= min_amount)

    if max_amount is not None:
        query = query.filter(Record.amount <= max_amount)

    records_list = query.order_by(Record.date.desc(), Record.id.desc()).all()
    stats = get_month_stats()

    return render_template('records.html', records=records_list, filter_type=filter_type,
                           date_range=date_range, search=search, min_amount=min_amount,
                           max_amount=max_amount, stats=stats, specific_date=specific_date)


@app.route('/delete_record/<int:id>', methods=['POST'])
def delete_record(id):
    record = Record.query.get_or_404(id)
    db.session.delete(record)
    db.session.commit()
    flash('记录已删除', 'success')
    return redirect(url_for('records'))


@app.route('/edit_record/<int:id>')
def edit_record(id):
    record = Record.query.get_or_404(id)
    categories = get_categories()
    return render_template('edit_record.html', record=record, categories=categories)


@app.route('/update_record/<int:id>', methods=['POST'])
def update_record(id):
    record = Record.query.get_or_404(id)
    record.amount = float(request.form['amount'])
    record.type = request.form['type']
    record.category = request.form['category']
    record.note = request.form.get('note', '')
    record.date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()

    db.session.commit()
    flash('记录已更新', 'success')
    return redirect(url_for('records'))


@app.route('/stats')
def stats():
    today = date.today()
    first_day_of_month = date(today.year, today.month, 1)

    month_records = Record.query.filter(Record.date >= first_day_of_month).all()

    total_income = sum(r.amount for r in month_records if r.type == 'income')
    total_expense = sum(r.amount for r in month_records if r.type == 'expense')
    balance = total_income - total_expense
    budget = get_budget()

    category_expense = {}
    for r in month_records:
        if r.type == 'expense':
            category_expense[r.category] = category_expense.get(r.category, 0) + r.amount

    week_days = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    week_expense = {day: 0 for day in week_days}

    start_of_week = today - timedelta(days=today.weekday())
    for i in range(7):
        day = start_of_week + timedelta(days=i)
        day_str = week_days[i]
        week_records = Record.query.filter(
            Record.date == day,
            Record.type == 'expense'
        ).all()
        week_expense[day_str] = sum(r.amount for r in week_records)

    last_month = date(today.year - 1 if today.month == 1 else today.year,
                      12 if today.month == 1 else today.month - 1, 1)
    last_month_records = Record.query.filter(
        Record.date >= last_month,
        Record.date < first_day_of_month
    ).all()
    last_month_expense = sum(r.amount for r in last_month_records if r.type == 'expense')

    expense_change = 0
    if last_month_expense > 0:
        expense_change = ((total_expense - last_month_expense) / last_month_expense) * 100

    main_increase_cat = None
    if expense_change > 0:
        last_month_cat = {}
        for r in last_month_records:
            if r.type == 'expense':
                last_month_cat[r.category] = last_month_cat.get(r.category, 0) + r.amount

        for cat, amount in category_expense.items():
            last_amount = last_month_cat.get(cat, 0)
            if amount > last_amount and (amount - last_amount) > 50:
                main_increase_cat = cat
                break

    week_spending_this = get_week_spending(0)
    week_spending_last = get_week_spending(1)
    week_avg_this = week_spending_this / 7 if today.weekday() + 1 > 0 else week_spending_this
    week_avg_last = week_spending_last / 7

    warning = None
    if week_avg_last > 0 and (week_avg_this - week_avg_last) / week_avg_last > 0.3:
        warning = "⚠️ 最近一周消费明显增加"

    week_spending_4w = [get_week_spending(i) for i in range(4)]
    min_week = min(week_spending_4w)
    max_week = max(week_spending_4w)
    min_week_idx = week_spending_4w.index(min_week) + 1
    max_week_idx = week_spending_4w.index(max_week) + 1

    common_combo = get_common_combinations()

    cat_budgets = get_category_budgets()
    cat_spending = {}
    for cat in category_expense.keys():
        cat_spending[cat] = get_category_spending(cat)

    challenges = Challenge.query.filter_by(status='active').all()

    return render_template(
        'stats.html',
        total_income=total_income,
        total_expense=total_expense,
        balance=balance,
        budget=budget,
        category_expense=category_expense,
        week_expense=week_expense,
        week_days=week_days,
        last_month_expense=last_month_expense,
        expense_change=expense_change,
        main_increase_cat=main_increase_cat,
        warning=warning,
        week_spending_this=week_spending_this,
        min_week=min_week,
        max_week=max_week,
        min_week_idx=min_week_idx,
        max_week_idx=max_week_idx,
        common_combo=common_combo,
        cat_budgets=cat_budgets,
        cat_spending=cat_spending,
        challenges=challenges
    )


@app.route('/set_budget', methods=['POST'])
def set_budget_route():
    new_budget = float(request.form['budget'])
    set_budget(new_budget)
    flash('预算已更新', 'success')
    return redirect(url_for('stats'))


@app.route('/export_csv')
def export_csv():
    records = Record.query.order_by(Record.date.desc(), Record.id.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', '日期', '类型', '分类', '金额', '备注'])

    for r in records:
        writer.writerow([
            r.id,
            r.date.strftime('%Y-%m-%d'),
            '支出' if r.type == 'expense' else '收入',
            r.category,
            r.amount,
            r.note or ''
        ])

    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = f'attachment; filename=ledger_export_{date.today().strftime("%Y%m%d")}.csv'

    return response


@app.route('/calendar')
def calendar():
    month = request.args.get('month', date.today().strftime('%Y-%m'))
    year, mon = map(int, month.split('-'))

    first_day = date(year, mon, 1)
    if mon == 12:
        last_day = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = date(year, mon + 1, 1) - timedelta(days=1)

    start_weekday = first_day.weekday()

    records = Record.query.filter(
        Record.date >= first_day,
        Record.date <= last_day
    ).all()

    day_data = {}
    for r in records:
        day_key = r.date.day
        if day_key not in day_data:
            day_data[day_key] = {'expense': 0, 'income': 0}
        if r.type == 'expense':
            day_data[day_key]['expense'] += r.amount
        else:
            day_data[day_key]['income'] += r.amount

    if mon == 1:
        prev_month = f'{year - 1}-12'
    else:
        prev_month = f'{year}-{mon - 1:02d}'

    if mon == 12:
        next_month = f'{year + 1}-01'
    else:
        next_month = f'{year}-{mon + 1:02d}'

    return render_template('calendar.html', first_day=first_day, last_day=last_day,
                           start_weekday=start_weekday, day_data=day_data,
                           prev_month=prev_month, next_month=next_month, month=month)


@app.route('/manage_budgets', methods=['GET', 'POST'])
def manage_budgets():
    if request.method == 'POST':
        category = request.form['category']
        budget_amount = float(request.form['budget_amount'])
        month = request.form['month']

        existing = CategoryBudget.query.filter_by(category=category, month=month).first()
        if existing:
            existing.budget_amount = budget_amount
        else:
            new_budget = CategoryBudget(category=category, budget_amount=budget_amount, month=month)
            db.session.add(new_budget)
        db.session.commit()
        flash('分类预算已保存', 'success')
        return redirect(url_for('manage_budgets'))

    month = request.args.get('month', date.today().strftime('%Y-%m'))
    budgets = CategoryBudget.query.filter_by(month=month).all()
    categories = get_categories()
    budget_dict = {b.category: b.budget_amount for b in budgets}

    cat_spending = {}
    for cat_name, _, _ in categories:
        cat_spending[cat_name] = get_category_spending(cat_name, month)

    return render_template('manage_budgets.html', categories=categories,
                           budget_dict=budget_dict, cat_spending=cat_spending, month=month)


@app.route('/reminders', methods=['GET', 'POST'])
def reminders():
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'add':
            reminder_type = request.form['type']
            day_of_month = request.form.get('day_of_month', type=int)
            weekday = request.form.get('weekday', type=int)
            category = request.form['category']
            amount = float(request.form['amount'])
            note = request.form.get('note', '')
            is_active = request.form.get('is_active') == 'on'

            reminder = Reminder(
                type=reminder_type,
                day_of_month=day_of_month if reminder_type == 'monthly' else None,
                weekday=weekday if reminder_type == 'weekly' else None,
                category=category,
                amount=amount,
                note=note,
                is_active=is_active
            )
            db.session.add(reminder)
            db.session.commit()
            flash('提醒已添加', 'success')

        elif action == 'delete':
            reminder_id = request.form.get('reminder_id', type=int)
            reminder = Reminder.query.get_or_404(reminder_id)
            db.session.delete(reminder)
            db.session.commit()
            flash('提醒已删除', 'success')

        elif action == 'toggle':
            reminder_id = request.form.get('reminder_id', type=int)
            reminder = Reminder.query.get_or_404(reminder_id)
            reminder.is_active = not reminder.is_active
            db.session.commit()
            flash('提醒状态已更新', 'success')

        return redirect(url_for('reminders'))

    all_reminders = Reminder.query.all()
    categories = get_categories()
    return render_template('reminders.html', reminders=all_reminders, categories=categories)


@app.route('/templates', methods=['GET', 'POST'])
def templates_page():
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'add':
            name = request.form['name']
            template_type = request.form['type']
            category = request.form['category']
            amount = request.form.get('amount', type=float)
            note = request.form.get('note', '')

            template = Template(
                name=name,
                type=template_type,
                category=category,
                amount=amount if amount and amount > 0 else None,
                note=note
            )
            db.session.add(template)
            db.session.commit()
            flash('模板已添加', 'success')

        elif action == 'delete':
            template_id = request.form.get('template_id', type=int)
            template = Template.query.get_or_404(template_id)
            db.session.delete(template)
            db.session.commit()
            flash('模板已删除', 'success')

        return redirect(url_for('templates_page'))

    all_templates = Template.query.all()
    categories = get_categories()
    return render_template('templates.html', templates=all_templates, categories=categories)


@app.route('/challenges', methods=['GET', 'POST'])
def challenges():
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'add':
            target_category = request.form['category']
            target_amount = float(request.form['target_amount'])
            month = request.form['month']

            challenge = Challenge(
                target_category=target_category,
                target_amount=target_amount,
                month=month,
                status='active'
            )
            db.session.add(challenge)
            db.session.commit()
            flash('挑战已创建', 'success')

        elif action == 'complete':
            challenge_id = request.form.get('challenge_id', type=int)
            challenge = Challenge.query.get_or_404(challenge_id)
            challenge.status = 'completed'
            challenge.completed_at = datetime.utcnow()
            db.session.commit()
            flash('🎉 挑战完成！', 'success')

        elif action == 'cancel':
            challenge_id = request.form.get('challenge_id', type=int)
            challenge = Challenge.query.get_or_404(challenge_id)
            challenge.status = 'cancelled'
            db.session.commit()
            flash('挑战已取消', 'info')

        return redirect(url_for('challenges'))

    all_challenges = Challenge.query.order_by(Challenge.created_at.desc()).all()
    categories = get_categories()
    current_month = date.today().strftime('%Y-%m')

    challenge_progress = {}
    for c in all_challenges:
        if c.status == 'active':
            spending = get_category_spending(c.target_category, c.month)
            progress = (spending / c.target_amount * 100) if c.target_amount > 0 else 0
            challenge_progress[c.id] = {'spent': spending, 'progress': min(progress, 100)}

    return render_template('challenges.html', challenges=all_challenges, categories=categories,
                           current_month=current_month, challenge_progress=challenge_progress)


@app.route('/categories', methods=['GET', 'POST'])
def categories_page():
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'add':
            name = request.form['name']
            icon = request.form.get('icon', '📦')
            color = request.form.get('color', '#3b82f6')
            sort_order = request.form.get('sort_order', 0, type=int)

            existing = Category.query.filter_by(name=name).first()
            if existing:
                flash('分类已存在', 'error')
            else:
                category = Category(
                    name=name,
                    icon=icon,
                    color=color,
                    is_default=False,
                    sort_order=sort_order
                )
                db.session.add(category)
                db.session.commit()
                flash('分类已添加', 'success')

        elif action == 'update':
            cat_id = request.form.get('cat_id', type=int)
            category = Category.query.get_or_404(cat_id)
            category.name = request.form['name']
            category.icon = request.form.get('icon', '📦')
            category.color = request.form.get('color', '#3b82f6')
            category.sort_order = request.form.get('sort_order', 0, type=int)
            db.session.commit()
            flash('分类已更新', 'success')

        elif action == 'delete':
            cat_id = request.form.get('cat_id', type=int)
            category = Category.query.get_or_404(cat_id)
            if category.is_default:
                flash('默认分类不能删除', 'error')
            else:
                db.session.delete(category)
                db.session.commit()
                flash('分类已删除', 'success')

        return redirect(url_for('categories_page'))

    all_categories = Category.query.order_by(Category.sort_order).all()
    return render_template('categories.html', categories=all_categories)


@app.route('/manage_keywords', methods=['GET', 'POST'])
def manage_keywords():
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'add':
            keyword = request.form['keyword']
            category = request.form['category']

            existing = KeywordCategory.query.filter_by(keyword=keyword).first()
            if existing:
                existing.category = category
            else:
                new_kw = KeywordCategory(keyword=keyword, category=category)
                db.session.add(new_kw)
            db.session.commit()
            flash('关键词已保存', 'success')

        elif action == 'delete':
            kw_id = request.form.get('kw_id', type=int)
            keyword = KeywordCategory.query.get_or_404(kw_id)
            db.session.delete(keyword)
            db.session.commit()
            flash('关键词已删除', 'success')

        return redirect(url_for('manage_keywords'))

    all_keywords = KeywordCategory.query.all()
    categories = get_categories()
    return render_template('manage_keywords.html', keywords=all_keywords, categories=categories)


@app.route('/backup')
def backup():
    data = {
        'records': [],
        'configs': [],
        'category_budgets': [],
        'reminders': [],
        'templates': [],
        'challenges': [],
        'keywords': [],
        'categories': []
    }

    for r in Record.query.all():
        data['records'].append({
            'id': r.id, 'amount': r.amount, 'type': r.type,
            'category': r.category, 'note': r.note,
            'date': r.date.isoformat()
        })

    for c in Config.query.all():
        data['configs'].append({'key': c.key, 'value': c.value})

    for cb in CategoryBudget.query.all():
        data['category_budgets'].append({
            'category': cb.category, 'budget_amount': cb.budget_amount, 'month': cb.month
        })

    for rem in Reminder.query.all():
        data['reminders'].append({
            'type': rem.type, 'day_of_month': rem.day_of_month, 'weekday': rem.weekday,
            'category': rem.category, 'amount': rem.amount, 'note': rem.note, 'is_active': rem.is_active
        })

    for t in Template.query.all():
        data['templates'].append({
            'name': t.name, 'type': t.type, 'category': t.category,
            'amount': t.amount, 'note': t.note
        })

    for ch in Challenge.query.all():
        data['challenges'].append({
            'target_category': ch.target_category, 'target_amount': ch.target_amount,
            'month': ch.month, 'status': ch.status
        })

    for kw in KeywordCategory.query.all():
        data['keywords'].append({'keyword': kw.keyword, 'category': kw.category})

    for cat in Category.query.all():
        data['categories'].append({
            'name': cat.name, 'icon': cat.icon, 'color': cat.color,
            'is_default': cat.is_default, 'sort_order': cat.sort_order
        })

    response = make_response(json.dumps(data, ensure_ascii=False, indent=2))
    response.headers['Content-Type'] = 'application/json'
    response.headers['Content-Disposition'] = f'attachment; filename=ledger_backup_{date.today().strftime("%Y%m%d")}.json'
    return response


@app.route('/restore', methods=['GET', 'POST'])
def restore():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('没有上传文件', 'error')
            return redirect(url_for('index'))

        file = request.files['file']
        if file.filename == '':
            flash('没有选择文件', 'error')
            return redirect(url_for('index'))

        try:
            data = json.load(file)

            Record.query.delete()
            Config.query.delete()
            CategoryBudget.query.delete()
            Reminder.query.delete()
            Template.query.delete()
            Challenge.query.delete()
            KeywordCategory.query.delete()
            Category.query.delete()
            db.session.commit()

            for rec in data.get('records', []):
                r = Record(
                    amount=rec['amount'], type=rec['type'], category=rec['category'],
                    note=rec.get('note', ''), date=datetime.strptime(rec['date'], '%Y-%m-%d').date()
                )
                db.session.add(r)

            for conf in data.get('configs', []):
                c = Config(key=conf['key'], value=conf['value'])
                db.session.add(c)

            for cb in data.get('category_budgets', []):
                c = CategoryBudget(category=cb['category'], budget_amount=cb['budget_amount'], month=cb['month'])
                db.session.add(c)

            for rem in data.get('reminders', []):
                r = Reminder(
                    type=rem['type'], day_of_month=rem.get('day_of_month'),
                    weekday=rem.get('weekday'), category=rem['category'],
                    amount=rem['amount'], note=rem.get('note', ''), is_active=rem.get('is_active', True)
                )
                db.session.add(r)

            for t in data.get('templates', []):
                t_obj = Template(
                    name=t['name'], type=t['type'], category=t['category'],
                    amount=t.get('amount'), note=t.get('note', '')
                )
                db.session.add(t_obj)

            for ch in data.get('challenges', []):
                c = Challenge(
                    target_category=ch['target_category'], target_amount=ch['target_amount'],
                    month=ch['month'], status=ch.get('status', 'active')
                )
                db.session.add(c)

            for kw in data.get('keywords', []):
                k = KeywordCategory(keyword=kw['keyword'], category=kw['category'])
                db.session.add(k)

            for cat in data.get('categories', []):
                c = Category(
                    name=cat['name'], icon=cat.get('icon', '📦'),
                    color=cat.get('color', '#3b82f6'),
                    is_default=cat.get('is_default', False),
                    sort_order=cat.get('sort_order', 0)
                )
                db.session.add(c)

            db.session.commit()
            flash('数据恢复成功！', 'success')
        except Exception as e:
            flash(f'恢复失败: {str(e)}', 'error')

        return redirect(url_for('index'))

    return render_template('restore.html')


with app.app_context():
    db.create_all()
    init_default_categories()
    init_budget()


if __name__ == '__main__':
    app.run(debug=True)