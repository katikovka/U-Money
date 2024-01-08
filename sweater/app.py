import os
import secrets
import string

from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, flash, session
from flask_login import LoginManager, login_user, login_required, logout_user
from werkzeug.security import check_password_hash, generate_password_hash
from flask_mail import Mail, Message
from sqlalchemy import or_
from sqlalchemy import text
from sweater.api import api_bp
from sweater.models import Category, Transaction, User, db
from sweater.admin import admin

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db_flask.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["JSON_AS_ASCII"] = True
app.config["SECRET_KEY"] = "SECRET_Kedrftgyhujmikjhswedfrgthyju8kie4dfrgt6hyjukiefrgthyjuiEY"
app.config["JSON_AS_ASCII"] = True
app.config["MAIL_SERVER"] = 'smtp.gmail.com'
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = 'katikovka@gmail.com'
app.config["MAIL_PASSWORD"] = 'wmxc mscl lvgy sgmj'
app.secret_key = os.environ["secret_key"]
manager = LoginManager(app)
db.init_app(app)
admin.init_app(app)


mail = Mail(app)

app.register_blueprint(api_bp, url_prefix="/api")


def generate_secure_string(length=50):
    alphabet = string.ascii_letters
    secure_string = ''.join(secrets.choice(alphabet) for _ in range(length))
    return secure_string


@manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


@app.route('/')
def index():
    return render_template("about.html")


@app.route('/secret_key')
@login_required  # only login users
def get_secret_key():
    print(session.get('data')['key'])
    return render_template("secret_key.html", secret_key=session.get('data')['key'])


@app.route('/search')
@login_required
def search(search_text=None):

    key_value = session.get('data')['key']

    if search_text:
        history = (db.session.query(
            User.name,
            Category.name,
            Transaction.amount,
            Transaction.transaction_type,
            Transaction.date)
                   .filter(User.id == Transaction.user_id)
                   .filter(Category.id == Transaction.category_id)
                   .filter(Transaction.index == key_value)
                   .filter(or_(
            User.name == search_text,
            Transaction.date == search_text,
            Transaction.amount == search_text,
            Transaction.transaction_type == search_text))
                   .order_by(Transaction.date.desc())
                   .all())
        print(db.session.query(Transaction.date))
    else:
        history = (db.session.query(
            User.name,
            Category.name,
            Transaction.amount,
            Transaction.transaction_type,
            Transaction.date)
                   .filter(User.id == Transaction.user_id)
                   .filter(Category.id == Transaction.category_id)
                   .filter(Transaction.index == key_value)
                   .order_by(Transaction.date.desc())
                   .all())
    history_list = []
    for data in history:
        username, categories_name, transaction_money, transaction_type, transaction_date = data
        history_list.append(
            {'name': username,
             'name_transactions': categories_name,
             'money': transaction_money,
             'type': transaction_type,
             'date': f'{transaction_date.hour}:{transaction_date.minute} '
                     f'{transaction_date.day}.{transaction_date.month}.{transaction_date.year}'})

    return history_list


@app.route('/home')
@login_required  # only login users
def about():
    key = request.args.get('key')
    print(session.get('data')['key'])
    search_text = request.args.get('searchText')
    search(search_text)

    if session.get('data')['roll'] == 'user' and not db.session.query(User).filter(User.secrets == key).first():
        return render_template('test.html')
    if db.session.query(User).filter(User.secrets == session.get('data')['key']).first():
        column_name = db.session.query(Category).join(User).filter(User.secrets == session.get('data')['key']).all()
        categories = [row.name for row in column_name]
        user = db.session.query(User).filter(User.id == session.get('data')['id']).first()
        key_value = session.get('data')['key']

        history_list = search(search_text)

        creator = (db.session.query(User.name).filter(User.secrets == session.get('data')['key']).first()[0]
                   if session.get('data')['roll'] == 'active_user' else None)
        secret_key = (session.get('data')['key']
                      if session.get('data')['roll'] == 'creator'
                      else "Вы не обладаете секретным ключём так как вы подключились с счёту")

        return render_template("test.html", name=user.name, categories=categories, amount=
        db.session.query(User.balance).filter(User.secrets == session.get('data')['key']).first()[0],
                               secret_key=secret_key,
                               creator=creator,
                               history=history_list)

    return redirect('/')


