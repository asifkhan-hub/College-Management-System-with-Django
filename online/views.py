# views.py

from django.shortcuts import render, get_object_or_404, redirect
from .models import OnlineClass, Session, Attendee
from django.contrib.auth.decorators import login_required

@login_required
def online_class_list(request):
    classes = OnlineClass.objects.all()
    return render(request, 'online/class_list.html', {'classes': classes})

@login_required
def class_detail(request, class_id):
    online_class = get_object_or_404(OnlineClass, id=class_id)
    sessions = Session.objects.filter(online_class=online_class)
    return render(request, 'online/class_detail.html', {'online_class': online_class, 'sessions': sessions})

@login_required
def session_detail(request, session_id):
    session = get_object_or_404(Session, id=session_id)
    attendees = Attendee.objects.filter(session=session)
    return render(request, 'online/session_detail.html', {'session': session, 'attendees': attendees})

@login_required
def attend_session(request, session_id):
    session = get_object_or_404(Session, id=session_id)
    attendee, created = Attendee.objects.get_or_create(user=request.user, session=session)
    if not created:
        attendee.attended = True
        attendee.save()
    return redirect('session_detail', session_id=session_id)
