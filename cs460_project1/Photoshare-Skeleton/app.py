######################################
# author ben lawson <balawson@bu.edu> 
# Edited by: Craig Einstein <einstein@bu.edu>
######################################
# Some code adapted from 
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################

import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
import flask.ext.login as flask_login
import time
from collections import Counter
from itertools import groupby
from collections import OrderedDict
#for image uploading
from werkzeug import secure_filename
import os, base64

current_date = time.strftime("%Y-%m-%d")
mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string'  # Change this!

#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'cs460database'
app.config['MYSQL_DATABASE_DB'] = 'photoshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from Users") 
users = cursor.fetchall()

def getUserList():
	cursor = conn.cursor()
	cursor.execute("SELECT email from Users") 
	return cursor.fetchall()

def getAllUsers():
	cursor = conn.cursor()
	cursor.execute("SELECT user_id, first_name, last_name from Users")
	return cursor.fetchall()

class User(flask_login.UserMixin):
	pass

@login_manager.user_loader
def user_loader(email):
	users = getUserList()
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	return user

@login_manager.request_loader
def request_loader(request):
	users = getUserList()
	email = request.form.get('email')
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	cursor = mysql.connect().cursor()
	cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
	data = cursor.fetchall()
	pwd = str(data[0][0] )
	user.is_authenticated = request.form['password'] == pwd 
	return user

'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''

@app.route('/show', methods = ['GET'])
@flask_login.login_required
def show():
    if request.method == 'GET':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		return render_template('photoStore.html', photos=getUsersPhotos(uid) )
	#The method is GET so we return a  HTML form to upload the a photo.

@app.route('/login', methods=['GET', 'POST'])
def login():
	if flask.request.method == 'GET':
		return '''
			   <form action='login' method='POST'>
				<input type='text' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
				<input type='submit' name='submit'></input>
			   </form></br>
		   <a href='/'>Home</a>
			   '''
	#The request method is POST (page is recieving data)
	email = flask.request.form['email']
	cursor = conn.cursor()
	#check if email is registered
	if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
		data = cursor.fetchall()
		pwd = str(data[0][0] )
		if flask.request.form['password'] == pwd:
			user = User()
			user.id = email
			flask_login.login_user(user) #okay login in user
			return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file

	#information did not match
	return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"

@app.route('/logout')
def logout():
	flask_login.logout_user()
	return render_template('hello.html', message='Logged out') 

@login_manager.unauthorized_handler
def unauthorized_handler():
	return render_template('unauth.html') 

#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register", methods=['GET'])
def register():
	return render_template('register.html', supress='True')  

@app.route("/register", methods=['POST'])
def register_user():
	try:
		email=request.form.get('email')
		password=request.form.get('password')
	except:
		print "couldn't find all tokens" #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('register'))
	fname = request.form.get('first name')
	lname = request.form.get('last name')
	dob = request.form.get('birthday')
	gender = request.form.get('gender')
	hometown = request.form.get('hometown')
	cursor = conn.cursor()
	test =  isEmailUnique(email) and None not in [password,fname,lname,dob,gender,hometown]
	if test:
		print cursor.execute("INSERT INTO Users (email, password,first_name,last_name,date_of_birth,gender,hometown) VALUES ('{0}', '{1}','{2}','{3}','{4}','{5}','{6}')".format(email, password,fname,lname,dob,gender,hometown))
		conn.commit()
		#log user in
		user = User()
		user.id = email
		flask_login.login_user(user)
		return render_template('hello.html', name=lname, message='Account Created!')
	else:
		print "couldn't find all tokens"
		return flask.redirect(flask.url_for('register'))

def getUserInfo(name):
	cursor = conn.cursor()
	cursor.execute("SELECT * from Users WHERE first_name = '{0}' or last_name = '{1}'".format(name,name))
	return cursor.fetchall()

def getAlbumList(uid):
    cursor = conn.cursor()
    cursor.execute("SELECT name, album_creationDate, user_id from Albums WHERE user_id = '{0}'".format(uid))
    return cursor.fetchall()

def getPhotoInAlbum(uid, name):
	cursor = conn.cursor()
	cursor.execute("SELECT p.imgdata, p.picture_id, p.caption from Pictures p, Albums a WHERE p.belong_to = a.name and p.user_id = a.user_id and a.name = '{0}' and a.user_id = '{1}'".format(name, uid))
	return cursor.fetchall()

def getUsersPhotos(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]

def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id  FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]

