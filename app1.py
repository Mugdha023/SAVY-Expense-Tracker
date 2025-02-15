from flask import Flask, render_template, request, redirect, flash, session, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import logging
from logging import FileHandler
import importlib.metadata
from flask_migrate import Migrate
import pandas as pd
import matplotlib.pyplot as plt
import io
from flask import make_response
from sqlalchemy import func


# Print the version of Flask-SQLAlchemy
version = importlib.metadata.version("flask-sqlalchemy")
print(f"Flask-SQLAlchemy version: {version}")

app1 = Flask(__name__)
app1.instance_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance')

app1.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///expense.db"

app1.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app1.config['SECRET_KEY'] = 'your_secret_key_here'

db = SQLAlchemy(app1)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)  # Add this line


class Expense(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    desc = db.Column(db.String(500), nullable=False)
    category = db.Column(db.String(100), nullable=False)  
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    def _repr_(self) -> str:
        return f"{self.sno} - {self.amount}"

class Income(db.Model):
    _bind_key_ = 'income'  # Bind to the income database
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Integer, nullable=False)
    desc = db.Column(db.String(500), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    date_submitted = db.Column(db.DateTime, default=datetime.utcnow)

    def _repr_(self):
        return f"Income({self.amount}, {self.desc})"

# Home route
@app1.route('/')
def home():
    return render_template('home.html')

@app1.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']  # Get the name from the form
        username = request.form['username']
        password = request.form['password']

        # Check if username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists! Please choose a different one.', 'danger')
            return render_template('register.html')

        # Create a new user
        new_user = User(name=name, username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


# Login Route
@app1.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session.clear()  # Clear any existing session data
            session['user_id'] = user.id
            session['username'] = user.username
            session['name'] = user.name  # Store the name in session
            flash(f'Hello {user.name}, welcome to the app!', 'success')  # Greeting
            return redirect('/expenses')
        else:
            flash('Invalid username or password', 'danger')
            return render_template('login.html')

    return render_template('login.html')



@app1.route('/expenses', methods=['GET', 'POST'])
def expenses():
    if 'user_id' not in session:
        flash('You need to log in first!', 'danger')
        return redirect(url_for('login'))

    user_name = session.get('name', 'User')  # Retrieve the name from session
    greeting_message = f"Hello {user_name}, ready to add some expenses!"  # Greeting message

    if request.method == 'POST':
        amount = request.form.get('amount')
        desc = request.form.get('desc')
        category = request.form.get('category')
        if not amount or not desc or not category:
            flash('Expense, description, and category cannot be empty!', 'danger')
            return redirect('/expenses')
        try:
            expense = Expense(amount=float(amount), desc=desc, category=category)
            db.session.add(expense)
            db.session.commit()
            flash('Expense added successfully!', 'success')
        except Exception as e:
            app1.logger.error(f"Error adding expense: {e}")
            flash('An error occurred while adding the expense.', 'danger')
        return redirect('/expenses')

    all_expense = Expense.query.all()
    return render_template('main.html', allExpense=all_expense, greeting_message=greeting_message)


@app1.route('/update/<int:sno>', methods=['GET', 'POST'])
def update(sno):
    expense = Expense.query.filter_by(sno=sno).first_or_404()
    
    if request.method == 'POST':
        amount = request.form.get('amount')
        desc = request.form.get('desc')
        category = request.form.get('category')  
        if not amount or not desc or not category:
            flash('Amount, description, and category cannot be empty!', 'danger')
            return redirect(f'/update/{sno}')
        try:
            expense.amount = float(amount)
            expense.desc = desc
            expense.category = category
            db.session.commit()
            flash('Expense updated successfully!', 'success')
        except Exception as e:
            app1.logger.error(f"Error updating expense: {e}")
            flash('An error occurred while updating the expense.', 'danger')
        return redirect('/expenses')
        
    return render_template('update_expense.html', expense=expense)

@app1.route('/delete_expense/<int:sno>')
def delete_expense(sno):
    expense = Expense.query.filter_by(sno=sno).first_or_404()
    try:
        db.session.delete(expense)
        db.session.commit()
        flash('Expense deleted successfully!', 'success')
    except Exception as e:
        app1.logger.error(f"Error deleting expense: {e}")
        flash('An error occurred while deleting the expense.', 'danger')
    return redirect('/expenses')

@app1.route('/income', methods=['GET', 'POST'])
def income():
    if request.method == 'POST':
        amount = request.form.get('amount')
        desc = request.form.get('desc')
        category = request.form.get('category')  
        if not amount or not desc or not category:
            flash('Income, description, and category cannot be empty!', 'danger')
            return redirect('/income')
        try:
            income = Income(amount=float(amount), desc=desc, category=category)
            db.session.add(income)
            db.session.commit()
            flash('Income added successfully!', 'success')
        except Exception as e:
            app1.logger.error(f"Error adding income: {e}")
            flash('An error occurred while adding the income.', 'danger')
        return redirect('/income')

    allIncome = Income.query.all()
    return render_template('income.html', allIncome=allIncome)

@app1.route('/update/income/<int:id>', methods=['GET', 'POST'])
def update_income(id):
    income = Income.query.filter_by(id=id).first_or_404()
    
    if request.method == 'POST':
        amount = request.form.get('amount')
        desc = request.form.get('desc')
        category = request.form.get('category')  
        if not amount or not desc or not category:
            flash('Amount, description, and category cannot be empty!', 'danger')
            return redirect(f'/update/income/{id}')
        try:
            income.amount = float(amount)
            income.desc = desc
            income.category = category
            db.session.commit()
            flash('Income updated successfully!', 'success')
        except Exception as e:
            app1.logger.error(f"Error updating income: {e}")
            flash('An error occurred while updating the income.', 'danger')
        return redirect('/income')
        
    return render_template('update_income.html', income=income)

@app1.route('/delete_income/<int:id>')
def delete_income(id):
    income = Income.query.filter_by(id=id).first_or_404()
    try:
        db.session.delete(income)
        db.session.commit()
        flash('Income deleted successfully!', 'success')
    except Exception as e:
        app1.logger.error(f"Error deleting income: {e}")
        flash('An error occurred while deleting the income.', 'danger')
    return redirect('/income')


@app1.route('/expense_pie_chart')
def expense_pie_chart():
    # Fetch data from the database using SQLAlchemy
    data = db.session.query(Expense.category, Expense.amount).all()  # Adjust based on your actual data structure
    expenses = pd.DataFrame(data, columns=['Category', 'Amount'])
    
    # Assuming you want to calculate the expenses based on 'desc'
    expenses['Amount'] = pd.to_numeric(expenses['Amount'], errors='coerce')  # Convert to numeric
    
    # Drop rows where 'Amount' is NaN
    expenses.dropna(subset=['Amount'], inplace=True)
    
    # Aggregate expenses by category
    category_sums = expenses.groupby('Category').sum()

    # Generate pie chart
    plt.figure(figsize=(8, 8))
    plt.pie(category_sums['Amount'], labels=category_sums.index, autopct='%1.1f%%')
    plt.title('Expenses by Category')

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    
    response = make_response(buf.getvalue())
    response.headers['Content-Type'] = 'image/png'
    return response


@app1.route('/income_pie_chart')
def income_pie_chart():
    # Fetch data from the database using SQLAlchemy
    data = db.session.query(Income.category, Income.amount).all()  # Adjust based on your actual data structure
    incomes = pd.DataFrame(data, columns=['Category', 'Amount'])
    
    # Assuming you want to calculate the incomes based on 'desc'
    incomes['Amount'] = pd.to_numeric(incomes['Amount'], errors='coerce')  # Convert to numeric
    
    # Drop rows where 'Amount' is NaN
    incomes.dropna(subset=['Amount'], inplace=True)
    
    # Aggregate expenses by category
    category_sums = incomes.groupby('Category').sum()

    # Generate pie chart
    plt.figure(figsize=(8, 8))
    plt.pie(category_sums['Amount'], labels=category_sums.index, autopct='%1.1f%%')
    plt.title('Incomes by Category')

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    
    response = make_response(buf.getvalue())
    response.headers['Content-Type'] = 'image/png'
    return response


@app1.route('/e')
def e():
    # Query to get all expenses
    e = Expense.query.all()
    
    # Query to calculate the total amount directly in the database
    total_amount = db.session.query(func.sum(Expense.amount)).scalar() or 0

    return render_template('expenses.html', e=e, total_amount=total_amount)



if __name__ == "__main__":
    with app1.app_context():
        db.create_all()  # Create tables based on models defined
# Set up logging to a file in the current project directory
log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'error.log')
file_handler = FileHandler(log_path)
file_handler.setLevel(logging.ERROR)
app1.logger.addHandler(file_handler)

app1.run(debug=True)