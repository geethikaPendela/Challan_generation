from flask import Flask, render_template, request
import os 
from deeplearning import object_detection
# webserver gateway interface
app = Flask(__name__)

BASE_PATH = os.getcwd()
UPLOAD_PATH = os.path.join(BASE_PATH,'static/upload/')


@app.route('/',methods=['POST','GET'])
def index():
    if request.method == 'POST':
        upload_file = request.files['image_name']
        filename = upload_file.filename
        path_save = os.path.join(UPLOAD_PATH,filename)
        upload_file.save(path_save)
        text_list = object_detection(path_save,filename)
        
        print(text_list)

        return render_template('index.html',upload=True,upload_image=filename,text=text_list,no=len(text_list))

    return render_template('index.html',upload=False)
import bcrypt

# ... (your existing code)

 