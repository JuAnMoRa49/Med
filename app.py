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

bcrypt = Bcrypt(app)

def get_cursor():
    return mysql.connection.cursor()

@app.route('/')
def index():
    return render_template('login_medi.html')


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Verificar si el correo electrónico está almacenado en la sesión
        if 'rfc_user' not in session:
            # Redirigir al inicio de sesión si no ha iniciado sesión
            flash('Debe iniciar sesión para acceder a esta página.')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def obtener_rol(rfc):
    cursor = get_cursor()
    query = 'SELECT rol FROM Medicos WHERE RFC = %s'
    cursor.execute(query, (rfc,))
    resultado = cursor.fetchone()
    
    if resultado:
        return resultado[0]
    else:
        return None



@app.route('/login', methods=['POST'])
def login():
    
    vrfc = request.form['rfc']
    vpassword = request.form['password']
    CS= mysql.connection.cursor()
    
    # consulta= 'select RFC from Medicos where RFC = %s and password = %s'
    # CS.execute(consulta, (vrfc, vpassword))
    # resultado = CS.fetchone()
    cursor = get_cursor()
    query = 'SELECT RFC, password FROM Medicos WHERE RFC = %s'
    cursor.execute(query, (vrfc,))
    resultado = cursor.fetchone()
    
    if resultado is not None:
        session['rfc_user'] = vrfc
        session['rol'] = obtener_rol(vrfc)
        return redirect(url_for('cons_cita'))
    else:
        flash('RFC o contraseña incorrectos')
        return redirect(url_for('index'))
    



@app.route('/admi_medi', methods=['POST', 'GET'])
@login_required
def admi_medi():
    
    if session.get('rol') == 'Medico':
        flash('Acceso denegado: No tienes permiso para acceder a esta página.', 'error')
        return redirect(url_for('cons_cita'))
    
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

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')  # Encriptar la contraseña
        cursor = get_cursor()
        query = 'INSERT INTO Medicos (RFC, nombreCompleto, cedulaProfesional, correo, password, rol) ' \
                'VALUES (%s, %s, %s, %s, %s, %s)'
        cursor.execute(query, (rfc, nombre, cedula, correo, hashed_password, rol))
        mysql.connection.commit()
        flash('Registro exitosamente!') 
        return redirect(url_for('admi_medi'))

    return render_template('admi_medi.html')



@app.route('/busc_medi', methods=['GET', 'POST'])
@login_required
def buscar():
    
    if session.get('rol') == 'Medico':
        flash('Acceso denegado: No tienes permiso para acceder a esta página.', 'error')
        return redirect(url_for('cons_cita'))
    
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

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    query = '''UPDATE Medicos 
               SET nombreCompleto = %s, cedulaProfesional = %s, correo = %s, password = %s, rol = %s 
               WHERE RFC = %s'''
    cursor.execute(query, (nombre, cedula, correo, hashed_password, rol, rfc))
    mysql.connection.commit()

    flash('Registro actualizado correctamente', 'success')

    return redirect(url_for('buscar'))


@app.route('/eliminar_medico/<rfc>', methods=['POST'])
@login_required
def eliminar_medico(rfc):
    cursor = get_cursor()

    # Eliminar el médico de la base de datos
    query = 'DELETE FROM Medicos WHERE RFC = %s'
    cursor.execute(query, (rfc,))
    mysql.connection.commit()

    flash('Registro eliminado correctamente', 'success')
    return redirect(url_for('admi_medi'))




@app.route('/cons_paci')
@login_required
def cons_paci():
    cursor = get_cursor()

    # Obtener el idMedico del médico que ha iniciado sesión
    rfc_medico = session['rfc_user']
    cursor.execute('SELECT idMedico FROM Medicos WHERE RFC = %s', (rfc_medico,))
    id_medico = cursor.fetchone()[0]

    # Consultar los pacientes registrados por el médico
    query = '''SELECT Pacientes.idPaciente, Medicos.nombreCompleto AS nombreMedico, Pacientes.nombreCompleto AS nombrePaciente,
                      Pacientes.fechaNacimiento, Pacientes.enfermedadesCronicas, Pacientes.alergias, Pacientes.antecedentesFamiliares
               FROM Pacientes
               JOIN Medicos ON Pacientes.idMedico = Medicos.idMedico
               WHERE Medicos.idMedico = %s'''
    cursor.execute(query, (id_medico,))
    pacientes = cursor.fetchall()

    return render_template('consultarPacientes.html', pacientes=pacientes
)


