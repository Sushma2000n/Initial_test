from datetime import datetime
from bson.json_util import dumps
from flask import Flask, render_template, request, redirect, url_for,session,flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_socketio import SocketIO, join_room, leave_room
from pymongo.errors import DuplicateKeyError
from functools import wraps
import time

import pandas as pd
import os
from csv import writer
import random

from db import get_user, save_user, save_room, add_room_members, get_rooms_for_user, get_room, is_room_member, \
    get_room_members, is_room_admin, update_room, remove_room_members, save_message, get_messages

app = Flask(__name__)
app.secret_key = "sfdjkafnk"
socketio = SocketIO(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)


#Questions
data=pd.read_csv('bm.csv')
records=data.to_records(index=False)
result = list(records)
q1=random.choice(result)
q2=random.choice(result)
coding=pd.read_csv('coding.csv')
coding_records=coding.to_records(index=False)
code_result = list(coding_records)
q3=random.choice(code_result)
q4=random.choice(code_result)
current=pd.read_csv('ca.csv')
current_records=current.to_records(index=False)
current_result = list(current_records)
q5=random.choice(current_result)
q6=random.choice(current_result)

# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap

@app.route('/')
def home():
    rooms = []
    if current_user.is_authenticated:
        rooms = get_rooms_for_user(current_user.username)
    return render_template("index.html", rooms=rooms)

