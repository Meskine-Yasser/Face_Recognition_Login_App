import os
import pickle
import sqlite3
import tkinter as tk
from pathlib import Path
from tkinter import *
from tkinter import messagebox
import cv2
import bcrypt
import face_recognition
import numpy as np
from PIL import Image, ImageTk


# class: Dlib Face Unlock
# Purpose: This class will update the encoded known face if the directory has changed
# as well as encoding a face from a live feed to compare the face to allow the facial recognition
# to be integrated into the system
# Methods: ID
def hash_password(password: str):
    # Hash the password
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return hashed_password.decode('utf-8')


def add_user(username, password, email, student_id):
    # Connect to the database (creates the file if it doesn't exist)
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    # Create the table if it doesn't exist
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        username text,
        password text,
        email text,
        student_id text
    )""")

    # Check if the username has already been taken
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    user = c.fetchone()
    if user:
        # Close the connection
        conn.close()
        # Return False if the username has already been taken
        return False

    # Hash the password
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    # Insert the user
    c.execute("""INSERT INTO users (username, password, email, student_id)
        VALUES (?,?,?,?)""", (username, hashed_password.decode('utf-8'), email, student_id))
    # Save (commit) the changes
    conn.commit()
    # Close the connection
    conn.close()
    # Return True if the user was added successfully
    return True


def check_user(username, password):
    # Connect to the database
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    # Check if the user exists
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    user = c.fetchone()
    # Close the connection
    conn.close()
    # Return False if the user doesn't exist
    if not user:
        return False, False, None
    # Check if the password is correct
    if bcrypt.checkpw(password.encode('utf-8'), user[1].encode('utf-8')):
        return True, user[2], user[3]
    # Return False if the password is incorrect
    return False, None, None


class Dlib_Face_Unlock:
    # When the Dlib Face Unlock Class is first initialised it will check if the employee photos directory has been updated
    # if an update has occurred either someone deleting their face from the system or someone adding their face to the system
    # the face will then be encoded and saved to the encoded pickle file
    def __init__(self):
        # this is to detect if the directory is found or not
        try:
            # this will open the existing pickle file to load in the encoded faces of the users who has sign up for the service
            with open(r'C:\Users\p\Desktop\FACE-LOGIN-2-main\labels.pickle', 'rb') as self.f:
                self.og_labels = pickle.load(self.f)
        # error checking
        except FileNotFoundError:
            # allowing me to known that their was no file found
            print("No label.pickle file detected, will create required pickle files")

        # this will be used to for selecting the photos
        self.current_id = 0
        # creating a blank ids dictionary
        self.labels_ids = {}
        # this is the directory where all the users are stored
        self.BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.image_dir = os.path.join(self.BASE_DIR, 'images')
        for self.root, self.dirs, self.files in os.walk(self.image_dir):
            # checking each folder in the images directory
            for self.file in self.files:
                # looking for any png or jpg files of the users
                if self.file.endswith('png') or self.file.endswith('jpg'):
                    # getting the folder name, as the name of the folder will be the user
                    self.path = os.path.join(self.root, self.file)
                    self.label = os.path.basename(os.path.dirname(self.path)).replace(' ', '-').lower()
                    if not self.label in self.labels_ids:
                        # adding the user into the labels_id dictionary
                        self.labels_ids[self.label] = self.current_id
                        self.current_id += 1
                        self.id = self.labels_ids[self.label]

        # print(self.labels_ids)
        # this is compare the new label ids to the old label ids dictionary seeing if their has been any new users or old users
        # being added to the system, if there is no change then nothing will happen
        self.og_labels = 0
        if self.labels_ids != self.og_labels:
            # if the dictionary change then the new dictionary will be dump into the pickle file
            with open('labels.pickle', 'wb') as self.file:
                pickle.dump(self.labels_ids, self.file)

            self.known_faces = []
            for self.i in self.labels_ids:
                # Get number of images of a person
                noOfImgs = len([filename for filename in os.listdir('images/' + self.i)
                                if os.path.isfile(os.path.join('images/' + self.i, filename))])
                print(noOfImgs)
                for imgNo in range(1, (noOfImgs + 1)):
                    self.directory = os.path.join(self.image_dir, self.i, str(imgNo) + '.png')
                    self.img = face_recognition.load_image_file(self.directory)
                    self.img_encoding = face_recognition.face_encodings(self.img)[0]
                    self.known_faces.append([self.i, self.img_encoding])
            # print(self.known_faces)
            print("No Of Imgs" + str(len(self.known_faces)))
            with open('KnownFace.pickle', 'wb') as self.known_faces_file:
                pickle.dump(self.known_faces, self.known_faces_file)
        else:
            with open(r'C:\Users\p\Desktop\FACE-LOGIN-2-main\KnownFace.pickle', 'rb') as self.faces_file:
                self.known_faces = pickle.load(self.faces_file)
            print(self.known_faces)

    # Method: ID
    # Purpose:This is method will be used to create a live feed .i.e turning on the devices camera
    # then the live feed will be used to get an image of the user and then encode the users face
    # once the users face has been encoded then it will be compared to in the known faces
    # therefore identifying the user
    # the live will lag because it's taking many pictures per second to identify the user as accurately as possible
    def ID(self):
        # turning on the camera to get a photo of the user frame by frame

        self.cap = cv2.VideoCapture(0)
        cv2.namedWindow("Scanning...")
        # setting the running variable to be true to allow me to known if the face recognition is running
        self.running = True
        self.face_names = []
        while self.running == True:
            # taking a photo of the frame from the camera
            self.ret, self.frame = self.cap.read()
            cv2.imshow("Scanning...", self.frame)
            k = cv2.waitKey(7000)
            if k % 256 == 32:
                continue
            # SPACE pressed
            # waiting for 3 seconds
            # resizing the frame so that the face recognition module can read it
            self.small_frame = cv2.resize(self.frame, (0, 0), fx=0.5, fy=0.5)
            # converting the image into black and white
            self.rgb_small_frame = self.small_frame[:, :, ::-1]
            if self.running:
                # searching the black and white image for a face
                self.face_locations = face_recognition.face_locations(self.frame)

                # if self.face_locations == []:
                #     Dlib_Face_Unlock.ID(self)
                # it will then encode the face into a matrix
                self.face_encodings = face_recognition.face_encodings(self.frame, self.face_locations)
                # creating a names list to append the users identify into
                self.face_names = []
                # looping through the face_encoding that the system made
                for self.face_encoding in self.face_encodings:
                    # looping though the known_faces dictionary
                    for self.face in self.known_faces:
                        # using the compare face method in the face recognition module
                        self.matches = face_recognition.compare_faces([self.face[1]], self.face_encoding)
                        print(self.matches)
                        self.name = 'Unknown'
                        # compare the distances of the encoded faces
                        self.face_distances = face_recognition.face_distance([self.face[1]], self.face_encoding)
                        # uses the numpy module to compare the distance to get the best match
                        self.best_match = np.argmin(self.face_distances)
                        print(self.best_match)
                        print('This is the match in best match ', self.matches[self.best_match])
                        if self.matches[self.best_match] == True:
                            self.running = False
                            self.face_names.append(self.face[0])
                            break
            print("The best match(es) is " + str(self.face_names))
            self.cap.release()
            cv2.destroyAllWindows()
            break
        return self.face_names


def register():
    # Get the username, password, email, ID entered by the user
    username = name.get()
    password = passwordE.get()
    email = loggedInUserEmail.get()
    ID = loggedInUserStudentID.get()

    add_user(username, password, email, ID)

    # Create images folder
    if not os.path.exists("images"):
        os.makedirs("images")
    # Create folder of person (IF NOT EXISTS) in the images folder
    Path("images/" + name.get()).mkdir(parents=True, exist_ok=True)
    # Obtain the number of photos already in the folder
    numberOfFile = len([filename for filename in os.listdir('images/' + name.get())
                        if os.path.isfile(os.path.join('images/' + name.get(), filename))])
    # Add 1 because we start at 1
    numberOfFile += 1
    # Take a photo code
    cam = cv2.VideoCapture(0)

    cv2.namedWindow("Press SPACE to Capture...")

    while True:
        ret, frame = cam.read()
        cv2.imshow("Press SPACE to Capture...", frame)
        if not ret:
            break
        k = cv2.waitKey(1)

        if k % 256 == 27:
            # ESC pressed
            print("Escape hit, Closing...")
            cam.release()
            cv2.destroyAllWindows()
            break
        elif k % 256 == 32:
            # SPACE pressed
            print("Space hit, Capturing...")
            img_name = str(numberOfFile) + ".png"
            cv2.imwrite(img_name, frame)
            print("{} written!".format(img_name))
            os.replace(str(numberOfFile) + ".png", "images/" + name.get().lower() + "/" + str(numberOfFile) + ".png")
            cam.release()
            cv2.destroyAllWindows()
            break
    # Insert the username and password into the database
    raiseFrame(mainFrame)


def login():
    username = username_entry.get()
    password = password_entry.get()

    # Check if the entered username and password are valid

    user, email, student_id = check_user(username, password)
    if user is False and email is False:
        messagebox.showerror("Error", "User doesn't exist, Please Register First.")
        return
    elif user is False and email is None:
        messagebox.showerror("Error", "Incorrect Password, Please Check Again.")
        return

    # After someone has registered, the face scanner needs to load again with the new face
    print("Scanning...")
    dfu = Dlib_Face_Unlock()
    # Will return the user's name as a list, will return an empty list if no matches
    face_user = dfu.ID()
    if face_user == []:
        messagebox.showerror("Sorry", "Face Not Recognised")
        return
    if face_user[0] != username:
        messagebox.showerror("Sorry", "Face does not match with entered username")
        return

    loggedInUser.set(username)
    loggedInUserEmail.set(email)
    loggedInUserStudentID.set(student_id)
    raiseFrame(userMenuFrame)
    showMainMenu()


def logout():
    # After someone has registered, the face scanner needs to load again with the new face
    #dfu = Dlib_Face_Unlock()
    # Will return the user's name as a list, will return an empty list if no matches
    # user = dfu.ID()
    # if user == []:
    #     messagebox.showerror("Sorry", "Face Not Detected")
    #     return
    loggedOutUser.set("")
    raiseFrame(mainFrame)


# Raise Functions
def raiseFrame(frame):
    frame.tkraise()


def regFrameRaiseFrame():
    raiseFrame(regFrame)


def mainFrameRaise():
    raiseFrame(mainFrame)


def loginFrameRaiseFrame():
    raiseFrame(loginFrame)


# Tkinter
root = tk.Tk()
root.geometry("1100x900")
root.resizable(width=False, height=False)
root.title("STUDENT APP")
root.configure(background='#1f93ff')
root['background'] = '#1f93ff'

# Frames
mainFrame = tk.Frame(root)
regFrame = tk.Frame(root)
userMenuFrame = tk.Frame(root)
loginFrame = tk.Frame(root)

frame = tk.Frame(root)

# Define Frame List
frameList = [mainFrame, regFrame, userMenuFrame, loginFrame]
# Configure all Frames
for frame in frameList:
    frame.grid(row=0, column=0, sticky='news')
    frame.configure(bg='#1f93ff')
#


# Tkinter Vars
# Stores user's name when registering
username_entry = tk.StringVar()
password_entry = tk.StringVar()
# Stores user's name when they have logged in
loggedInUser = tk.StringVar()
loggedOutUser = tk.StringVar()

# Main Frame

tk.Label(mainFrame, text="STUDENT APP", font=("Times New Roman", 70), foreground="white", bg="#856ff8").grid(
    row=1, column=3, padx=240, pady=100)
loginButton = tk.Button(mainFrame, text="Login", bg="white", font=("Arial", 30), command=loginFrameRaiseFrame)
loginButton.grid(row=3, column=3, pady=100)

regButton = tk.Button(mainFrame, text="Register", command=regFrameRaiseFrame, bg="white", font=("Arial", 30))
regButton.grid(row=4, column=3)

############
# Login Frame

tk.Label(loginFrame, text="STUDENT LOGIN", font=("Times New Roman", 70), foreground="white", bg="#856ff8").grid(row=1,
                                                                                                                column=2,
                                                                                                                padx=10,
                                                                                                                pady=100)

tk.Label(loginFrame, text="Username: ", font=("Times New Roman", 30), foreground="white", bg="#856ff8").grid(row=2,
                                                                                                             column=1,
                                                                                                             padx=50,
                                                                                                             pady=50)

username_Entry = tk.Entry(loginFrame, textvariable=username_entry, font=("Arial", 30))
username_Entry.grid(row=2, column=2, padx=10, pady=50)
tk.Label(loginFrame, text="Password: ", font=("Times New Roman", 30), foreground="white", bg="#856ff8").grid(row=3,
                                                                                                             column=1,
                                                                                                             padx=50,
                                                                                                             pady=50)
password_Entry = tk.Entry(loginFrame, textvariable=password_entry, font=("Arial", 30), show="*")
password_Entry.grid(row=3, column=2, padx=10, pady=50)

loginSubmitButton = tk.Button(loginFrame, text="Login", command=login, bg="white", font=("Arial", 30))
loginSubmitButton.grid(row=5, column=2, padx=30, pady=30)

BackButton = tk.Button(loginFrame, text="Back", command=mainFrameRaise, bg="red", font=("Arial", 30))
BackButton.grid(row=6, column=2, padx=30, pady=30)

###########
# Register Frame
tk.Label(regFrame, text="STUDENT REGISTER", font=("Times New Roman", 56), foreground="white", bg="#856ff8").grid(row=1,
                                                                                                                 column=2,
                                                                                                                 padx=0,
                                                                                                                 pady=80)

tk.Label(regFrame, text="Name: ", font=("Times New Roman", 30), foreground="white", bg="#856ff8").grid(row=2, column=1,
                                                                                                       padx=50, pady=20)

name = tk.StringVar()
nameEntry = tk.Entry(regFrame, textvariable=name, font=("Arial", 30)).grid(row=2, column=2, padx=10, pady=20)

tk.Label(regFrame, text="Password: ", font=("Times New Roman", 30), foreground="white", bg="#856ff8").grid(row=3,
                                                                                                           column=1,
                                                                                                           padx=50,
                                                                                                           pady=20)

passwordE = tk.StringVar()
passwordEntry = tk.Entry(regFrame, textvariable=passwordE, font=("Arial", 30), show='*').grid(row=3, column=2, padx=10,
                                                                                              pady=50)
tk.Label(regFrame, text="Email: ", font=("Times New Roman", 30), foreground="white", bg="#856ff8").grid(row=4,
                                                                                                        column=1,
                                                                                                        padx=50,
                                                                                                        pady=20)
loggedInUserEmail = tk.StringVar()
EmailEntry = tk.Entry(regFrame, textvariable=loggedInUserEmail, font=("Arial", 30)).grid(row=4, column=2, padx=10,
                                                                                         pady=50)
tk.Label(regFrame, text="Student ID: ", font=("Times New Roman", 30), foreground="white", bg="#856ff8").grid(row=5,
                                                                                                             column=1,
                                                                                                             padx=50,
                                                                                                             pady=20)
loggedInUserStudentID = tk.StringVar()
IDEntry = tk.Entry(regFrame, textvariable=loggedInUserStudentID, font=("Arial", 30)).grid(row=5, column=2, padx=10,
                                                                                          pady=20)

registerButton = tk.Button(regFrame, text="Register", command=register, bg="white", font=("Arial", 30))
registerButton.grid(row=6, column=2, padx=30, pady=30)

BackButton = tk.Button(regFrame, text="Back", command=mainFrameRaise, bg="red", font=("Arial", 30))
BackButton.grid(row=6, column=1, padx=30, pady=30)


##########
# Main Menu


def showMainMenu():
    ta = tk.Label(userMenuFrame, text="STUDENT PROFILE", font=("Times New Roman", 40), foreground="white", bg="#1f93ff")
    ta.grid(row=0, column=2, padx=1, pady=1)
    tb = tk.Label(userMenuFrame, text="Hello, ", font=("Arial", 30), foreground="white", bg="#1f93ff")
    tb.grid(row=2, column=1, padx=30, pady=20)
    la = tk.Label(userMenuFrame, textvariable=loggedInUser, font=("Arial", 30), foreground="red", bg="#1f93ff")
    la.grid(row=2, column=2, padx=1, pady=20)

    td = tk.Label(userMenuFrame, text="Email: ", font=("Arial", 30), foreground="white", bg="#1f93ff")
    td.grid(row=3, column=1, padx=30, pady=20)
    ld = tk.Label(userMenuFrame, textvariable=loggedInUserEmail, font=("Arial", 30), foreground="red", bg="#1f93ff")
    ld.grid(row=3, column=2, padx=1, pady=20)
    te = tk.Label(userMenuFrame, text="Student ID: ", font=("Arial", 30), foreground="white", bg="#1f93ff")
    te.grid(row=4, column=1, padx=30, pady=20)
    le = tk.Label(userMenuFrame, textvariable=loggedInUserStudentID, font=("Arial", 30), foreground="red", bg="#1f93ff")
    le.grid(row=4, column=2, padx=1, pady=20)

    profile_pic = Image.open("images/" + loggedInUser.get() + "/1.png")
    profile_pic = profile_pic.resize((int(profile_pic.width / 2), int(profile_pic.height / 2)))
    photo = ImageTk.PhotoImage(profile_pic)

    label_pic = tk.Label(userMenuFrame, image=photo)
    label_pic.image = photo
    label_pic.grid(row=0, column=4, padx=15, pady=20)
    tc = tk.Button(userMenuFrame, text="Logout", font=("Arial", 30), bg="red", command=mainFrameRaise)
    tc.grid(row=5, column=4, padx=50, pady=50)


dfu = Dlib_Face_Unlock()
raiseFrame(mainFrame)

root.mainloop()