@app.route('/register', methods=['GET', 'POST'])
def register_page():
    if request.method == 'POST':
        login = request.form.get('login')
        name = request.form.get('name')
        password = request.form.get('password')
        re_password = request.form.get('re_password')
        if not (login and password and re_password and name):
            flash("Please enter your login or password")
        elif db.session.query(User.login).filter(User.login == login).scalar():
            flash(f"Login {login} registered")
            return redirect('/register')
        elif password != re_password:
            flash("Password are not equal")
        else:
            password = generate_password_hash(password, "sha256")
            new_user = User(login=login, password=password, name=name, balance=0, roll="Неопределённый")
            db.session.add(new_user)
            db.session.commit()

            return redirect("/login")

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'GET':
        return render_template('login.html')

    login = request.form.get('login')
    password = request.form.get('password')
    roll = request.form.get('roll')

    if login and password:
        user = User.query.filter_by(login=login).first()
        if not user:
            flash('Login not found')
            return render_template('login.html')

        if check_password_hash(user.password, password):
            login_user(user)
            user_id = db.session.query(User.id).filter(User.login == login).first()[0]
            user.roll = roll

            if not db.session.query(Category.name).join(User).filter(User.id == user_id).all():
                db.session.execute(text("INSERT INTO category (name, user_id) VALUES ('Прочее', :id)"), {'id': user_id})
            if roll == 'creator' and not db.session.query(User.secrets).filter(User.login == login).first()[0]:
                key = generate_secure_string()
                db.session.execute(text("update user SET secrets = :secrets where login = :login"),
                                   {'secrets': key, 'login': login})
            db.session.commit()
            session['data'] = {'id': user_id, 'roll': roll,
                               'key': db.session.query(User.secrets).filter(User.login == login).first()[0]}

            next_page = request.args.get('next')
            if not next_page:
                next_page = "/"
            return redirect(next_page)
        else:
            flash('Invalid login or password')
            return render_template('login.html')
    else:
        flash('Please fill login and password fields')
        return render_template('login.html')


@app.route('/logout', methods=['GET', 'POST'])
@login_required  # only login users
def logout():
    session.pop('data', None)
    logout_user()
    return redirect('/')


@app.route('/join', methods=['POST', ])
def join():
    print(request.form.get('key'))
    if db.session.query(User.secrets).filter(User.secrets == request.form.get('key')).first()[0]:
        db.session.execute(text("update user set roll = :roll where id = :id"),
                           {'roll': 'active_user', 'id': session.get('data')['id']})
        db.session.commit()
        session['data']['key'] = request.form.get('key')
        session['data']['roll'] = 'active_user'
        session.modified = True
        print(12)
        print(session['data'])
        return redirect('/home')
    return redirect('/')


@app.route('/update_balance', methods=['POST', ])
@login_required
def update_balance():
    action = request.form.get('action')
    overhead = float(request.form.get('overhead'))

    amount = db.session.query(User.balance).filter(User.secrets == session.get('data')['key']).first()[0]
    if action == 'expenses':
        amount -= overhead
        category = request.form.get('dropdownList')
        category_id = db.session.query(Category.id).join(User).filter(
            User.secrets == session.get('data')['key'] and Category.name == category).first()[0]

        user = db.session.query(User).get(1)
        db.session.execute(text("update user set balance = :balance where secrets = :secrets"),
                           {'balance': amount, 'secrets': session.get('data')['key']})
        db.session.commit()
        print(category_id)
        print(user)
        new_transaction = Transaction(category_id=category_id, amount=overhead, index=session.get('data')['key'],
                                      transaction_type='expenses',
                                      user_id=session.get('data')['id'])
        db.session.add(new_transaction)
        db.session.commit()
    elif action == 'income':
        amount += overhead
        category = request.form.get('dropdownList')
        category_id = db.session.query(Category.id).join(User).filter(
            User.secrets == session.get('data')['key'] and Category.name == category).first()[0]
        db.session.execute(text("update user set balance = :balance where secrets = :secrets"),
                           {'balance': float(amount), 'secrets': session.get('data')['key']})
        db.session.commit()
        new_transaction = Transaction(category_id=category_id, amount=overhead, index=session.get('data')['key'],
                                      transaction_type='income',
                                      user_id=session.get('data')['id'])
        db.session.add(new_transaction)
        db.session.commit()

    return redirect('/home')


@app.after_request
def redirect_to_registered(response):
    if response.status_code == 401:
        return redirect('/login' + '?next=' + request.url)
    return response


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name")
        message = request.form.get("message")
        email = request.form.get("email")
        msg = Message("Вам поступило новое обращение на сайте", sender=email,
                      recipients=["katikovka@gmail.com"])
        msg.body = f"""
        имя: {name}
        сообщение: {message}
        """
        mail.send(msg)
        flash("Ваше сообщение доставлено")
        return redirect('/')
    else:
        return redirect('/')


@app.route('/add_category', methods=['POST'])
def add_category():
    # categories_string = request.json.get('categories')
    # print(categories_string)
    # # categories_string = request.form.get('categories')
    #
    # if not categories_string:
    #     flash('Please provide at least one category')
    #     return redirect('/home')
    #
    # categories_list = [category.strip() for category in categories_string.split(' ')]
    #
    # for category in categories_list:
    #     sql_query = text('INSERT INTO category (user_id, name) VALUES (:user_id, :category)')
    #     db.session.execute(sql_query, {'user_id': session.get('data')['id'], 'category': category})
    #
    # db.session.commit()
    # flash('Categories added successfully')
    #
    # return redirect('/home')

    categories_json = request.json.get('categorias')  # Получаем JSON-данные из POST-запроса
    # user_id = session.get('data')['id']  # Получаем user_id из сессии
    user_id = request.json.get('user_id')
    print("categories", categories_json)
    print("user", user_id)
    print(22)

    if categories_json is None:
        return 'error: Please provide at least one category'

    # categories_string = categories_json['categories']
    categories_list = [category.strip() for category in categories_json.split(' ')]



    for category_name in categories_list:
        # Создаем новую категорию и добавляем ее в базу данных
        new_category = Category(name=category_name, user_id=user_id)
        db.session.add(new_category)

    db.session.commit()
    return 'message: Categories added successfully'


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
