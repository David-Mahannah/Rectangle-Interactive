import os
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

possible_file_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.pdf', '.txt']

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def getExtension(obj, typ):
    for i in possible_file_extensions:
        if typ == "user":
            filename = obj.name + "pp" + i
            pth = os.path.join("static", "uploads", "profile_pictures", filename)
            
        elif typ == "post":
            filename = str(obj.id) + i
            pth = os.path.join("static", "uploads", "posts", filename)

        elif typ == "event_post":
            filename = str(obj.id) + i
            pth = os.path.join("static", "uploads", "event_posts", filename)

        else:
            raise TypeError("Invalid type: ", type(obj), ". Should be either User type or Post type", type(Post))
        
        if os.path.isfile(pth):
            return i

    return None

def deleteImage(reference_obj, typ):
    ''' Deletes the image associated with post/user '''
    extension = getExtension(reference_obj, typ)
    if extension:
        if typ == "user":
            filename = reference_obj.name + "pp" + extension
            os.remove(os.path.join('static', 'uploads', "profile_pictures", filename))
            return True

        elif typ == "post":
            filename = str(reference_obj.id) + extension
            os.remove(os.path.join('static', 'uploads', 'posts', filename))
            return True

        elif typ == "event_post":
            filename = str(reference_obj.id) + extension
            os.remove(os.path.join('static', 'uploads', 'event_posts', filename))
            return True

        else: # Neither
            raise AttributeError(" Invalid reference_obj type. Expected User/Post Got: ", type(reference_obj))
    else:
        print("No Image to remove")
        return False
    
def createImage(reference_object, file, typ):
    if allowed_file(file.filename):
        filename = secure_filename(file.filename)
        extension = filename.rsplit('.', 1)[1].lower()      
        deleteImage(reference_object, typ)

        if typ == "user":
            filename = reference_object.name + "pp" + "." + extension
            file.save(os.path.join("static", "uploads", "profile_pictures", filename))

        elif typ == "post":
            filename = str(reference_object.id) + "." + extension
            file.save(os.path.join("static", "uploads", "posts", filename))    

        elif typ == "event_post":
             filename = str(reference_object.id) + "." + extension
             file.save(os.path.join("static", "uploads", "event_posts", filename))

        else: # Neither
            raise AttributeError(" Invalid reference_obj type. Expected User/Post/EventPost ")
