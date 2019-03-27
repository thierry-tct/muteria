from flask import Flask, render_template, request
from werkzeug import secure_filename
from werkzeug.datastructures import MultiDict, ImmutableMultiDict

app = Flask(__name__)

@app.route('/editconf')
def student():
   return render_template('student.html')

@app.route('/saveconf',methods = ['POST', 'GET'])
def result():
   if request.method == 'POST':
      result = request.form
      f = request.files['file']
      f.save(secure_filename(f.filename))
      result = MultiDict(result)
      result.add(secure_filename(f.filename), 'file uploaded successfully')
      result = ImmutableMultiDict(result)
      return render_template("result.html",result = result)

if __name__ == '__main__':
   app.run(debug = True)