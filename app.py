from flask import Flask,render_template,request,redirect,url_for
from models import db,Event,Resource,event_resource_allocation
from flask_migrate import Migrate
from datetime import datetime,date


app=Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI']='mysql+pymysql://root:root1234@localhost/flask_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False

db.init_app(app)
migrate=Migrate(app,db)

@app.route('/')
def home_page():
    return render_template('home.html')

@app.route('/events')
def event_page():
    all_events=Event.query.all()
    return render_template('events.html',all_events=all_events,now=datetime.now())

@app.route('/events_create', methods=['GET','POST'])
def create_event_page():
    today=date.today()
    time=datetime.now()
    resources=Resource.query.all()
    event_all=Event.query.all()
    if request.method=='POST':
        title=request.form.get('event_name')
        start_time=request.form.get('event_date')
        end_time=request.form.get('event_enddate')
        description=request.form.get('description')
        resource_id=int(request.form.get('resource_id'))
        start_t=datetime.fromisoformat(start_time)
        end_t=datetime.fromisoformat(end_time)
        if start_t.time()<time.time() and start_t.date()<= today:
            error_message="Start time must be in the future."
            return render_template('event_create.html', error_message=error_message,resources=resources)
        if end_t < start_t:
            error_message="End time must be after start time."
            return render_template('event_create.html', error_message=error_message,resources=resources)
        overlap = db.session.query(Event).join(
            event_resource_allocation,
            event_resource_allocation.event_id == Event.event_id
        ).filter(
            event_resource_allocation.resource_id == resource_id,
            Event.start_time <= end_t,
            Event.end_time >= start_t
        ).first()
        
        if overlap:
            return render_template('event_create.html', error_message="Already have event on Time",resources=resources)
        
        existing_event=Event.query.filter_by(
            title=title,
            start_time=start_time,
            end_time=end_time
            ).first()
        if existing_event:
            error_message="Already exists."
            return render_template('event_create.html', error_message=error_message,resources=resources)
        new_event=Event(
            title=title,
            start_time=start_time,
            end_time=end_time,
            description=description
        )
        db.session.add(new_event)
        db.session.commit()
        resource=request.form.get('resource_id')
        new_allocation=event_resource_allocation(   
            event_id=new_event.event_id,
            resource_id=resource
        )
        db.session.add(new_allocation)
        db.session.commit()

        return redirect(url_for('event_page'))

    return render_template('event_create.html',resources=resources)

@app.route('/resource')
def resource_page():
    all_resources=Resource.query.all()
    return render_template('resource.html',all_resources=all_resources)


@app.route('/resource_create', methods=['GET','POST'])
def create_resource_page():
    if request.method=='POST':
        resource_name=request.form.get('resource_name')
        resource_type=request.form.get('resource_type')

        exist_resource=Resource.query.filter_by(
            resource_name=resource_name,
            resource_type=resource_type
        ).first()
        if exist_resource:
            error_message="Resource already exists."
            return render_template('resource_create.html', error_message=error_message)
        
        new_resource=Resource(
            resource_name=resource_name,
            resource_type=resource_type
        )
        db.session.add(new_resource)
        db.session.commit()
        error_message="Resource created successfully."
        return redirect(url_for('resource_page'))

    return render_template('resource_create.html')

@app.route('/allocation')
def allocation_page():
    all_allocations=db.session.query(event_resource_allocation,Event,Resource).join(Event, event_resource_allocation.event_id==Event.event_id).join(Resource, event_resource_allocation.resource_id==Resource.resource_id).all()
    return render_template('allocation.html',all_allocations=all_allocations)

@app.route('/edits/<int:event_id>', methods=['GET','POST'])
def edit_event_page(event_id):
    today=date.today()
    time=datetime.now()
    resource=Resource.query.all()
    event=Event.query.get(event_id)
    if request.method=='POST':
        event.title=request.form.get('title')
        event.start_time=request.form.get('start_time')
        event.end_time=request.form.get('end_time')
        start_t=datetime.fromisoformat(event.start_time)
        end_t=datetime.fromisoformat(event.end_time)
        if start_t.time()<time.time() and start_t.date()<= today:
            error_message="Start time must be in the future."
            return render_template('edits.html',event=event,error_message=error_message,resources=resource)
        if end_t < start_t:
            error_message="End time must be after start time."
            return render_template('edits.html',event=event ,error_message=error_message,resources=resource)
        event.description=request.form.get('description')
        check_existing=Event.query.filter_by(
            title=event.title,
            start_time=event.start_time,
            end_time=event.end_time,
            description=event.description
        ).first()
        if check_existing and check_existing.event_id != event.event_id:
            error_message="An event with these details already exists."
            return render_template('edits.html', event=event, error_message=error_message,resources=resource)
        
        db.session.commit()
        return redirect(url_for('event_page'))
    return render_template('edits.html', event=event,resources=resource)

@app.route('/report')
def report_page():
    resource=Resource.query.all()
    report=db.session.query(event_resource_allocation,Event,Resource).join(Event, event_resource_allocation.event_id==Event.event_id).join(Resource, event_resource_allocation.resource_id==Resource.resource_id).all()
    return render_template('report.html',resource=resource,report=report,today=datetime.today())
@app.route('/resource_update/<int:id>', methods=['GET','POST'])
def update_resource_page(id):
    resource=Resource.query.get(id)
    if request.method=='POST':
        resource__name=request.form.get('resource_name')
        resource__type=request.form.get('resource_type')
        check_existing=Resource.query.filter_by(
            resource_name=resource__name,
            resource_type=resource__type
        ).first()
        if check_existing and check_existing.resource_id != resource.resource_id:
            error_message="A resource with these details already exists."
            return render_template('resource_update.html', resource=resource, error_message=error_message)
        resource.resource_name=resource__name
        resource.resource_type=resource__type
        db.session.commit()
        return redirect(url_for('resource_page'))
    return render_template('resource_update.html', resource=resource)
if __name__=="__main__":
    app.run(debug=True)