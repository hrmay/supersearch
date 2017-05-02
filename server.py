import os
from flask import Flask, render_template, request, redirect, url_for, session
import MySQLdb, utils
import psycopg2
import psycopg2.extras

app = Flask(__name__)

app.secret_key = os.urandom(24).encode('hex')

def connectToDB():
    connectionString = 'dbname=session user=postgres password=password host=localhost'
    try:
        return psycopg2.connect(connectionString)
    except:
        print("Can't connect to database.")

@app.route('/', methods=['GET', 'POST'])
def mainIndex():
    conn = connectToDB()
    cur = conn.cursor()
    
    if 'username' in session:
        user = session['username']
    else:
        user = ''
    queryType = 'None'
    if 'user' in session:
        print('User: ' + session['user'])
    rows = []
    # if user typed in a post ...
    if request.method == 'POST':
        search = {'term': "%" + request.form['search'] + "%"}
        print(search)
        if 'username' in session:
            search['joinzip1'] = " JOIN users ON (movies.zip = users.zipcode)"
            search['joinzip2'] = " JOIN users ON (stores.zip = users.zipcode)"
            search['zip1'] = " WHERE movies.zip = (SELECT users.zipcode WHERE users.username = '" + session['username'] + "')"
            search['zip2'] = " AND stores.zip = (SELECT zipcode WHERE username = '" + session['username'] + "')"
            search['zip3'] = " AND movies.zip = (SELECT users.zipcode WHERE users.username = '" + session['username'] + "')"
        else:
            search['joinzip1'] = ""
            search['joinzip2'] = ""
            search['zip1'] = ""
            search['zip2'] = ""
            search['zip3'] = ""
            
        if search['term'] == '%movies%':
            query = "SELECT * from movies" + search['joinzip1'] + search['zip1'] + ";"
            queryType = 'movies'
            cur.execute(query, search)
        else:
            query = "SELECT * FROM movies" + search['joinzip1'] + " WHERE movie LIKE %(term)s" + search['zip3'] + " ORDER BY movie;"
            queryType = 'movies'
            cur.execute(query, search)
            if cur.rowcount == 0:
                query = "SELECT * FROM stores " + search['joinzip2'] + " WHERE (name LIKE %(term)s OR type LIKE %(term)s)" + search['zip2'] +" ORDER BY name;"
                queryType = 'stores'
                cur.execute(query, search)

        rows = cur.fetchall()
        
        if cur.rowcount == 0:
            queryType = 'none'


    return render_template('index.html', queryType=queryType, results=rows, selectedMenu='Home', user=user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    conn = connectToDB()
    cur = conn.cursor()
    
    # if user typed in a post ...
    if request.method == 'POST':
      print "HI"
      username = request.form['username']
      session['username'] = username

      pw = request.form['pw']
      
      userInfo = {'username':username, 'password':pw}
      
      query = "select * from users WHERE username = %(username)s AND password = %(password)s" 
      print(query)
      cur.execute(query, userInfo)
      if cur.fetchone():
         return redirect(url_for('mainIndex'))
         
    if 'username' in session:
        user = session['username']
    else:
        user = ''
        
    return render_template('login.html', selectedMenu='Login', user=user)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    conn = connectToDB()
    cur = conn.cursor()
    
    if 'username' in session:
        user = session['username']
    else:
        user = ''
    
    menu = 'display'
        
    if request.method == "POST":
        query = {'username':request.form['username'], 'password':request.form['pw'], 'confirm':request.form['conf-pw'], 'zip':request.form['zip']}
        
        if query['password'] == query['confirm']:
            try:
                cur.execute("""INSERT INTO users (username, password, zipcode) VALUES (%(username)s, crypt(%(password)s, gen_salt('bf')), %(zip)s);""", query)
                menu = 'success'
            except:
                print("ERROR executing INSERT")
                print(cur.mogrify("""INSERT INTO users (username, password, zipcode) VALUES (%(username)s, crypt(%(password)s, gen_salt('bf')), %(zip)s);""", query))
                conn.rollback();
                menu = 'failure'
            conn.commit()
        else:
            menu = 'failure'
        
        
    
    return render_template('signup.html', selectedMenu='Sign Up', user=user, menu = menu)

if __name__ == '__main__':
    app.run(host=os.getenv('IP', '0.0.0.0'), port=int(os.getenv('PORT', 8080)), debug=True)