@app.route('/testing')
def testing():
    return render_template('registration.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    message = ''
    if request.method == 'POST':
        username = request.form.get('username')
        password_input = request.form.get('password')
        user = get_user(username)

        if user and user.check_password(password_input):
            login_user(user)
            return redirect(url_for('home'))
        else:
            message = 'Failed to login!'
    return render_template('login1.html', message=message)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    message = ''
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        usn = request.form.get('usn')
        name = request.form.get('name')
        branch = request.form.get('branch')
        try:
            save_user(username, email, password,usn,name,branch)
            return redirect(url_for('login'))
        except DuplicateKeyError:
            message = "User already exists!"
    return render_template('registration.html', message=message)

#Homepage
@app.route('/home')
def homes():
    return render_template('homepage1.html')


@app.route("/logout/")
@login_required
def logout():
    logout_user()
    session.clear()
    flash("Successfully Logged out!!!")
    return redirect(url_for('home'))

@app.route('/test')
@login_required
def test():  
        # with open('answer.csv', 'a+', newline='') as write_obj:
        #     csv_writer = writer(write_obj)
        #     csv_writer.writerow(ours)
   
    return render_template('quiz2.html',name="poorna",q1=q1,q2=q2,q3=q3,q4=q4,q5=q5,q6=q6,q7=q4,q8=q4,q9=q4,q10=q4)

@app.route('/answer',methods=['GET','POST'])
@login_required
def answer():
    if request.method == "POST":
        qes1=request.form.get('q1')
        qes2=request.form.get('q2')
        qes3=request.form.get('q3')
        qes4=request.form.get('q4')
        qes5=request.form.get('q5')
        qes6=request.form.get('q6')
        qes7=request.form.get('q7')
        qes8=request.form.get('q8')
        qes9=request.form.get('q9')
        qes10=request.form.get('q10')
        points=0
        if (q1[6]==qes1):
            points=points+10
        if (q2[6]==qes2):
            points=points+10
        if (q3[6]==qes3):
            points=points+10
        if (q4[6]==qes4):
            points=points+10
        if (q1[6]==qes1):
            points=points+10
        if (q1[6]==qes1):
            points=points+10
        if (q1[6]==qes1):
            points=points+10
        if (q1[6]==qes1):
            points=points+10
        if (q1[6]==qes1):
            points=points+10
        if (q1[6]==qes1):
            points=points+10
        if (q1[6]==qes1):
            points=points+10
        
        name=current_user.username
        points = str(points)
        with open('answer.csv','r+') as f:
            myDataList=f.readlines()
            nameList=[]
            for line in myDataList:
                entry = line.split(',') 
                nameList.append('added') 
            
            if name not in nameList:
                now =datetime.now()
                dtString=now.strftime('%H:%M:%S')
                f.writelines(f'\n{name},{dtString},{points}')
            
        
        return redirect('/score')
    return "Not working yet"

@app.route('/create-room/', methods=['GET', 'POST'])
@is_logged_in
def create_room():
    message = ''
    if request.method == 'POST':
        room_name = request.form.get('room_name')
        usernames = [username.strip() for username in request.form.get('members').split(',')]

        if len(room_name) and len(usernames):
            room_id = save_room(room_name, current_user.username)
            if current_user.username in usernames:
                usernames.remove(current_user.username)
            add_room_members(room_id, room_name, usernames, current_user.username)
            return redirect(url_for('view_room', room_id=room_id))
        else:
            message = "Failed to create room"
    return render_template('create_room.html', message=message)


@app.route('/rooms/<room_id>/edit', methods=['GET', 'POST'])
@is_logged_in
def edit_room(room_id):
    room = get_room(room_id)
    if room and is_room_admin(room_id, current_user.username):
        existing_room_members = [member['_id']['username'] for member in get_room_members(room_id)]
        room_members_str = ",".join(existing_room_members)
        message = ''
        if request.method == 'POST':
            room_name = request.form.get('room_name')
            room['name'] = room_name
            update_room(room_id, room_name)

            new_members = [username.strip() for username in request.form.get('members').split(',')]
            members_to_add = list(set(new_members) - set(existing_room_members))
            members_to_remove = list(set(existing_room_members) - set(new_members))
            if len(members_to_add):
                add_room_members(room_id, room_name, members_to_add, current_user.username)
            if len(members_to_remove):
                remove_room_members(room_id, members_to_remove)
            message = 'Room edited successfully'
            room_members_str = ",".join(new_members)
        return render_template('edit_room.html', room=room, room_members_str=room_members_str, message=message)
    else:
        return "Room not found", 404


@app.route('/rooms/<room_id>/')
@is_logged_in
def view_room(room_id):
    room = get_room(room_id)
    if room and is_room_member(room_id, current_user.username):
        room_members = get_room_members(room_id)
        messages = get_messages(room_id)
        return render_template('view_room.html', username=current_user.username, room=room, room_members=room_members,
                               messages=messages)
    else:
        return "Room not found", 404

#Result
@app.route('/score')
def score():
    score=pd.read_csv('answer.csv')
    score1=score.to_records(index=False)
    result = list(score1)
    # lists1 = list.sort_values("marks", ascending=True)
    return render_template('score.html',results=result)

@app.route('/rooms/<room_id>/messages/')
@is_logged_in
def get_older_messages(room_id):
    room = get_room(room_id)
    if room and is_room_member(room_id, current_user.username):
        page = int(request.args.get('page', 0))
        messages = get_messages(room_id, page)
        return dumps(messages)
    else:
        return "Room not found", 404


@socketio.on('send_message')
def handle_send_message_event(data):
    app.logger.info("{} has sent message to the room {}: {}".format(data['username'],
                                                                    data['room'],
                                                                    data['message']))
    data['created_at'] = datetime.now().strftime("%d %b, %H:%M")
    save_message(data['room'], data['message'], data['username'])
    socketio.emit('receive_message', data, room=data['room'])


@socketio.on('join_room')
def handle_join_room_event(data):
    app.logger.info("{} has joined the room {}".format(data['username'], data['room']))
    join_room(data['room'])
    socketio.emit('join_room_announcement', data, room=data['room'])


@socketio.on('leave_room')
def handle_leave_room_event(data):
    app.logger.info("{} has left the room {}".format(data['username'], data['room']))
    leave_room(data['room'])
    socketio.emit('leave_room_announcement', data, room=data['room'])


@login_manager.user_loader
def load_user(username):
    return get_user(username)


if __name__ == '__main__':
    socketio.run(app, debug=True)