def getUserNameFromId(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT last_name  FROM Users WHERE user_id = '{0}'".format(uid))
	return cursor.fetchone()[0]

def getAllComments():
	cursor = conn.corsor()
	cursor.execute("SELECT picture_id, comment_text FROM Comments")
	return cursor.fetchall() 

def getPictureComments(picture_id):
	cursor = conn.cursor()
	cursor.execute("SELECT picture_id, comment_text FROM Comments WHERE picture_id = '{0}'".format(picture_id))
	return cursor.fetchall() 

def getTopFiveTags(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT DISTINCT t.tag_text, COUNT(t.tag_text) as count FROM Pictures p, PictureTags t WHERE p.picture_id = t.picture_id AND p.user_id = '{0}' GROUP BY t.tag_text ORDER BY count DESC".format(uid))
	TagList = cursor.fetchall()
	return TagList[:5]

def isEmailUnique(email):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)): 
		#this means there are greater than zero entries with that email
		return False
	else:
		return True

def isAlbumNameUnique(name, uid):
	cursor = conn.cursor()
	if cursor.execute("SELECT A.name FROM Albums A WHERE A.name = '{0}' AND A.user_id = '{1}';".format(name, uid)): 
		#this means there are greater than zero entries with that email
		return False
	else:
		return True
#end login code

