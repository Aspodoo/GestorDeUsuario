from flask import Flask, render_template, request, redirect, url_for, session, flash
from database import conectar

apps = Flask(__name__)
apps.secret_key = "12345"

# ---------------- LOGIN ----------------

@apps.route('/')
def login():
    return render_template("login.html")


@apps.route('/', methods=["POST"])
def login_form():

    user = request.form['txtusuario']
    password = request.form['txtcontrasena']

    con = conectar()
    cursor = con.cursor()

    cursor.execute("SELECT * FROM usuarios WHERE usuario=%s AND PASSWORD=%s", (user, password))
    user_db = cursor.fetchone()

    if user_db:
        session['usuario'] = user_db[1]
        session['rol'] = user_db[3]
        session['documento'] = user_db[4]

        if user_db[3] == "administrador":
            return redirect(url_for("inicio"))
        else:
            return redirect(url_for("panel_empleado"))
    else:
        flash("Usuario y contraseña incorrectos", "danger")
        return redirect(url_for('login'))

# ---------------- PANEL ADMIN ----------------

@apps.route('/inicio')
def inicio():

    if 'usuario' not in session:
        return redirect(url_for('login'))

    if session['rol'] != "administrador":
        return redirect(url_for('panel_empleado'))

    con = conectar()
    cursor = con.cursor()

    cursor.execute("SELECT * FROM usuarios")
    usuarios = cursor.fetchall()

    cursor.execute("""
        SELECT e.*, d.nombre_area 
        FROM empleados e
        INNER JOIN departamentos d 
        ON e.id_area = d.id_area
    """)
    empleados = cursor.fetchall()

    cursor.execute("SELECT * FROM departamentos")
    areas = cursor.fetchall()

    cursor.close()
    con.close()

    return render_template("index.html", user=usuarios, empleados=empleados, areas=areas)

# ---------------- PANEL EMPLEADO ----------------

@apps.route('/panel_empleado')
def panel_empleado():

    if 'usuario' not in session:
        return redirect(url_for('login'))

    con = conectar()
    cursor = con.cursor()

    cursor.execute("""
        SELECT e.*, d.nombre_area 
        FROM empleados e
        INNER JOIN departamentos d 
        ON e.id_area = d.id_area
        WHERE e.documento=%s
    """, (session['documento'],))

    empleado = cursor.fetchone()

    cursor.close()
    con.close()

    return render_template("panel_empleado.html", empleado=empleado)

# ---------------- EDITAR USUARIO ----------------

@apps.route('/editar/<int:id>')
def editar(id):

    if 'usuario' not in session:
        return redirect(url_for('login'))

    if session['rol'] != "administrador":
        flash("No tienes permisos para editar usuarios", "danger")
        return redirect(url_for('panel_empleado'))

    con = conectar()
    cursor = con.cursor()

    cursor.execute("SELECT * FROM usuarios WHERE id_usuario=%s", (id,))
    usuario = cursor.fetchone()

    cursor.close()
    con.close()

    return render_template("editar.html", usuario=usuario)

# ---------------- ACTUALIZAR USUARIO ----------------

@apps.route('/actualizar', methods=["POST"])
def actualizar():

    if 'usuario' not in session:
        return redirect(url_for('login'))

    if session['rol'] != "administrador":
        flash("No tienes permisos", "danger")
        return redirect(url_for('panel_empleado'))

    id = request.form['id']
    usuario = request.form['usuario']
    password = request.form['password']
    rol = request.form['rol']
    documento = request.form['documento']

    con = conectar()
    cursor = con.cursor()

    cursor.execute("""
        UPDATE usuarios 
        SET usuario=%s, PASSWORD=%s, rol=%s, documento=%s
        WHERE id_usuario=%s
    """, (usuario, password, rol, documento, id))

    con.commit()
    cursor.close()
    con.close()

    flash("Usuario actualizado correctamente", "success")
    return redirect(url_for('inicio'))

# ---------------- REGISTRAR USUARIO ----------------

@apps.route('/registrar', methods=["POST"])
def registrar():

    if 'usuario' not in session:
        return redirect(url_for('login'))

    if session['rol'] != "administrador":
        return redirect(url_for('panel_empleado'))

    usuario = request.form['usuario']
    password = request.form['password']
    rol = request.form['rol']
    documento = request.form['documento']

    con = conectar()
    cursor = con.cursor()

    cursor.execute("SELECT * FROM usuarios WHERE usuario=%s", (usuario,))
    if cursor.fetchone():
        flash("Ese usuario ya existe", "warning")
        return redirect(url_for('inicio'))

    cursor.execute("SELECT * FROM usuarios WHERE documento=%s", (documento,))
    if cursor.fetchone():
        flash("Ese documento ya está registrado", "warning")
        return redirect(url_for('inicio'))

    cursor.execute(
        "INSERT INTO usuarios (usuario, PASSWORD, rol, documento) VALUES (%s, %s, %s, %s)",
        (usuario, password, rol, documento)
    )

    con.commit()
    cursor.close()
    con.close()

    flash("Usuario registrado correctamente", "success")
    return redirect(url_for('inicio'))

# ---------------- REGISTRAR EMPLEADO ----------------

