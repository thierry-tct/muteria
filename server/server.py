"""
- A project is a configuration (can be created, modified/updated, deleted)
- It is possible to switch between projects (every project operation needs)
   the project unique id as part of the url
- Each user operation need the user id as part of the url 
   (for nor default value)
"""

from flask import Flask, render_template, request, session, url_for
from werkzeug import secure_filename
from werkzeug.datastructures import MultiDict, ImmutableMultiDict

import argparse

app = Flask(__name__)

@app.route("/")
def homepage():
   return render_template("home.html")

@app.route('/createproject/<projectname>')
def create_project():
   return render_template('createproject.html')

@app.route('/openproject/<projectname>')
def open_project():
   return render_template('configurations.html')

@app.route('/saveproject/<projectname>', methods = ['POST', 'GET'])
def save_config():
   pass #TODO
   # Make sure that the config is sound and save (with backup)
   if request.method == 'POST':
      result = request.form
      f = request.files['file']
      f.save(secure_filename(f.filename))
      result = MultiDict(result)
      result.add(secure_filename(f.filename), 'file uploaded successfully')
      result = ImmutableMultiDict(result)

@app.route('/execute/<projectname>', methods = ['POST', 'GET'])
def execute_with_saved_conf():
   return render_template("progress.html",result = result)

@app.route('/configurations/<projectname>', methods = ['POST', 'GET'])
def execution_configurations(projectname):
   return render_template("configurations.html")

@app.route('/progress/<projectname>', methods = ['POST', 'GET'])
def execution_progress(projectname):
   return render_template("progress.html",result = result)

@app.route('/report/<projectname>', methods = ['POST', 'GET'])
def execution_report(projectname):
   return render_template("report.html",result = result)

@app.route('/info/<projectname>', methods = ['POST', 'GET'])
def execution_info(projectname):
   return render_template("info.html",result = result)

if __name__ == '__main__':
   parser = argparse.ArgumentParser()
   parser.add_argument('--host', default='127.0.0.1', \
                        help="host to use (set to 0.0.0.0 for public access)")
   parser.add_argument('-p', '--port', type=int, default=5000, \
                                                            help="port to use")
   parser.add_argument('-d', '--debug', action="store_true", \
                                       help="enable debug mode for the server")
   args = parser.parse_args()

   # Start the app
   app.run(host=args.host, port=args.port, debug=args.debug)