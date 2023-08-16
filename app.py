from flask import Flask, render_template, request, redirect, url_for,flash, session, jsonify
from flask_mysqldb import MySQL
from functools import wraps
from flask_bcrypt import Bcrypt

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['MYSQL_HOST'] = "127.0.0.1"
app.config['MYSQL_USER'] = "root"
app.config['MYSQL_PASSWORD'] = ""
app.config['MYSQL_DB'] = "BaseMedicos"
app.secret_key = 'mysecretkey'

mysql = MySQL(app)

def get_cursor():
    return mysql.connection.cursor()

@app.route('/')
def index():
    return render_template('login_medi.html')

@app.route('/login', methods=['POST'])
def login():
    rfc = request.form['rfc']
    password = request.form['password']
    cursor = get_cursor()
    query = 'SELECT RFC FROM usuarios WHERE RFC = %s AND password = %s'
    cursor.execute(query, (rfc, password))
    resultado = cursor.fetchone()
    if resultado is not None:
        return redirect(url_for('menu'))
    else:
        flash('RFC o contraseña incorrectos')
        return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3307, debug=True)

