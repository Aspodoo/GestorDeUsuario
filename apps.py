from flask import Flask, render_template, url_for, request, flash, redirect, session
from database import conectar 

apps = Flask(__name__)
apps.secret_key = "12345"

# LOGIN

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
    user = cursor.fetchone()

    if user:
        session['usuario'] = user[1]
        session['rol'] = user[3]

        return redirect(url_for("inicio"))
    else:
        flash("Usuario y contraseña incorrectos", "danger")
        return redirect(url_for('login'))

# INICIO

@apps.route('/inicio')
def inicio():

    if 'usuario' not in session:
        return redirect(url_for('login'))

    con = conectar()
    cursor = con.cursor()

    cursor.execute("SELECT * FROM usuarios")
    lista_usuarios = cursor.fetchall()

    cursor.execute("""
        SELECT e.*, d.nombre_area 
        FROM empleados e
        INNER JOIN departamentos d 
        ON e.id_area = d.id_area
    """)
    lista_empleados = cursor.fetchall()

    cursor.execute("SELECT * FROM departamentos")
    lista_areas = cursor.fetchall()

    cursor.close()
    con.close()

    return render_template(
        "index.html",
        user=lista_usuarios,
        empleados=lista_empleados,
        areas=lista_areas
    )

# REGISTRAR USUARIO

@apps.route('/registrar', methods=["POST"])
def registrar():

    if 'usuario' not in session:
        return redirect(url_for('login'))

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

# REGISTRAR EMPLEADO

@apps.route('/registrar_empleado', methods=["POST"])
def registrar_empleado():

    if 'usuario' not in session:
        return redirect(url_for('login'))

    documento = request.form['documento']
    nombre = request.form['nombre']
    apellido = request.form['apellido']
    cargo = request.form['cargo']
    salario = float(request.form['salario'])

    horas = int(request.form['horas_extras'] or 0)
    bonificacion = float(request.form['bonificacion'] or 0)
    area = request.form['id_area']

    # CALCULOS
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

# ELIMINAR

@apps.route('/eliminar/<int:id>')
def eliminarusu(id):

    if 'usuario' not in session:
        return redirect(url_for('login'))

    con = conectar()
    cursor = con.cursor()

    cursor.execute("DELETE FROM usuarios WHERE id_usuario=%s", (id,))
    con.commit()

    cursor.close()
    con.close()

    flash("Usuario eliminado", "success")
    return redirect(url_for("inicio"))

# ELIMINAR EMPLEADO

@apps.route('/eliminar_empleado/<int:id>')
def eliminar_empleado(id):

    if 'usuario' not in session:
        return redirect(url_for('login'))

    con = conectar()
    cursor = con.cursor()

    cursor.execute("DELETE FROM empleados WHERE id_empleado=%s", (id,))
    con.commit()

    cursor.close()
    con.close()

    flash("Empleado eliminado", "success")
    return redirect(url_for("inicio"))

# EDITAR USUARIO

@apps.route('/editar/<int:id>')
def editar(id):

    if 'usuario' not in session:
        return redirect(url_for('login'))

    con = conectar()
    cursor = con.cursor()

    cursor.execute("SELECT * FROM usuarios WHERE id_usuario=%s", (id,))
    usuario = cursor.fetchone()

    cursor.close()
    con.close()

    return render_template("editar.html", usuario=usuario)

# EDITAR EMPLEADO

@apps.route('/editar_empleado/<int:id>')
def editar_empleado(id):

    if 'usuario' not in session:
        return redirect(url_for('login'))

    con = conectar()
    cursor = con.cursor()

    cursor.execute("SELECT * FROM empleados WHERE id_empleado=%s", (id,))
    empleado = cursor.fetchone()

    cursor.close()
    con.close()

    return render_template("editar_empleado.html", empleado=empleado)

# ACTUALIZAR USUARIO

@apps.route('/actualizar', methods=["POST"])
def actualizar():

    if 'usuario' not in session:
        return redirect(url_for('login'))

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

    flash("Usuario actualizado", "success")
    return redirect(url_for('inicio'))

# ACTUALIZAR EMPLEADO

@apps.route('/actualizar_empleado', methods=["POST"])
def actualizar_empleado():

    if 'usuario' not in session:
        return redirect(url_for('login'))

    id = request.form['id']
    documento = request.form['documento']
    nombre = request.form['nombre']
    apellido = request.form['apellido']
    cargo = request.form['cargo']
    salario = float(request.form['salario'])

    horas = int(request.form['horas_extras'] or 0)
    bonificacion = float(request.form['bonificacion'] or 0)
    area = request.form['id_area']

    # RECALCULAR
    valor_hora = salario / 240
    total_horas_extras = horas * valor_hora * 1.5

    salud = salario * 0.04
    pension = salario * 0.04

    salario_neto = salario + bonificacion + total_horas_extras - salud - pension

    con = conectar()
    cursor = con.cursor()

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

    con.commit()
    cursor.close()
    con.close()

    flash("Empleado actualizado correctamente", "success")
    return redirect(url_for('inicio'))

#  SALIR

@apps.route('/salir')
def salir():
    session.clear()
    return redirect(url_for('login'))

#  MAIN 

if __name__ == '__main__':
    apps.run(debug=True)