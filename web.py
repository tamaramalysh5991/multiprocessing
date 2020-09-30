from flask import Flask, render_template

from database import return_db

app = Flask(__name__)


@app.route('/hello/')
@app.route('/hello/<name>')
def show_t(name=None):
    # show the post with the given id, the id is an integer
    return render_template('hello.html', name=name)


@app.route('/')
def show_table():
    data = return_db()
    return render_template('database.html', data=data)


@app.route('/file')
def show_file():
    with open('date.txt', 'r') as f:
        content = f.readlines()
    content = [x.strip() for x in content]
    return render_template('from_file.html', data=content)


if __name__ == "__main__":
    app.run(debug=True)
