To make this aplications, for backEnd i used python (flask) and for fronEnd mainly html + JS, for database simple sqlite

Explanain of all the code and logic behind the code:

first, we start with databse.
There are 3 tables (entities)
1.  Users
2.  Tasks
3.  user_tasks

Users and Tasks are quite simple, there both have primary AUTOINCREMENT key, which then will be used later on

Why not use just these two? because then you would have so called "many-to-many relationship" which is almost all the time bad

Sometimes it helps to visualize the problem, so here we go

  We create a user:
  id = 1, name = john, password = 1234

  Then we create a task:
  id = 1, user_id = 1, title = "app", description = "make a task manager app"

  each task belongs to only one user
  if we want to assign the same task to multiple users, we must duplicate the task
  duplicated data so it can be harder to maintain

 users:
(1, john, 1234)
(2, mary, 4321)

tasks
(1, APP, make a task manager app)

Then we assign tasks using a junction table:

user_tasks:
(1, user_id=1, task_id=1, completed=0)
(2, user_id=2, task_id=1, completed=1)

Surely more on this topic you will learn somewhere else, but just to be clear why are we using the 3rd table

also, in flask using sqli you need to put 

conn = sqlite3.connect("users.db")
 conn.execute("""some code
 """)
this tells the app to execute the code to the database
the you need comit and close

conn.commit()
conn.close()

Main app

basicly all things you need to learn to make proper backend is to understand endpoints

endpoint si later on visile in url and is used for frondend to fetch data from this endpoint

@aplikace.route("/")
def index():
    return render_template("index.html")

("/") - this is the most basic endpoint, mainly used for home page etc.

the we have @aplikace.route("/registration", methods=["GET", "POST"])
def registration():

here we have to optiones, if the endpoint will recive GET, it will just return template - like if you press register button on the home page and then you will be 
"redirected" to different html.

if the endopint recives POST request : the data were send in JSON format and they need to be transformed into python dictionary

JSON will send data in this format 
{
  "id": 1,
  "name": "john",
  "password": "1234"
}
and we need to have python discionary format, which will look like this

user = {
    "id": 1,
    "name": "john",
    "password": "1234"
}

command "data = request.get_json()" will "translate" json to python dictionary

then we use " name = data.get("name") " to get certain data from existing dictionary

name, password will the be inserted in to the databse and create new user

if we need to display message (warning, completed etc.) on the html page, we have to again convert the message to JSON

this will be done be command "jsonify"

send back to frontend.

return jsonify({
    "success": True,
    "message": "Users registred"
})

This sends JSON back to JavaScript, where frontend can read it and display message.

Frontend logic

On frontend we have normal HTML form:

<form id="registrationForm">

but we do not want this form to reload page automatically, so in JS we use:

event.preventDefault();

This stops default html form behavior.

Then we use fetch:

fetch("/registration", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    name: regNameInput.value,
    password: regPasswordInput.value,
    password2: regPasswordInput2.value,
  }),
})

This sends data from inputs to Flask endpoint "/registration".

Important part is JSON.stringify, because JS object has to be converted into JSON before it is send to backend.

Then backend checks:

1. if data exist
2. if name and passwords exist
3. if both passwords are same
4. if username is not already taken

For duplicate username i created function:

def duplicitaJmen(name):

This function checks database if some user with same name already exists.

If user exists, registration will stop.

If everything is correct, user is inserted into database.

Login logic

Login works almost same as registration. Except the data arent begin send to the database, just retrieves it

Frontend sends name and password to endpoint "/login".

Backend then searches database:

SELECT * FROM users WHERE name = ?

Question mark is important, because it protects against SQL injection.
so instead of SELECT * FROM users WHERE name = john
there is SELECT * FROM users WHERE name = ?, (john)

so sql injection cant escape parametrers

Then backend checks:

if user does not exist:
    return error

if password is wrong:
    return error

if password is correct:
    create session

Session/cookies

this one was quite hard for me to understand

Session is used to remember that user is logged in.

we can create cookies/sessions by importing python library and then specify, whidh data they will keep

NEVER store users passwords or other important data, cookies are being heavily used in cyber atacks

  session.permanent = True - you might dont want to have this, because the user will keep being loged in even after refreshing the site
    session["prihlasen"] = True - just for the test
    session["user_id"] = user["id"] - here we are storing users id
    session["user_name"] = user["name"] - here we stoer users name

This means that after login we know which user is currently using the app.

For example in profile endpoint:

if "user_id" not in session:
    return redirect("/login?msg=Not logged")

This means if user is not logged in, he cannot see profile page.

This will be it for our login/register
Creating tasks

Tasks are created only by admin.

First admin opens Admin page.

If user is not logged in, he is send back to login page.

If user is logged in, but his name is not admin, he is also send back.

So only admin can create task for someone.

In Admin.html admin writes:

user
task
description

Then frontend sends these data to backend using POST request.

Backend receives data like this:

data = request.get_json()

Then we take values from data:

user = data.get("user")
task = data.get("task")
desc = data.get("desc")

After that backend checks if user and task exist.

Description is not required, because task can exist even without description.

Then backend tries to find selected user in database:

SELECT id FROM users WHERE name = ?

This is needed because in user_tasks table we do not save username, but user id.

If user is not found, backend returns error.

If user exists, backend first creates new task in tasks table:

INSERT INTO tasks (title, description) VALUES (?, ?)

This creates task itself, but it is not connected to user yet.

After insert we need id of this new task:

id_task = cursor.lastrowid

"lastrowid" gives us id of task which was just created.

Then we insert row into user_tasks table:

INSERT INTO user_tasks (id_user, id_task) VALUES (?, ?)

This connects selected user with selected task.

So the task is now assigned to that user.

Completed is not inserted here, because database has default value 0.

That means new task is automatically not completed.

After that we do:

conn.commit()
conn.close()

commit saves changes into database.

close closes connection.

Then backend sends message back to frontend:

return jsonify({
    "success": True,
    "message": "Task was addes to user"
})

So frontend can display if task was created or if something went wrong.

Simple example:

admin writes:

user = test
task = Clean room
desc = Do it today

Backend finds user test and gets his id.

Then creates task Clean room.

Then connects this task with user test in user_tasks table.

After that, when test logs in and opens profile, he will see this task.

This will be all for this app, its really simple but for the basics, its not bad to try it yourself, GLHF
