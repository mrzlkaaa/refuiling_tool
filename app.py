import os, sys
from flask import render_template, request, redirect, url_for, session
import numpy as np
from db import *
from refuiling import *

UPLOAD_FOLDER = 'input/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route("/home", methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        # name = request.form['name']
        uploaded = request.files['uploaded']
        uploaded.save(os.path.join(app.config['UPLOAD_FOLDER'], uploaded.filename))
        print(url_for('reading_file', file_name = uploaded.filename, ))
        return redirect(url_for('reading_file', file_name = uploaded.filename))
    return render_template('home.html')


@app.route('/proc/<file_name>', methods=['GET', 'POST'])
def reading_file(file_name):
    arr = Average(file_name).average_burnup()
    print(arr)
    if request.method == 'POST':
        print('detected_POST')
        option = request.form['options']
        numbers = request.form['numbers']
        if option == 'fresh':
            new = Fresh(file_name, numbers).refueling()
            print(new)
        elif option == 'swap':
            new = Swap(file_name, numbers).swap()
            print(new)
        session['old_core'] = arr.tolist()
        session['new_core'] = new.tolist()
        return redirect(url_for('core_refueling'))
        # print(option, numbers)

        # return redirect(url_for('refueling', file_name = uploaded.filename))

    return render_template('reading_file.html', burnup = arr)

@app.route('/refueling', methods=['GET', 'POST'])
def core_refueling():
    old_core = np.array(session.get('old_core'))
    new_core = np.array(session.get('new_core'))
    form = RefuelList()
    form.add_existing.choices = [(data.refueling_name, data.refueling_name) for data in RefuelingDB.query.all()]
    print(form.add_existing)
    if request.method == 'POST':
        name = request.form.get('new_refuel')
        data = new_core.tobytes() #* convert to bytes
        desc = request.form.get('description')
        if len(name) == 0:
            name = request.form['add_existing']
            print(name)
            query_refueling = RefuelingDB.query.filter_by(refueling_name=name).first()
            print(type(query_refueling))
            date = query_refueling.date
            add_activity = RefuelingActs(description=desc, data=data, refuel=query_refueling)
            print(add_activity)
            # query_refueling = RefuelingDB.query.filter_by(refueling_name=name).first()
            # print(query_refueling.activities)
            # inst = RefuelingDB(name=name, date=date)
            db.session.add(add_activity)
            db.session.commit()
        else:
            if len(request.form.get('date')) > 0: date = request.form.get('date')
            else: date = datetime.now()
            inst = RefuelingDB(name=name, date=date)
            db.session.add(inst)
            db.session.commit()
        print(name, date)
        # inst = RefuelingDB(name=name, description=desc, date=date, data=data)
        
        # return redirect(url_for('list'))
    return render_template('refueling.html', old_core=old_core, new_core=new_core, form=form)

@app.route('/list')
def list():
    refueling_list = RefuelingDB.query.order_by(RefuelingDB.date).all()
    print(RefuelingDB.query.all())
    return render_template('list.html', list=refueling_list)

@app.route('/detail/<name>', methods=['GET','POST'])
def detail(name):
    print(name)
    refueling_data = RefuelingDB.query.filter_by(refueling_name=name).first()
    core_configuration = np.frombuffer(refueling_data.burnup_data).reshape((6,4))
    print(refueling_data)
    return render_template('detail.html', data=refueling_data, burnup=core_configuration )


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)