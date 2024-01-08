from datetime import datetime

from flask import Flask, render_template, request, redirect, flash, make_response, session, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from flask_sqlalchemy import SQLAlchemy
from flask import current_app

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(128), nullable=False, unique=True)
    password = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(128), nullable=False)
    balance = db.Column(db.Float, nullable=False)
    roll = db.Column(db.String, nullable=False)
    secrets = db.Column(db.String(128))


class Transaction(db.Model):
    __tablename__ = 'transaction'

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    index = db.Column(db.String(100), nullable=False)
    transaction_type = db.Column(db.String(24), nullable=False)  # 'income' или 'expense'
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    # Отношение транзакций к пользователям
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


class Category(db.Model):
    __tablename__ = 'category'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
