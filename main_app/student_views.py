import json
import math
from datetime import datetime

from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import (HttpResponseRedirect, get_object_or_404,
                              redirect, render)
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, date

from .forms import *
from .models import *
from django.core.cache import cache


def student_home(request):
    # Define a cache key for this view
    cache_key = f'student_home_{request.user.id}'
    
    # Attempt to get the rendered template from the cache
    cached_template = cache.get(cache_key)
    
    if cached_template is not None:
        return cached_template

    student = get_object_or_404(Student, admin=request.user)
    total_subject = Subject.objects.filter(course=student.course).count()
    total_attendance = AttendanceReport.objects.filter(student=student).count()
    total_present = AttendanceReport.objects.filter(student=student, status=True).count()

    if total_attendance == 0:  # Avoid DivisionByZero
        percent_absent = percent_present = 0
    else:
        percent_present = math.floor((total_present / total_attendance) * 100)
        percent_absent = math.ceil(100 - percent_present)

    subject_name = []
    data_present = []
    data_absent = []
    subjects = Subject.objects.filter(course=student.course)

    for subject in subjects:
        attendance = Attendance.objects.filter(subject=subject)
        present_count = AttendanceReport.objects.filter(
            attendance__in=attendance, status=True, student=student).count()
        absent_count = AttendanceReport.objects.filter(
            attendance__in=attendance, status=False, student=student).count()
        subject_name.append(subject.name)
        data_present.append(present_count)
        data_absent.append(absent_count)

    # Fetch student fee details
    fees = StudentFee.objects.filter(student=student)

    context = {
        'total_attendance': total_attendance,
        'percent_present': percent_present,
        'percent_absent': percent_absent,
        'total_subject': total_subject,
        'subjects': subjects,
        'data_present': data_present,
        'data_absent': data_absent,
        'data_name': subject_name,
        'fees': fees,  # Add student fee details to the context
        'page_title': 'Student Homepage'
    }

    # Render the template
    rendered_template = render(request, 'student_template/home_content.html', context)

    # Cache the rendered template with a suitable timeout
    cache.set(cache_key, rendered_template, 3600)  # Cache for 3600 seconds (1 hour)

    return rendered_template


from django.views.decorators.cache import cache_page

@ csrf_exempt
@cache_page(3600)  # Cache the view for 3600 seconds (1 hour)
def student_view_attendance(request):
    student = get_object_or_404(Student, admin=request.user)
    if request.method != 'POST':
        course = get_object_or_404(Course, id=student.course.id)
        context = {
            'subjects': Subject.objects.filter(course=course),
            'page_title': 'View Attendance'
        }
        return render(request, 'student_template/student_view_attendance.html', context)
    else:
        subject_id = request.POST.get('subject')
        start = request.POST.get('start_date')
        end = request.POST.get('end_date')
        try:
            subject = get_object_or_404(Subject, id=subject_id)
            start_date = datetime.strptime(start, "%Y-%m-%d")
            end_date = datetime.strptime(end, "%Y-%m-%d")
            attendance = Attendance.objects.filter(
                date__range=(start_date, end_date), subject=subject)
            attendance_reports = AttendanceReport.objects.filter(
                attendance__in=attendance, student=student)
            json_data = []
            for report in attendance_reports:
                data = {
                    "date":  str(report.attendance.date),
                    "status": report.status
                }
                json_data.append(data)
            return JsonResponse(json.dumps(json_data), safe=False)
        except Exception as e:
            return None