@app.route('/editar_paciente/<int:idPaciente>', methods=['GET', 'POST'])
@login_required
def editar_paciente(idPaciente):
    # Aquí deberías implementar la lógica para editar el paciente con el ID proporcionado
    # y luego renderizar la plantilla de edición de paciente con los datos prellenados
    
    return render_template('editar_paciente.html', idPaciente = idPaciente)



@app.route('/actualizar_paciente/<int:idPaciente>', methods=['POST'])
@login_required
def actualizar_paciente(idPaciente):
    cursor = get_cursor()

    nombrePaciente = request.form.get('nombrePaciente')
    fechanacimiento = request.form.get('fechanacimiento')
    enfermedades = request.form.get('enfermedades')
    alergias = request.form.get('alergias')
    antecedentes = request.form.get('antecedentes')

    query = '''UPDATE Pacientes 
               SET nombrePaciente = %s, fechanacimiento = %s, enfermedadesCronicas = %s, alergias = %s, antecedentesFamiliares = %s
               WHERE idPaciente = %s'''
    cursor.execute(query, (nombrePaciente, fechanacimiento, enfermedades, alergias, antecedentes, idPaciente))
    mysql.connection.commit()

    flash('Paciente actualizado correctamente', 'success')

    return redirect(url_for('cons_paci'))



@app.route('/eliminar_paciente/<int:idPaciente>', methods=['POST'])
@login_required
def eliminar_paciente(idPaciente):
    cursor = get_cursor()

    # Eliminar al paciente de la base de datos
    query = 'DELETE FROM Pacientes WHERE idPaciente = %s'
    cursor.execute(query, (idPaciente,))
    mysql.connection.commit()

    flash('Registro de paciente eliminado correctamente', 'success')
    return redirect(url_for('cons_paci'))


@app.route('/cons_cita', methods=['GET', 'POST'])
@login_required
def cons_cita():
    cursor = get_cursor()
    citas = None
    busqueda_realizada = False  # Variable que indica si se ha hecho una búsqueda

    if request.method == 'POST':
        nombrePaciente = request.form.get('nombre')
        print(f"Buscando citas para el paciente: {nombrePaciente}")  # Debugging
        busqueda_realizada = True  # Cambia el valor a True cuando se realiza una búsqueda

        if nombrePaciente:
            query = '''
                SELECT 
                    Medicos.nombreCompleto AS nombreMedico, 
                    Pacientes.nombreCompleto AS nombrePaciente, 
                    Citas.sintomas, Citas.diagnostico, Citas.tratamiento,
                    Citas.fecha  -- Aquí se agrega el campo fecha
                FROM Citas
                JOIN Pacientes ON Citas.idPaciente = Pacientes.idPaciente
                JOIN Medicos ON Pacientes.idMedico = Medicos.idMedico
                WHERE Pacientes.nombreCompleto LIKE %s
            '''

            print(f"Query: {query}")  # Debugging
            cursor.execute(query, ('%' + nombrePaciente + '%',))
            citas = cursor.fetchall()

            # Debugging
            if citas:
                print(type(citas[0]))

            if not citas:
                print("No se encontraron citas para el paciente.")
            else:
                print(f"Citas encontradas: {len(citas)}")
                for cita in citas:
                    print(cita)

    return render_template('cons_cita.html', citas=citas, busqueda_realizada=busqueda_realizada)




@app.route('/regi_expl', methods=['GET', 'POST'])
@login_required
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

        idMedico = medico[0]
        # Insertar el paciente en la base de datos
        cursor.execute("INSERT INTO Pacientes (idMedico, nombreCompleto, fechaNacimiento, enfermedadesCronicas, alergias, antecedentesFamiliares) VALUES (%s, %s, %s, %s, %s, %s)", (idMedico, nombrePaciente, fechanacimiento, enfermedades, alergias, antecedentes))
        mysql.connection.commit()

        flash('Paciente registrado con éxito', 'success')

        return redirect(url_for('regi_expl'))

    return render_template('regi_expl.html')



@app.route('/cerrar')
def logout():
    session.pop('rfc_user', None)
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)


