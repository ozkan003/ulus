from flask import Flask, render_template, redirect, url_for, session, logging, request
from flask.helpers import flash
from flask_mysqldb import MySQL
from flask_wtf import FlaskForm
from wtforms import Form, StringField, PasswordField, SubmitField, validators
from passlib.hash import sha256_crypt
from functools import wraps
from datetime import timedelta

# Kullanıcı Giriş Durumunu Kontrol Eden DEcoder Fonksiyonu


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Bu sayfayı görüntülemek için giriş yapınız!", "danger")
            return redirect(url_for("login"))
    return decorated_function


# Kullanıcı Giriş Formu WTF Form İle Oluşturulan class
class LoginForm(Form):
    username = StringField("Kullanıcı Adı")
    password = PasswordField("Şifre")


class SearchForm(FlaskForm):
    text_area = StringField("Ara", validators=[validators.DataRequired()])
    submit = SubmitField("Gönder")


# Flask app konfigürasyonları
app = Flask(__name__)
app.secret_key = "k!asdlLdkfjpS0FD*fsad"
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "data"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"
app.permanent_session_lifetime = timedelta(minutes=1)


mysql = MySQL(app)


@app.route("/", methods=["GET", "POST"])
def index():
    form = SearchForm()
    if form.validate_on_submit():
        id = form.text_area.data
        return redirect(url_for("student", id=id))
    else:
        return render_template("index.html", form=form)


@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    form = SearchForm()
    if form.validate_on_submit():
        id = form.text_area.data
        # Virgül ile gelen id için çalışan koşul (POST request)
        if "," in id:
            liste = id.split(",")
            len_list = len(liste)
            liste = tuple(liste)
            cursor = mysql.connection.cursor()
            sorgu = "Select * from student where id in %s"
            result = cursor.execute(sorgu, (liste,))

            if result > 0:
                ogrenci = cursor.fetchall()
            else:
                flash("Böyle Bir Öğrenci Bulunamadı!", "danger")
                return redirect(url_for("index"))

            cursor.close()
            return render_template("dashboard.html", form=form, len_list=len_list, ogrenci=ogrenci)

        # Virgülsüz gelen id için çalışan koşul (POST request)
        else:
            cursor = mysql.connection.cursor()
            sorgu = "Select * from student where id=%s"
            result = cursor.execute(sorgu, (id,))
            if result > 0:
                ogrenci = cursor.fetchone()
            else:
                flash("Böyle Bir Öğrenci Bulunamadı!", "danger")
                return redirect(url_for("dashboard"))
            cursor.close()
            return render_template("dashboard.html", form=form, ogrenci=ogrenci, len_list=0)

    # GET methodu ile dönen return
    return render_template("dashboard.html", form=form)


@app.route("/student/<string:id>", methods=["GET"])
def student(id):
    if request.method == 'GET':
        cursor = mysql.connection.cursor()
        sorgu = "Select * from student where id=%s"
        result = cursor.execute(sorgu, (id,))
        if result > 0:
            ogrenci = cursor.fetchone()
        else:
            flash("Böyle Bir Öğrenci Bulunamadı!", "danger")
            return redirect(url_for("index"))
        cursor.close()
        return render_template("student.html", ogrenci=ogrenci)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST":
        username = form.username.data
        password_entered = form.password.data

        cursor = mysql.connection.cursor()

        sorgu = "Select * From users where username = %s "

        result = cursor.execute(sorgu, (username,))

        if result > 0:
            data = cursor.fetchone()
            real_password = data["password"]
            if sha256_crypt.verify(password_entered, real_password):
                flash("Başarıyla Giriş Yaptınız!", "success")
                session["logged_in"] = True
                session["username"] = username
                session.permanent = True
                session.modified = True
                return redirect(url_for("dashboard"))
            else:
                flash("Şifreniz Yanlış!", "danger")
                return redirect(url_for("login"))
        else:
            flash("Böyle bir kullanıcı adı bulunmamaktadır!", "danger")
            return redirect(url_for("login"))

    return render_template("login.html", form=form)


@app.route("/logout")
@login_required
def logout():
    session.clear()
    flash("Çıkış Yapıldı!", "success")
    return redirect(url_for("index"))


@app.route("/increase/<string:id>", methods=["GET", "POST"])
@login_required
def increase(id):
    form = SearchForm()
    form.text_area.data = id

    if "," in id:
        liste = id.split(",")
        len_list = len(liste)
        liste = tuple(liste)
        cursor = mysql.connection.cursor()
        sorgu = "UPDATE student SET point=point+5 WHERE id in %s"
        sorgu2 = "SELECT * from student WHERE id in %s"
        cursor.execute(sorgu, (liste,))
        mysql.connection.commit()
        cursor.execute(sorgu2, (liste,))
        ogrenci = cursor.fetchall()
        return render_template("dashboard.html", form=form, ogrenci=ogrenci, len_list=len_list)

    cursor = mysql.connection.cursor()
    sorgu = "UPDATE student SET point=point+5 WHERE id=%s"
    sorgu2 = "SELECT * from student WHERE id=%s"
    cursor.execute(sorgu, (id,))
    mysql.connection.commit()
    cursor.execute(sorgu2, (id,))
    ogrenci = cursor.fetchall()
    return render_template("dashboard.html", form=form, ogrenci=ogrenci, len_list=1)


@app.route("/decrease/<string:id>", methods=["GET", "POST"])
@login_required
def decrease(id):
    form = SearchForm()
    form.text_area.data = id
    if "," in id:
        liste = id.split(",")
        len_list = len(liste)
        liste = tuple(liste)
        cursor = mysql.connection.cursor()
        sorgu = "UPDATE student SET point=point-5 WHERE id in %s"
        sorgu2 = "SELECT * from student WHERE id in %s"
        cursor.execute(sorgu, (liste,))
        mysql.connection.commit()
        cursor.execute(sorgu2, (liste,))
        ogrenci = cursor.fetchall()
        return render_template("dashboard.html", form=form, ogrenci=ogrenci, len_list=len_list)

    cursor = mysql.connection.cursor()
    sorgu = "UPDATE student SET point=point-5 WHERE id=%s"
    sorgu2 = "SELECT * from student WHERE id=%s"
    cursor.execute(sorgu, (id,))
    mysql.connection.commit()
    cursor.execute(sorgu2, (id,))
    ogrenci = cursor.fetchall()
    return render_template("dashboard.html", form=form, ogrenci=ogrenci, len_list=1)


if __name__ == "__main__":
    app.run(debug=True)
