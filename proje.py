# Google Authenticator Kütüphanesi
import pyotp

from flask import Flask, render_template, redirect, url_for, session, request
from flask.helpers import flash
from flask_wtf import FlaskForm
from flask_sqlalchemy import SQLAlchemy
from wtforms import Form, StringField, PasswordField, SubmitField, validators
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
    submit = SubmitField("Ara")


# Flask app konfigürasyonları
app = Flask(__name__)
app.secret_key = "k!asdlLdkfjpS0FD*fsad"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////data.db'
app.permanent_session_lifetime = timedelta(minutes=20)


db = SQLAlchemy(app)


class student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String)
    lastname = db.Column(db.String)
    point = db.Column(db.Integer)


class users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String)
    firstname = db.Column(db.String)
    lastname = db.Column(db.String)
    email = db.Column(db.String)
    secret_key = db.Column(db.String)


@app.route("/", methods=["GET", "POST"])
def index():
    form = SearchForm()
    if form.validate_on_submit():
        id = form.text_area.data
        return redirect(url_for("detail", id=id))
    else:
        return render_template("index.html", form=form)


@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    form = SearchForm()
    if form.validate_on_submit():
        id = form.text_area.data
        return redirect("dashboard_detail/{}".format(id))

    # GET methodu ile dönen return
    return render_template("dashboard.html", form=form)


@app.route("/dashboard_detail/<string:id>", methods=["GET", "POST"])
@login_required
def dashboard_detail(id):
    if " " in id:
        liste = id.split(" ")
        liste = tuple(liste)
        ogrenci_list = student.query.filter(student.id.in_(liste)).all()
        return render_template("dashboard_detail.html", ogrenci_list=ogrenci_list, id=id)
    else:
        ogrenci = student.query.filter_by(id=id).first()
        return render_template("dashboard_detail.html", ogrenci=ogrenci)


@app.route("/detail/<string:id>", methods=["GET"])
def detail(id):
    if request.method == 'GET':
        ogrenci = student.query.filter_by(id=id).first()
        if ogrenci == None:
            flash("Böyle bir öğrenci bulunmamaktadır!", "danger")
            return redirect(url_for("index"))
        else:
            return render_template("detail.html", ogrenci=ogrenci)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST":
        username = form.username.data
        password_entered = form.password.data
        sorgu = users.query.filter_by(username=username).first()
        if sorgu != None:
            totp = pyotp.TOTP(sorgu.secret_key)
            if totp.verify(password_entered):
                flash("Başarıyla Giriş Yaptınız!", "success")
                session["logged_in"] = True
                session["username"] = username
                """session.permanent = True
                session.modified = True"""
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


@app.route("/increase/<string:id>", methods=["GET"])
@login_required
def increase(id):
    if " " in id:
        liste = id.split(" ")
        liste = tuple(liste)
        ogrenci_list = student.query.filter(student.id.in_(liste)).all()
        for i in ogrenci_list:
            i.point += 5
        db.session.commit()
        return redirect("/dashboard_detail/{}".format(id))

    ogrenci = student.query.filter_by(id=id).first()
    ogrenci.point += 5
    db.session.commit()
    return redirect("/dashboard_detail/{}".format(id))


@app.route("/decrease/<string:id>", methods=["GET"])
@login_required
def decrease(id):
    if " " in id:
        liste = id.split(" ")
        liste = tuple(liste)
        ogrenci_list = student.query.filter(student.id.in_(liste)).all()
        for i in ogrenci_list:
            i.point -= 5
        db.session.commit()
        return redirect("/dashboard_detail/{}".format(id))

    ogrenci = student.query.filter_by(id=id).first()
    ogrenci.point -= 5
    db.session.commit()
    return redirect("/dashboard_detail/{}".format(id))

@app.route("/leaderboard", methods=["GET"])
def leaderboard():
    ogrenci = student.query.order_by(student.point.desc()).limit(10)
    return render_template("leaderboard.html",ogrenci=ogrenci)

if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)