@apps.route('/registrar_empleado', methods=["POST"])
def registrar_empleado():

    if 'usuario' not in session:
        return redirect(url_for('login'))

    if session['rol'] != "administrador":
        return redirect(url_for('panel_empleado'))

    documento = request.form['documento']
    nombre = request.form['nombre']
    apellido = request.form['apellido']
    cargo = request.form['cargo']
    salario = float(request.form['salario'])

    horas = int(request.form['horas_extras'] or 0)
    bonificacion = float(request.form['bonificacion'] or 0)
    area = request.form['id_area']

    valor_hora = salario / 240
    total_horas_extras = horas * valor_hora * 1.5

    salud = salario * 0.04
    pension = salario * 0.04

    salario_neto = salario + bonificacion + total_horas_extras - salud - pension

    con = conectar()
    cursor = con.cursor()

    cursor.execute("SELECT * FROM empleados WHERE documento=%s", (documento,))
    if cursor.fetchone():
        flash("Este empleado ya existe", "warning")
        return redirect(url_for('inicio'))

    cursor.execute("""
        INSERT INTO empleados 
        (documento, nombre, apellido, cargo, salario, horas_extras, bonificacion, salud, pension, salario_neto, id_area)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (documento, nombre, apellido, cargo, salario, horas, bonificacion, salud, pension, salario_neto, area))

    con.commit()
    cursor.close()
    con.close()

    flash("Empleado registrado correctamente", "success")
    return redirect(url_for('inicio'))

# ---------------- ELIMINAR USUARIO ----------------

@apps.route('/eliminar/<int:id>')
def eliminarusu(id):

    if 'usuario' not in session:
        return redirect(url_for('login'))

    if session['rol'] != "administrador":
        return redirect(url_for('panel_empleado'))

    con = conectar()
    cursor = con.cursor()

    cursor.execute("DELETE FROM usuarios WHERE id_usuario=%s", (id,))
    con.commit()

    cursor.close()
    con.close()

    flash("Usuario eliminado", "success")
    return redirect(url_for("inicio"))

# ---------------- ELIMINAR EMPLEADO ----------------

@apps.route('/eliminar_empleado/<int:id>')
def eliminar_empleado(id):

    if 'usuario' not in session:
        return redirect(url_for('login'))

    if session['rol'] != "administrador":
        return redirect(url_for('panel_empleado'))

    con = conectar()
    cursor = con.cursor()

    cursor.execute("DELETE FROM empleados WHERE id_empleado=%s", (id,))
    con.commit()

    cursor.close()
    con.close()

    flash("Empleado eliminado", "success")
    return redirect(url_for("inicio"))

# ---------------- EDITAR EMPLEADO ----------------

@apps.route('/editar_empleado/<int:id>')
def editar_empleado(id):

    if 'usuario' not in session:
        return redirect(url_for('login'))

    con = conectar()
    cursor = con.cursor()

    cursor.execute("SELECT * FROM empleados WHERE id_empleado=%s", (id,))
    empleado = cursor.fetchone()

    if session['rol'] != "administrador":
        if empleado[1] != session['documento']:
            flash("No tienes permiso", "danger")
            return redirect(url_for('panel_empleado'))

    cursor.close()
    con.close()

    return render_template("editar_empleado.html", empleado=empleado)

# ---------------- ACTUALIZAR EMPLEADO ----------------

@apps.route('/actualizar_empleado', methods=["POST"])
def actualizar_empleado():

    if 'usuario' not in session:
        return redirect(url_for('login'))

    id = request.form['id']
    documento = request.form['documento']

    if session['rol'] != "administrador":
        if str(documento) != str(session['documento']):
            flash("No puedes modificar otro empleado", "danger")
            return redirect(url_for('panel_empleado'))

    nombre = request.form['nombre']
    apellido = request.form['apellido']
    cargo = request.form['cargo']
    area = request.form['id_area']

    con = conectar()
    cursor = con.cursor()

    if session['rol'] == "administrador":

        salario = float(request.form['salario'])
        horas = int(request.form['horas_extras'] or 0)
        bonificacion = float(request.form['bonificacion'] or 0)

        valor_hora = salario / 240
        total_horas_extras = horas * valor_hora * 1.5

        salud = salario * 0.04
        pension = salario * 0.04

        salario_neto = salario + bonificacion + total_horas_extras - salud - pension

        cursor.execute("""
            UPDATE empleados 
            SET documento=%s, nombre=%s, apellido=%s, cargo=%s,
                salario=%s, horas_extras=%s, bonificacion=%s,
                salud=%s, pension=%s, salario_neto=%s, id_area=%s
            WHERE id_empleado=%s
        """, (
            documento, nombre, apellido, cargo,
            salario, horas, bonificacion,
            salud, pension, salario_neto, area, id
        ))

    else:
        cursor.execute("""
            UPDATE empleados 
            SET nombre=%s, apellido=%s, cargo=%s, id_area=%s
            WHERE id_empleado=%s
        """, (nombre, apellido, cargo, area, id))

    con.commit()
    cursor.close()
    con.close()

    flash("Empleado actualizado", "success")

    if session['rol'] == "administrador":
        return redirect(url_for('inicio'))
    else:
        return redirect(url_for('panel_empleado'))

# ---------------- SALIR ----------------

@apps.route('/salir')
def salir():
    session.clear()
    return redirect(url_for('login'))

# ---------------- MAIN ----------------

if __name__ == '__main__':
    apps.run(debug=True)