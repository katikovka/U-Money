from flask import request, jsonify, session
from flask import Blueprint
from sweater.models import db, User, Category, Transaction
from sqlalchemy import text

api_bp = Blueprint("api", __name__, template_folder="templates", static_folder="static")


@api_bp.route('/history', methods=['POST', 'GET'])
def history():
    key = None
    if request.method == "POST":
        key = request.json.get('key')
    elif request.method == "GET":
        key = request.args.get('key')
    history = (db.session.query(
        User.name,
        Category.name,
        Transaction.amount,
        Transaction.transaction_type,
        Transaction.date)
               .filter(User.id == Transaction.user_id)
               .filter(Category.id == Transaction.category_id)
               .filter(Transaction.index == key)
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

    return jsonify(history_list)
