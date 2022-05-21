from flask import (
    Blueprint, flash, g, redirect, session, render_template, request, url_for
)
from werkzeug.exceptions import abort
from hw_tracker.auth import login_required
from hw_tracker.db import get_db
from hw_tracker.email_alert import email_alert
from datetime import date, datetime
import urllib.parse

bp = Blueprint('homework', __name__)


@bp.route('/')
def welcome():
    return render_template('homework/welcome.html')


@bp.route('/index')
def index():
    db = get_db()
    hw_items = db.execute(
        'SELECT hw.id, course, name, typehw, desc, duedate, completed, author_id, u.username'
        '   FROM hw JOIN user u on hw.author_id = u.id'
    ).fetchall()
    return render_template('homework/index.html', hw_items=hw_items)


@bp.route('/create', methods=('POST', 'GET'))
@login_required
def create():
    if request.method == 'POST':
        course = request.form.get("course")
        name = request.form.get("name")
        type = request.form.get("type")
        desc = request.form.get("description")
        dd = request.form.get("duedate")
        error = None

        if not course or not name or not type or not desc or not dd:
            error = 'Please enter all fields'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO hw (course, name, typehw, desc, duedate, completed, author_id)'
                '   VALUES (?, ?, ?, ?, ?, ?, ?)',
                (course, name, type, desc, dd, 'no', g.user['id'])
            )
            db.commit()
            return redirect(url_for('homework.confirmation'))

    return render_template('homework/create.html')


def get_hw(id, check_author=True):
    hw = get_db().execute(
        'SELECT hw.id, course, name, typehw, desc, duedate, completed, author_id'
        '   FROM hw JOIN user u on hw.author_id = u.id'
        '   WHERE hw.id = ?',
        (id,)
    ).fetchone()

    if hw is None:
        abort(404, f'Homework id {id} doesn\'t exist.')

    if check_author and hw['author_id'] != g.user['id']:
        abort(403)

    return hw


@bp.route('/<int:id>/update', methods=('POST', 'GET'))
@login_required
def update(id):
    hw = get_hw(id)

    if request.method == 'POST':
        course = request.form.get("course")
        name = request.form.get("name")
        type = request.form.get("type")
        desc = request.form.get("description")
        dd = request.form.get("duedate")
        error = None

        if not course or not name or not type or not desc or not dd:
            error = 'Please enter all fields'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE hw SET course = ?, name = ?, typehw = ?, desc = ?, duedate = ?, completed = ?'
                '   WHERE id = ?',
                (course, name, type, desc, dd, 'no', id)
            )
            db.commit()
            return redirect(url_for('homework.index'))

    return render_template('homework/update.html', hw=hw)


@bp.route('/<int:id>/email', methods=('POST', 'GET'))
@login_required
def email(id):  # pragma: no cover
    hw = get_db().execute(
        'SELECT hw.duedate, course, desc, author_id, u.username'
        '   FROM hw JOIN user u on hw.author_id = u.id'
        '   WHERE hw.id = ?',
        (id,)
    ).fetchone()

    if request.method == 'POST':
        email_address = request.form.get("email_address")
        error = None
        if not email_address:
            error = "PLease gg"
        if error is not None:
            flash(error)
        else:
            y_str, m_str, d_str = hw[0].split('-')
            #email_address = str(email_form).replace('%40', '@')
            #y = int(hw['duedate'].strftime("%Y"))
            #m = int(hw['duedate'].strftime("%B"))
            #d = int(hw['duedate'].strftime("%d")) - 1

            y = int(y_str)
            m = int(m_str)
            d = int(d_str)-1
            email_alert(hw[1], hw[2], email_address)

            # Update the database
            db = get_db()
            db.execute(
                'INSERT INTO email_list (email_address, author_id)'
                '   VALUES (?, ?)',
                (email_address, g.user['id'])
            )
            db.commit()
            return redirect(url_for('homework.emailconfirm'))
    return render_template('homework/email.html')


@bp.route('/<int:id>/delete')
@login_required
def delete(id):
    get_hw(id)
    db = get_db()
    db.execute('DELETE FROM hw WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('homework.deleteconfirm'))


@bp.route('/about')
def about():
    return render_template('homework/welcome.html')


@bp.route('/settings')
def settings():
    return render_template('homework/settings.html')


@bp.route('/confirmation')
def confirmation():
    return render_template('homework/confirmation.html')


@bp.route('/emailconfirm')
def emailconfirm():
    return render_template('homework/emailconfirm.html')


@bp.route('/deleteconfirm')
def deleteconfirm():
    return render_template('homework/deleteconfirm.html')


@bp.route('/toggle_theme')
def toggle_theme():
    current_theme = session.get('theme')
    if current_theme == 'dark':
        session['theme'] = 'light'
    else:
        session['theme'] = 'dark'

    return redirect(url_for('homework.settings'))
