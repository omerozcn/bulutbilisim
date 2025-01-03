from flask import Flask, render_template ,request, redirect, session, flash, url_for 
import base64
from werkzeug.utils import secure_filename
import os
import sqlite3
app = Flask(__name__)
database_dir = "db.db"

app.secret_key = os.urandom(24) 

def create_connection():
    return sqlite3.connect(database_dir)

@app.route("/")
def anasayfa():
    return render_template("index.html",title="Home")

@app.route("/hakkinda")
def hakkinda():
    return render_template("hakkinda.html",title="About") 

@app.route("/admindestek", methods=["GET"])
def admindestek():
    connection = create_connection()
    cursor = connection.cursor()

    # Tüm destek biletlerini al
    cursor.execute("""
        SELECT id, description, photo, user_id FROM Biletler
    """)
    tickets = cursor.fetchall()
    
    connection.close()

    # Fotoğraf verilerini base64 formatına çevir
    tickets_with_photo_data = []
    for ticket in tickets:
        ticket_id, description, photo, user_id = ticket
        if photo:
            photo_data = base64.b64encode(photo).decode('utf-8')  # Base64 kodlama
        else:
            photo_data = None
        tickets_with_photo_data.append((ticket_id, description, photo_data, user_id))

    return render_template("admindestek.html", tickets=tickets_with_photo_data)



@app.route("/girisyap", methods=["GET", "POST"])
def girisyap():
    if request.method == "POST":
        username = request.form["inp_username"]
        password = request.form["inp_password"]

        connection = create_connection()
        cursor = connection.cursor()

        # Kullanıcı bilgilerini kontrol et ve user_id al
        cursor.execute("""
            SELECT id FROM Users
            WHERE username = ? AND password = ?
        """, (username, password))
        result = cursor.fetchone()

        connection.close()

        if result:  # Kullanıcı bulunduysa
            user_id = result[0]
            session["user_id"] = user_id
            session.permanent = True

            if user_id == 1:  # Eğer user_id 1 ise admin sayfasına yönlendir
                return redirect("/admindestek")
            else:
                return redirect("/dashboard")
        else:
            # Hatalı kullanıcı adı veya şifre
            flash("Kullanıcı adı veya şifre yanlış.", "error")
            return redirect("/")

    else:  # GET isteği
        return render_template("giris.html", title="Giriş Yap")


@app.route("/dashboard", methods=["GET"])
def dashboard():
    # Kullanıcı ID'sini alıyoruz
    user_id = session.get("user_id")
    
    if user_id:
        connection = create_connection()
        cursor = connection.cursor()
        
        cursor.execute("""
            SELECT description, photo FROM Biletler WHERE user_id = ? ORDER BY id DESC LIMIT 1
        """, (user_id,))
        ticket = cursor.fetchone()
        
        connection.close()
        
        if ticket:
            description, photo = ticket
            # Fotoğraf varsa, base64 formatında döndürülmesini sağlıyoruz
            if photo:
                photo_data = base64.b64encode(photo).decode('utf-8')
                return render_template("dashboard.html", description=description, photo_data=photo_data)
            else:
                return render_template("dashboard.html", description=description, photo_data=None)
        else:
            flash("Henüz bir destek bileti göndermediniz.", "warning")
            return redirect("/destek")
    else:
        flash("Kullanıcı oturumu açık değil.", "error")
        return redirect("/girisyap")
    

@app.route("/destek", methods=["GET", "POST"])
def destek():
    if request.method == "POST":
        description = request.form.get("inp_description")
        photo = request.files["photo"]

        user_id = session.get("user_id")
        
        if user_id:
            if photo:
                photo_data = photo.read()
            else:
                photo_data = None

            connection = create_connection()
            cursor = connection.cursor()

            cursor.execute("""
                INSERT INTO Biletler (photo, description, user_id)
                VALUES (?, ?, ?)
            """, (photo_data, description, user_id))

            connection.commit()
            connection.close()

            flash("Destek bileti başarıyla gönderildi.", "success")
            return redirect("/")  # Başarıyla gönderildikten sonra yönlendirme yapılmalı
        else:
            flash("Kullanıcı oturumu açık değil.", "error")
            return redirect("/girisyap")  # Oturum açılmamışsa giriş sayfasına yönlendirme

    return render_template("destek.html", title="Destek Gönder")


@app.route("/kayitol",methods=["GET","POST"])
def kayitol():
    if request.method == "POST":
        username = request.form["inp_username"]
        name = request.form["inp_name"]
        surname = request.form["inp_surname"]
        password = request.form["inp_password"]
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute("""
                       insert into Users
                       (name,surname,username,password)
                       values (?,?,?,?)
                    """, (name,surname,username,password))
        
        connection.commit()
        return redirect("/") # import
    else:
        return render_template("kayitol.html",title="Kayıt ol")

if __name__ == "__main__":
    app.run(host="0.0.0.0",port=6000,debug=True)