def getFriendList(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT * FROM Users u, Friendship f WHERE f.user1 = '{0}' AND f.user2 = u.user_id".format(uid))
	return cursor.fetchall()

def getFriendInfo(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT * FROM Users WHERE user_id = '{0}'".format(uid))
	return cursor.fetchone()

def getPhotoByTag(tag):
	cursor = conn.cursor()
	cursor.execute("SELECT p.imgdata, p.picture_id, p.caption From Pictures p, PictureTags t WHERE p.picture_id = t.picture_id and tag_text = '{0}'".format(tag))
	return cursor.fetchall()

def getPhotoByTagList(tagList):
	cursor = conn.cursor()
	photos = []
	for tag in tagList:
		photos.append(set(getPhotoByTag(tag)))
	return set.intersection(*photos)		

def getAllPhotoTags(pid):
	cursor = conn.cursor()
	cursor.execute("SELECT tag_text From PictureTags t WHERE t.picture_id = '{0}'".format(pid))
	return cursor.fetchall()

# def getAllRelatedTags(photoSet):
# 	tags = []
# 	for photo in photoSet:
# 		tags = tags + list(getAllPhotoTags(photo[1]))
# 	return tags  
def getRankingTags(tagList):
	queryhead = "SELECT tag_text FROM PictureTags WHERE "  
	querytail = " GROUP BY tag_text ORDER BY COUNT(picture_id) DESC"
	subquery = "picture_id IN (SELECT picture_id FROM PictureTags WHERE tag_text = '" + tagList[0] + "')"
	for tag in tagList:
		subquery = subquery + " AND picture_id IN (SELECT picture_id FROM PictureTags WHERE tag_text = '" + tag + "')"
	query = queryhead + subquery + querytail
	cursor = conn.cursor()
	cursor.execute(query)
	return cursor.fetchall()

@app.route('/tags')
def showTags():
	pid = request.args['photoid']
	tags = [str(i[0]) for i in getAllPhotoTags(pid)]
	return ' '.join(tags)


@app.route('/show/youMayAlsoLike')
@flask_login.login_required
def youMayAlsoLike ():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	tags =  getTopFiveTags(uid)
	tagList = [str(i[0]) for i in tags]
	photos = []
	cursor = conn.cursor()
	if len(tagList) < 5:
		return "Your tag number is less than 5, add more tags to see our recommendation"
	else: 
		tagList = tagList[:5]
		query = "SELECT p.imgdata, t.picture_id, p.caption FROM Pictures p, PictureTags t WHERE p.user_id <> '{0}' and p.picture_id = t.picture_id AND (t.tag_text = '{1}' OR t.tag_text = '{2}' OR t.tag_text = '{3}' OR t.tag_text = '{4}' OR t.tag_text = '{5}') GROUP BY t.picture_id ORDER BY Count(t.tag_text) DESC".format(uid, tagList[0],tagList[1], tagList[2], tagList[3], tagList[4])
		cursor.execute(query)
	photos = cursor.fetchall()
	print tagList
	return render_template('photoView.html', photos = photos, message = 'Photos that you may also interest in') 

# @app.route('/tag_management/tag_racommendation', methods = ['GET'])
# def tagRecommedation():
# 	return render_template ('enterTags.html')

@app.route('/tag_management/tag_racommendation', methods = ['GET', 'POST'])
def tagSearch():
	if request.method == 'POST':
		tags = request.form.get('description')
		tagList = tags.split()
		# photos = getPhotoByTagList(tagList)
		# ls = getAllRelatedTags(photos)
		# ls = [x for t in ls for x in t]
		diff = lambda l1,l2: [x for x in l1 if x not in l2]
		raw = list(getRankingTags(tagList))
		raw = [x for t in raw for x in t]
		result = diff(raw, tagList)
		# ls = diff(ls, tagList)
		# counts = Counter(ls)
		# reportedTags = [ [k,]*v for k,v in counts.items()]
		# reportedTags.sort(key = len, reverse = True)
		# reportedTags = sum(reportedTags, [])
		# reportedTags = list(OrderedDict.fromkeys(reportedTags))
		return render_template('tagRecommendation.html', message = 'Tags you may also interest in', tags = result)
	else:
		 return render_template ('enterTags.html')

@app.route('/profile')
@flask_login.login_required
def protected():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	lname = getUserNameFromId(uid)
	return render_template('hello.html', name=lname, message="Here's your profile")

@app.route('/friendList')
@flask_login.login_required
def friendList():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	lname = getUserNameFromId(uid)
	return render_template('friendinfo.html', message = 'Hello ' + lname, searchList = getFriendList(uid))

@app.route('/friendProfile', methods = ['GET'])
@flask_login.login_required
def enterProfile():
	info = request.args['info']
	lname = getUserNameFromId(info)
	profile = getFriendInfo(info)
	albums = getAlbumList(info)
	return render_template('profile.html', profile = profile, albums = albums, message = 'profile of ' + lname)

#begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML 
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		lname = getUserNameFromId(uid)
		imgfile = request.files['photo']
		caption = request.form.get('caption')
		print caption
		album = request.form.get('album')
		photo_data = base64.standard_b64encode(imgfile.read())
		cursor = conn.cursor()
		cursor.execute("INSERT INTO Pictures (imgdata, belong_to,user_id, caption) VALUES ('{0}', '{1}', '{2}', '{3}')".format(photo_data,album,uid, caption))
		conn.commit()		
		return render_template('hello.html',name=lname, message='Photo uploaded!',photos=getUsersPhotos(uid))
	# The method is GET so we return a  HTML form to upload the a photo.
	else:
		uid = getUserIdFromEmail(flask_login.current_user.id)
		return render_template('upload.html', albums = getAlbumList(uid))
	# if request.method == 'GET':
		# return 'test hello'
#end photo uploading code 

@app.route("/friendsearch", methods=['GET','POST'])
@flask_login.login_required
def search_friend():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		lname = getUserNameFromId(uid)
		friend = request.form.get('friend')
		print lname
		print friend
		result = getUserInfo(friend)
		if not result:
			return render_template('hello.html', name = lname, message = 'Sorry, no result matches your search')
		else:
			return render_template('friendList.html', message = 'Here is your search result', searchList = result) 
	else:
		return render_template('searchFriends.html')


@app.route("/photosearch", methods=['GET','POST'])
def photoSearch():
	if request.method == 'POST':
		tag = request.form.get('description')
		photos = []
		if (' ' in tag) == True:
			tagList = tag.split()
			for word in tagList:
				photos.append(getPhotoByTag(word))
			photos = reduce(lambda x,y: x+y,photos)
			photos = list(set(photos))
		else:
			photos = getPhotoByTag(tag) 
		return render_template('photoView.html', message = 'all photos with tag: ' + tag, photos = photos)
	else:
		return render_template('photoSearch.html')


@app.route("/tag_management", methods=['GET'])		
@flask_login.login_required
def tagManagement():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	photos = getUsersPhotos(uid)
	return render_template('tagManagement.html', photos = photos)

@app.route("/tag_management/add_tag", methods=['GET', 'POST'])		
@flask_login.login_required
def add_tag():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		lname = getUserNameFromId(uid)
		tag = request.form.get('tag')
		pid = request.args['pid']
		print pid
		cursor = conn.cursor()
		try:
			cursor.execute("INSERT INTO PictureTags(picture_id, tag_text) VALUES ('{0}', '{1}')".format(pid, tag))
			conn.commit()
			return render_template('hello.html', name=lname, message = 'Tag created!')
		except:
			return render_template('hello.html', name=lname, message = 'Cannot create the same tag!')
	else:
		return render_template('hello.html')

def getUidFromPhoto(pid):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id From Pictures WHERE picture_id = '{0}'".format(pid))
	return cursor.fetchone()[0]

def countLike(pid):
	cursor = conn.cursor()
	cursor.execute("SELECT COUNT(*) From LikeFunction WHERE picture_id = '{0}'".format(pid))
	return cursor.fetchone()[0]

@app.route("/howmanyLike", methods=['GET'])
def showHowmanyLike():
	pid = request.args['photoid']
	numLike = countLike(pid)
	return 'currently ' + str(numLike) + ' people like this photo' 

@app.route("/showComments", methods=['GET'])
def showAllComments():
	pid = request.args['photoid']
	comments = getPictureComments(pid)
	return render_template('comment.html', comments = comments)


def contributionScore(uid):
	cursor1 = conn.cursor()
	cursor1.execute("SELECT COUNT(*) From Comments WHERE owner_id = '{0}'".format(uid))
	cursor2 = conn.cursor()
	cursor2.execute("SELECT COUNT(*) From Pictures WHERE user_id = '{0}'".format(uid))
	score = cursor1.fetchone()[0] + cursor2.fetchone()[0]
	return score

def getAllTags():
	cursor = conn.cursor()
	cursor.execute("SELECT Distinct tag_text From PictureTags")
	return cursor.fetchall()

def getUserPhotoByTags(uid, tag):
	cursor = conn.cursor()
	cursor.execute("SELECT p.imgdata, p.picture_id, p.caption From Pictures p, PictureTags t, Users u WHERE p.user_id = u.user_id AND p.picture_id = t.picture_id and tag_text = '{0}' AND p.user_id = '{1}'".format(tag, uid))
	return cursor.fetchall()


def getTagPopularity(tag):
	cursor = conn.cursor()
	cursor.execute("SELECT COUNT(*) picture_id From PictureTags WHERE tag_text = '{0}'".format(tag))
	return cursor.fetchone()[0]

@app.route('/tag_management/allTags', methods=['GET'])
def showAllTags():
	tagList = getAllTags()
	return render_template('showTags.html', message = 'All Current Tags', tags = tagList)

@app.route('/tag_management/allTags/viewPhoto', methods=['GET'])
def viewPhotobyTag():
	tag = request.args['tag']
	photos = getPhotoByTag(tag)
	return render_template('photoView.html', message = 'all photos with tag: ' + tag, photos = photos)

@app.route('/tag_management/allTags/viewYourPhoto', methods=['GET'])
@flask_login.login_required
def viewUserPhotoByTags():
	tag = request.args['tag2']
	uid = getUserIdFromEmail(flask_login.current_user.id)
	photos = getUserPhotoByTags(uid, tag)
	return render_template('photoView.html', message = 'Your photos with tag: ' + tag, photos = photos)

@app.route('/like', methods=['GET'])
@flask_login.login_required
def addLike():
	pid = request.args['photoid']
	uid = getUserIdFromEmail(flask_login.current_user.id)
	try:
		cursor = conn.cursor()
		cursor.execute("INSERT INTO LikeFunction(user_id, picture_id) VALUES ('{0}', '{1}')".format(uid,pid))
		conn.commit()
		return 'Add Like successful!'				
	except:
	 	return 'cannot Like same photo twice'

@app.route('/tag_management/popularTags', methods=['GET'])
def showPopularTags():
	tagList = getAllTags()
	tags = []
	score = 0
	for tag in tagList:
		score = getTagPopularity(tag[0])
		tags.append((tag[0], score))
	tags.sort(key=lambda x: x[1])
	tags.reverse()
	if len(tags)>10:
		tags = tags[:10]
	return render_template('showTags.html', message = 'Top 10 most popupar tags', tags = tags)


@app.route('/add_comment', methods=['GET', 'POST'])
def comment():
	pid = request.args['pid']
	owner_id = getUidFromPhoto(pid)
	cursor = conn.cursor()
	print owner_id
	comment = request.form.get('description')
	try:
		uid = getUserIdFromEmail(flask_login.current_user.id)
		lname = getUserNameFromId(uid)
		print uid
		if uid != owner_id:
			cursor.execute("INSERT INTO Comments (comment_text, picture_id, owner_id, comment_date) VALUES ('{0}', '{1}', '{2}','{3}')".format(comment,pid,uid,current_date))
			conn.commit()
			return render_template('photoView.html', name=lname, message='Thanks for your comment!')
		else:
			return render_template('photoView.html', name=lname, message='Sorry, cannot comment your own photo.')
	except:
		cursor.execute("INSERT INTO Comments (comment_text, picture_id, comment_date) VALUES ('{0}', '{1}', '{2}')".format(comment,pid,current_date))
		conn.commit()
		return render_template('photoView.html', message='Thanks for your comment!')

@app.route('/userList', methods=['GET', 'POST'])
def userList():
	users = getAllUsers()
	return render_template('userList.html', users = users)

#default page  
@app.route("/", methods=['GET'])
def hello():
	return render_template('hello.html', message='Welecome to Photoshare')

@app.route('/create_an_album', methods=['GET','POST'])
@flask_login.login_required
def create_an_album():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	if request.method == 'POST':
		album_name = request.form.get('album_name')
		if isAlbumNameUnique(album_name, uid) == False:
			return render_template('repeatedAlbumName.html')
		uid = getUserIdFromEmail(flask_login.current_user.id)
		lname = getUserNameFromId(uid)
		print album_name #will show in the shell
		cursor = conn.cursor()
		cursor.execute("INSERT INTO Albums (name, user_id, album_creationDate) VALUES ('{0}', '{1}', '{2}')".format(album_name,uid,current_date))
		conn.commit()
		return render_template('hello.html', name=lname, message='Album created!', photos=getUsersPhotos(uid) )
    	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		return render_template('createAlbum.html')


@app.route('/albums', methods=['GET','POST'])
@flask_login.login_required
def albums():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	lname = getUserNameFromId(uid)
	return render_template('albumStore.html', name=lname, albums = getAlbumList(uid))

@app.route('/albums/deleteAlbum', methods=['GET'])
@flask_login.login_required
def deleteAlbum():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	lname = getUserNameFromId(uid)
	name = request.args['name']
	cursor = conn.cursor()
	cursor.execute("DELETE FROM Albums WHERE name = '{0}' and user_id = '{1}'".format(name, uid))
	conn.commit()
	return render_template('albumStore.html', name=lname, message="your album " + name + " has been deleted successfully!", albums = getAlbumList(uid))

@app.route('/deletePhoto', methods=['GET'])
@flask_login.login_required
def deletePhoto():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	lname = getUserNameFromId(uid)
	pid = request.args['pid']
	cursor = conn.cursor()
	cursor.execute("DELETE FROM Pictures WHERE picture_id = '{0}'".format(pid))
	conn.commit()
	return render_template('photoStore.html', name=lname, message="your photo has been deleted successfully!", photos = getUsersPhotos(uid))

@app.route('/albums/enteralbum', methods=['GET','POST'])
@flask_login.login_required
def enterAlbum():
	uid = request.args['uid']
	lname = getUserNameFromId(getUserIdFromEmail(flask_login.current_user.id))
	name = request.args['name']
	return render_template('photoStore.html', photos=getPhotoInAlbum(uid, name),name = lname, message = 'All photo in album: ' + name)

@app.route('/photoview', methods=['GET','POST'])
# @flask_login.login_required
def viewFriendsPhoto():
	uid = request.args['uid']
	lname = getUserNameFromId(uid)
	name = request.args['name']
	return render_template('photoView.html', photos=getPhotoInAlbum(uid, name),name = lname, message = 'All photo in album: ' + name)

@app.route('/viewProfile', methods=['GET'])
def viewProfile():
	uid = request.args['uid']
	return render_template('profile.html', albums = getAlbumList(uid))

@app.route('/userList/topTenUsers', methods=['GET'])
def topTenUsers():
	users = getAllUsers()
	userList = []
	uids = []
	scores = 0
	i=0
	for user in users:
		uids.append(user[0])
	for uid in uids:
		scores = contributionScore(uid)
		userList.append(users[i] + (scores, ))
		i = i + 1
	output = sorted(userList, key=lambda x: x[-1])
	output.reverse()
	if len(users)>10:
		return render_template('top10.html', users = output[:10])
	else:
		return render_template('top10.html', users = output)

@app.route('/friendsearch/add_friend', methods=['GET'])
@flask_login.login_required
def add_friend():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	lname = getUserNameFromId(uid)
	info = request.args['info']
	if uid != info:
		try:
			cursor = conn.cursor()
			cursor.execute("INSERT INTO Friendship VALUES ('{0}', '{1}')".format(uid, info))
			cursor.execute("INSERT INTO Friendship VALUES ('{0}', '{1}')".format(info, uid))
			conn.commit()
			return render_template('hello.html', name = lname, message = 'Friend added successfully!', friendList = getFriendList(uid))
		except:
			return render_template('hello.html', name = lname, message = 'Friend already added', friendList = getFriendList(uid))
	else:
		return render_template('hello.html', name = lname, message = 'Cannot add yourself as friend')

if __name__ == "__main__":
	#this is invoked when in the shell  you run 
	#$ python app.py 
	app.run(port=5000, debug=True)
