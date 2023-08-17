from flask import Flask, render_template, request, redirect, url_for,flash, session, jsonify
from flask_mysqldb import MySQL
from functools import wraps
from flask_bcrypt import Bcrypt

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['MYSQL_HOST'] = "localhost"
app.config['MYSQL_USER'] = "root"
app.config['MYSQL_PASSWORD'] = "danny22"
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
    query = 'SELECT RFC FROM Medicos WHERE RFC = %s AND password = %s'
    cursor.execute(query, (rfc, password))
    resultado = cursor.fetchone()
    if resultado is not None:
        return redirect(url_for('admi_medi'))
    else:
        flash('RFC o contraseña incorrectos', 'error')  # Flash an error message
        return redirect(url_for('index'))


@app.route('/busc_medi', methods=['GET', 'POST'])
def buscar():
    cursor = get_cursor()
    user = None

    if request.method == 'POST':
        rfc = request.form.get('rfc')

        query = 'SELECT nombreCompleto, cedulaProfesional, correo, password, rol FROM Medicos WHERE RFC = %s'
        cursor.execute(query, (rfc,))
        result = cursor.fetchone()

        if result:
            user = {
                "RFC": rfc,
                "NombreCompleto": result[0],
                "CedulaProfesional": result[1],
                "Correo": result[2],
                "Password": result[3],
                "Rol": result[4]
            }
            # Redirigir a la pantalla de actualización con los datos prellenados
            return render_template('actu_medi.html', user=user)

        else:
            flash('Usuario no encontrado!', 'error')

        cursor.close()  # Cerrar el cursor después de usarlo

    return render_template('busc_medi.html', user=user)

@app.route('/actu_medi', methods=['POST'])
def actu_medi():
    cursor = get_cursor()
    
    rfc = request.form.get('RFC')
    nombre = request.form.get('NombreCompleto')
    cedula = request.form.get('CedulaProfesional')
    correo = request.form.get('correo')
    password = request.form.get('password')
    rol = request.form.get('rol')

    query = '''UPDATE Medicos 
               SET nombreCompleto = %s, cedulaProfesional = %s, correo = %s, password = %s, rol = %s 
               WHERE RFC = %s'''
    cursor.execute(query, (nombre, cedula, correo, password, rol, rfc))
    mysql.connection.commit()

    flash('Registro actualizado correctamente', 'success')

    return redirect(url_for('buscar'))




@app.route('/admi_medi', methods=['POST', 'GET'])
# @login_required
def admi_medi():
    if request.method == 'POST':
        rfc = request.form.get('rfc')
        nombre = request.form.get('nombre')
        cedula = request.form.get('cedula')
        correo = request.form.get('correo')
        password = request.form.get('password')
        rol = request.form.get('rol')

        if not all([rfc, nombre, cedula, correo, password, rol]):
            error_message = "Por favor, completa todos los campos"
            return render_template('admi_medi.html', error=error_message)

        if rol == 'medicoadmin':
            rol = 'Médico Admin'
        elif rol == 'medico':
            rol = 'Médico'

        cursor = get_cursor()
        query = 'INSERT INTO Medicos (RFC, nombreCompleto, cedulaProfesional, correo, password, rol) ' \
                'VALUES (%s, %s, %s, %s, %s, %s)'
        cursor.execute(query, (rfc, nombre, cedula, correo, password, rol))
        mysql.connection.commit()

        return redirect(url_for('admi_medi'))

    return render_template('admi_medi.html')

@app.route('/cons_cita', methods=['GET', 'POST'])
def cons_cita():
    cursor = get_cursor()
    citas = None

    if request.method == 'POST':
        nombreMedico = request.form.get('nombreMedico')
        fecha = request.form.get('fecha')

        if nombreMedico:
            query = '''SELECT Medicos.nombreCompleto AS nombreMedico, Pacientes.nombreCompleto AS nombrePaciente, Citas.*
                       FROM Citas
                       JOIN Pacientes ON Citas.idPaciente = Pacientes.idPaciente
                       JOIN Medicos ON Pacientes.idMedico = Medicos.idMedico
                       WHERE Medicos.nombreCompleto LIKE %s'''
            cursor.execute(query, ('%' + nombreMedico + '%',))
            citas = cursor.fetchall()  # Ejecutar y obtener los resultados
        elif fecha:
            query = '''SELECT Medicos.nombreCompleto AS nombreMedico, Pacientes.nombreCompleto AS nombrePaciente, Citas.*
                       FROM Citas
                       JOIN Pacientes ON Citas.idPaciente = Pacientes.idPaciente
                       JOIN Medicos ON Pacientes.idMedico = Medicos.idMedico
                       WHERE Citas.fecha = %s'''
            cursor.execute(query, (fecha,))
            citas = cursor.fetchall()  # Ejecutar y obtener los resultados
        

    return render_template('cons_cita.html', citas=citas)




@app.route('/regi_expl', methods=['GET', 'POST'])
def regi_expl():
    if request.method == 'POST':
        medicoAtiende = request.form['medicoAtiende']
        nombrePaciente = request.form['nombrePaciente']
        fechanacimiento = request.form['fechanacimiento']
        enfermedades = request.form['enfermedades']
        alergias = request.form['alergias']
        antecedentes = request.form['antecedentes']

        cursor = get_cursor()

        # Obtener el idMedico a partir del nombre del médico
        cursor.execute("SELECT idMedico FROM Medicos WHERE nombreCompleto = %s", (medicoAtiende,))
        medico = cursor.fetchone()
        if not medico:
            flash('El médico proporcionado no existe', 'error')
            return redirect(url_for('regi_expl'))

        idMedico = medico['idMedico']

        # Insertar el paciente en la base de datos
        cursor.execute("INSERT INTO Pacientes (idMedico, nombreCompleto, fechaNacimiento, enfermedadesCronicas, alergias, antecedentesFamiliares) VALUES (%s, %s, %s, %s, %s, %s)", (idMedico, nombrePaciente, fechanacimiento, enfermedades, alergias, antecedentes))
        mysql.connection.commit()

        flash('Paciente registrado con éxito', 'success')

        return redirect(url_for('regi_expl'))

    return render_template('regi_expl.html')



@app.route('/cerrar')
def logout():
    # session.pop('rfcu', None)
    # Redirigir al usuario a la página de inicio de sesión
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)


