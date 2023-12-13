import os
from flask import Flask, render_template, redirect, request
from database import Database

app = Flask(__name__)

db = Database(os.environ['DB_URI'], os.environ['DB_USER'],
              os.environ['DB_PASSWORD'])

@app.route('/')
def index():
	return render_template('index.html')


@app.route('/people')
def people_all():
	return render_template('people_list.html', people=db.get_people_all())


@app.route('/people/male')
def people_male():
	return render_template('people_list.html', people=db.get_people_by_gender('Mężczyzna'))


@app.route('/people/female')
def people_female():
	return render_template('people_list.html', people=db.get_people_by_gender('Kobieta'))


@app.route('/people/alive')
def people_alive():
	return render_template('people_list.html', people=db.get_people_alive())


@app.route('/people/dead')
def people_dead():
	return render_template('people_list.html', people=db.get_people_dead())


@app.route('/people/alone')
def people_alone():
	return render_template('people_list.html', people=db.get_people_alone())


@app.route('/people/<id>')
def people(id):
	return render_template('people.html',
													person=db.get_person(id),
													mother=db.get_mother(id),
													father=db.get_father(id))


@app.route('/people/add', methods=('GET', 'POST'))
def people_add():
	if request.method == 'POST':
		first_name = request.form['firstName']
		last_name = request.form['lastName']
		gender = request.form['gender']
		birth_date = request.form['birthDate']
		death_date = request.form['deathDate']
		new_id = db.add_person(first_name, last_name, gender, birth_date, death_date)
		return redirect('/people/' + new_id)

	return render_template('people_add.html')


@app.route('/people/<id>/edit', methods=('GET', 'POST'))
def people_edit(id):
	if request.method == 'POST':
		first_name = request.form['firstName']
		last_name = request.form['lastName']
		gender = request.form['gender']
		birth_date = request.form['birthDate']
		death_date = request.form['deathDate']
		db.edit_person(id, first_name, last_name, gender, birth_date, death_date)
		return redirect('/people/' + id)

	return render_template('people_edit.html', person=db.get_person(id))


@app.route('/people/<id>/delete')
def people_delete(id):
	db.delete_person(id)
	return redirect('/people')


@app.route('/people/<id>/marry', methods=('GET', 'POST'))
def people_marry(id):
	if request.method == 'POST':
		marriage_date = request.form['marriageDate']
		marriage_end_date = request.form['marriageEndDate']
		other_id = request.form['otherID']
		db.marry_person(id, marriage_date, marriage_end_date, other_id)
		return redirect('/people/' + id + '/marriages')

	return render_template('people_marry.html',
													person=db.get_person(id),
													people=db.get_people_except(id))


@app.route('/people/<id>/marriages')
def people_marriages(id):
	return render_template('people_marriages.html',
													person=db.get_person(id),
													marriages=db.get_marriages(id))


@app.route('/people/<person_id>/marriages/<marriage_id>/delete')
def people_marriages_delete(person_id, marriage_id):
	db.delete_marriage(marriage_id)
	return redirect('/people/' + person_id + '/marriages')


@app.route('/people/<id>/mother', methods=('GET', 'POST'))
def people_mother(id):
	if request.method == 'POST':
		other_id = request.form['otherID']
		db.add_mother(id, other_id)
		return redirect('/people/' + id)

	return render_template('people_mother.html',
													person=db.get_person(id),
													people=db.get_people_except(id))


@app.route('/people/<id>/mother/delete')
def people_mother_delete(id):
	db.delete_mother(id)
	return redirect('/people/' + id)


@app.route('/people/<id>/father', methods=('GET', 'POST'))
def people_father(id):
	if request.method == 'POST':
		other_id = request.form['otherID']
		db.add_father(id, other_id)
		return redirect('/people/' + id)

	return render_template('people_father.html',
													person=db.get_person(id),
													people=db.get_people_except(id))


@app.route('/people/<id>/father/delete')
def people_father_delete(id):
	db.delete_father(id)
	return redirect('/people/' + id)