def student_apply_leave(request):
    # Define a cache key for this view
    cache_key = f'student_apply_leave_{request.user.id}'
    
    # Attempt to get the rendered template from the cache
    cached_template = cache.get(cache_key)
    
    if cached_template is not None:
        return cached_template

    form = LeaveReportStudentForm(request.POST or None)
    student = get_object_or_404(Student, admin_id=request.user.id)
    context = {
        'form': form,
        'leave_history': LeaveReportStudent.objects.filter(student=student),
        'page_title': 'Apply for leave'
    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                obj = form.save(commit=False)
                obj.student = student
                obj.save()
                messages.success(
                    request, "Application for leave has been submitted for review")
                return redirect(reverse('student_apply_leave'))
            except Exception:
                messages.error(request, "Could not submit")
        else:
            messages.error(request, "Form has errors!")

    # Render the template
    rendered_template = render(request, "student_template/student_apply_leave.html", context)

    # Cache the rendered template with a suitable timeout
    cache.set(cache_key, rendered_template, 3600)  # Cache for 3600 seconds (1 hour)

    return rendered_template

from django.views.decorators.cache import cache_page
@cache_page(3600)  # Cache the view for 3600 seconds (1 hour)
def student_feedback(request):
    form = FeedbackStudentForm(request.POST or None)
    student = get_object_or_404(Student, admin_id=request.user.id)
    context = {
        'form': form,
        'feedbacks': FeedbackStudent.objects.filter(student=student),
        'page_title': 'Student Feedback'

    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                obj = form.save(commit=False)
                obj.student = student
                obj.save()
                messages.success(
                    request, "Feedback submitted for review")
                return redirect(reverse('student_feedback'))
            except Exception:
                messages.error(request, "Could not Submit!")
        else:
            messages.error(request, "Form has errors!")
    return render(request, "student_template/student_feedback.html", context)


from django.views.decorators.cache import cache_page
@cache_page(3600)  # Cache the view for 3600 seconds (1 hour)
def student_view_profile(request):
    student = get_object_or_404(Student, admin=request.user)
    form = StudentEditForm(request.POST or None, request.FILES or None,
                           instance=student)
    context = {'form': form,
               'page_title': 'View/Edit Profile'
               }
    if request.method == 'POST':
        try:
            if form.is_valid():
                first_name = form.cleaned_data.get('first_name')
                last_name = form.cleaned_data.get('last_name')
                password = form.cleaned_data.get('password') or None
                address = form.cleaned_data.get('address')
                gender = form.cleaned_data.get('gender')
                passport = request.FILES.get('profile_pic') or None
                admin = student.admin
                if password != None:
                    admin.set_password(password)
                if passport != None:
                    fs = FileSystemStorage()
                    filename = fs.save(passport.name, passport)
                    passport_url = fs.url(filename)
                    admin.profile_pic = passport_url
                admin.first_name = first_name
                admin.last_name = last_name
                admin.address = address
                admin.gender = gender
                admin.save()
                student.save()
                messages.success(request, "Profile Updated!")
                return redirect(reverse('student_view_profile'))
            else:
                messages.error(request, "Invalid Data Provided")
        except Exception as e:
            messages.error(request, "Error Occured While Updating Profile " + str(e))

    return render(request, "student_template/student_view_profile.html", context)


@csrf_exempt
def student_fcmtoken(request):
    token = request.POST.get('token')
    student_user = get_object_or_404(CustomUser, id=request.user.id)
    try:
        student_user.fcm_token = token
        student_user.save()
        return HttpResponse("True")
    except Exception as e:
        return HttpResponse("False")


# from django.views.decorators.cache import cache_page
# @cache_page(3600)  # Cache the view for 3600 seconds (1 hour)
# # def student_view_notification(request):
# #     student = get_object_or_404(Student, admin=request.user)
# #     notifications = NotificationStudent.objects.filter(student=student)
# #     context = {
# #         'notifications': notifications,
# #         'page_title': "View Notifications"
# #     }
# #     return render(request, "student_template/student_view_notification.html", context)

def student_view_notification(request):
    student = get_object_or_404(Student, admin=request.user)
    notifications = NotificationStudent.objects.filter(student=student)
    context = {
        'notifications': notifications,
        'page_title': "View Notifications"
    }
    return render(request, "student_template/student_view_notification.html", context)


def student_view_result(request):
    student = get_object_or_404(Student, admin=request.user)
    results = StudentResult.objects.filter(student=student)
    context = {
        'results': results,
        'page_title': "View Results"
    }
    return render(request, "student_template/student_view_result.html", context)


# to display student fee update
def fee_detail(request):
    student = request.user.student
    fees = StudentFee.objects.filter(student=student)
    context = {'fees': fees}
    return render(request, 'student_template/fee_detail.html', context)


# for attending online classes @login_required
from django.contrib.auth.decorators import login_required

def online_class_list(request):
    # Define a cache key for the attended_classes queryset
    cache_key_attended = f'attended_classes_{request.user.id}'
    
    # Attempt to get the attended_classes queryset from the cache
    attended_classes = cache.get(cache_key_attended)
    
    if attended_classes is None:
        # If not found in cache, fetch the queryset from the database
        student = get_object_or_404(Student, admin=request.user)
        attended_classes = student.attended_online_classes.all()
        
        # Cache the queryset with a suitable timeout
        cache.set(cache_key_attended, attended_classes, 3600)  # Cache for 3600 seconds (1 hour)
    
    now = datetime.now()
    
    # Define a cache key for the upcoming_classes queryset
    cache_key_upcoming = f'upcoming_classes_{request.user.id}'
    
    # Attempt to get the upcoming_classes queryset from the cache
    upcoming_classes = cache.get(cache_key_upcoming)
    
    if upcoming_classes is None:
        # If not found in cache, fetch the queryset from the database
        upcoming_classes = OnlineClass.objects.filter(date__gte=date.today()).exclude(id__in=attended_classes.values_list('id', flat=True))
        
        # Cache the queryset with a suitable timeout
        cache.set(cache_key_upcoming, upcoming_classes, 3600)  # Cache for 3600 seconds (1 hour)
    
    context = {
        'attended_classes': attended_classes,
        'upcoming_classes': upcoming_classes,
        'page_title': 'Online Classes',
    }
    return render(request, 'student_template/online_class_list.html', context)


from django.views.decorators.cache import cache_page
@cache_page(3600)  # Cache the view for 3600 seconds (1 hour)
@login_required
def online_class_detail(request, pk):
    online_class = get_object_or_404(OnlineClass, pk=pk)
    context = {
        'online_class': online_class,
    }
    return render(request, 'student_template/online_class_detail.html', context)



# # for checking fee status 
# def pending_fees_view(request):
#     pending_fees = StudentFee.objects.filter(is_paid=False)
#     context = {'pending_fees': pending_fees}
#     return render(request, 'student_template/pending_fees.html', context)

# def paid_fees_view(request):
#     paid_fees = StudentFee.objects.filter(is_paid=True)
#     context = {'paid_fees': paid_fees}
#     return render(request, 'student_template/paid_fees.html', context)


def attended_students_list(request, class_id):
    online_class = OnlineClass.objects.get(pk=class_id)
    attended_students = online_class.students_attending.all()
    context = {
        'online_class': online_class,
        'attended_students': attended_students,
    }
    return render(request, 'hod_template/attended_students_list.html', context)