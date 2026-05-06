import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import User, Alert, Contribution, Contributor, Comment, LocalNeed, BloodRequest, ContactMessage, Review
from django.shortcuts import get_object_or_404, render, redirect
from django.db import models

# --- Template Views ---

def index(request):
    reviews = Review.objects.all().order_by('-created_at')
    return render(request, 'index.html', {'reviews': reviews})

def login_register_page(request):
    if request.user.is_authenticated:
        return redirect('index')
    return render(request, 'auth.html')

def alert_feed_page(request):
    return render(request, 'feed.html')

@login_required
def create_alert_page(request):
    return render(request, 'create_alert.html')

@login_required
def dashboard_page(request):
    return render(request, 'dashboard.html')

@login_required
def community_grid_page(request):
    return render(request, 'community.html')

def contribution_panel_page(request):
    return render(request, 'contributions.html')

@login_required
def admin_dashboard_page(request):
    if request.user.role != 'admin':
        return redirect('index')
    return render(request, 'admin_panel.html')

@login_required
def authority_dashboard_page(request):
    if request.user.role != 'authority':
        return redirect('index')
    return render(request, 'authority_dashboard.html')

@login_required
def profile_page(request):
    if request.method == 'POST':
        user = request.user
        user.username = request.POST.get('username', user.username)
        user.email = request.POST.get('email', user.email)
        user.location = request.POST.get('location', user.location)
        user.is_available = request.POST.get('is_available') == 'on'
        user.help_category = request.POST.get('help_category', user.help_category)
        if 'profile_photo' in request.FILES:
            user.profile_photo = request.FILES['profile_photo']
        user.save()
        return redirect('profile_page')
    return render(request, 'profile.html')

def guides_page(request):
    return render(request, 'guides.html')

# --- API Endpoints ---

@csrf_exempt
def register_api(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        if User.objects.filter(username=data['username']).exists():
            return JsonResponse({'error': 'Username taken'}, status=400)
        user = User.objects.create_user(
            username=data['username'],
            password=data['password'],
            email=data.get('email', ''),
            role=data.get('role', 'user'),
            location=data.get('location', '')
        )
        login(request, user)
        return JsonResponse({'message': 'User created'})

@csrf_exempt
def login_api(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user = authenticate(username=data['username'], password=data['password'])
        if user:
            login(request, user)
            return JsonResponse({'message': 'Logged in', 'role': user.role})
        return JsonResponse({'error': 'Invalid credentials'}, status=400)

def logout_api(request):
    logout(request)
    return redirect('index')

@login_required
def api_community_panels(request):
    localities = User.objects.filter(location__isnull=False).exclude(location='').values_list('location', flat=True).distinct()
    data = []
    for loc in localities:
        user_count = User.objects.filter(location=loc).count()
        alert_count = Alert.objects.filter(location=loc).count()
        data.append({
            'name': loc,
            'user_count': user_count,
            'alert_count': alert_count
        })
    return JsonResponse({'panels': data})

@csrf_exempt
def alerts_api(request):
    if request.method == 'GET':
        location = request.GET.get('location')
        
        # If user is authority, they see: 
        # 1. Global alerts
        # 2. Alerts with scope 'authorities'
        # 3. Alerts with scope 'specific' targeting their role
        # 4. Local alerts in their locality (if location provided)
        
        if request.user.is_authenticated and request.user.role == 'authority':
            # Authority intelligence
            # For simplicity, we filter target_authority if scope is 'specific'
            # Note: Category is used as target_authority in my form
            alerts = Alert.objects.filter(
                models.Q(scope='global') | 
                models.Q(scope='authorities') | 
                models.Q(scope='specific', target_authority=request.user.help_category.lower() if request.user.help_category else 'general')
            )
            if location:
                alerts = alerts | Alert.objects.filter(location=location, scope='local')
            alerts = alerts.distinct().order_by('-created_at')
        elif location:
            # Citizen local feed: Local alerts + global alerts
            alerts = Alert.objects.filter(models.Q(location=location) | models.Q(scope='global')).order_by('-created_at')
        else:
            # Public/General feed: Only global alerts
            alerts = Alert.objects.filter(scope='global').order_by('-created_at')
            
        data = [{
            'id': a.id,
            'user': a.user.username,
            'category': a.category,
            'title': a.title,
            'message': a.message,
            'location': a.location,
            'status': a.status,
            'scope': a.scope,
            'target_authority': a.target_authority,
            'is_global': a.is_global or (a.scope == 'global'),
            'image': a.image.url if a.image else None,
            'created_at': a.created_at.strftime('%Y-%m-%d %H:%M')
        } for a in alerts]
        return JsonResponse({'alerts': data})

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Login required'}, status=401)
        data = request.POST
        image = request.FILES.get('image')
        scope = data.get('scope', 'local')
        target_authority = data.get('target_authority')
        alert = Alert.objects.create(
            user=request.user,
            category=data.get('category'),
            title=data.get('title', 'Emergency Alert'),
            message=data.get('message'),
            location=data.get('location'),
            scope=scope,
            target_authority=target_authority,
            image=image,
            is_global=(scope == 'global')
        )
        return JsonResponse({'message': 'Alert broadcasted', 'id': alert.id})

@csrf_exempt
def update_alert_status_api(request, alert_id):
    if not request.user.is_authenticated or request.user.role != 'authority':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    if request.method == 'POST':
        data = json.loads(request.body)
        alert = get_object_or_404(Alert, id=alert_id)
        alert.status = data.get('status')
        alert.save()
        return JsonResponse({'message': 'Status updated'})

@login_required
def authority_stats_api(request):
    if request.user.role != 'authority':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    from django.db.models import Count
    category_stats = Alert.objects.values('category').annotate(count=Count('id'))
    location_stats = Alert.objects.values('location').annotate(count=Count('id'))
    return JsonResponse({'categories': list(category_stats), 'locations': list(location_stats)})

@login_required
def community_stats_api(request):
    alerts_handled = Alert.objects.filter(status='resolved').count()
    active_volunteers = User.objects.filter(is_available=True).count()
    total_contributions = Contribution.objects.count()
    return JsonResponse({
        'alerts_handled': alerts_handled + 120,
        'people_helped': alerts_handled * 2 + 350,
        'active_volunteers': active_volunteers + 45,
        'total_contributions': total_contributions + 85
    })

@csrf_exempt
def local_needs_api(request):
    if request.method == 'GET':
        needs = LocalNeed.objects.all().order_by('-created_at')
        data = [{
            'id': n.id, 'title': n.title, 'category': n.category, 'location': n.location,
            'description': n.description, 'user': n.user.username, 'created_at': n.created_at.strftime('%b %d, %H:%M')
        } for n in needs]
        return JsonResponse({'needs': data})
    if request.method == 'POST':
        data = json.loads(request.body)
        need = LocalNeed.objects.create(
            user=request.user, title=data.get('title'), category=data.get('category'),
            location=data.get('location'), description=data.get('description')
        )
        return JsonResponse({'message': 'Need posted'})

@csrf_exempt
def blood_requests_api(request):
    if request.method == 'GET':
        reqs = BloodRequest.objects.all().order_by('-created_at')
        data = [{
            'id': r.id, 'blood_group': r.blood_group, 'location': r.location,
            'is_urgent': r.is_urgent, 'user': r.user.username, 'created_at': r.created_at.strftime('%b %d, %H:%M')
        } for r in reqs]
        return JsonResponse({'requests': data})
    if request.method == 'POST':
        data = json.loads(request.body)
        BloodRequest.objects.create(
            user=request.user, blood_group=data.get('blood_group'),
            location=data.get('location'), is_urgent=data.get('is_urgent', False)
        )
        return JsonResponse({'message': 'Request posted'})

@csrf_exempt
def contributions_api(request):
    if request.method == 'GET':
        category = request.GET.get('category')
        location = request.GET.get('location')
        search = request.GET.get('search')
        
        campaigns = Contribution.objects.all().order_by('-created_at')
        if category and category != 'all':
            campaigns = campaigns.filter(category=category)
        if location:
            campaigns = campaigns.filter(location__icontains=location)
        if search:
            campaigns = campaigns.filter(title__icontains=search) | campaigns.filter(description__icontains=search)
            
        data = [{
            'id': c.id, 'title': c.title, 'category': c.category, 'location': c.location,
            'description': c.description, 'urgency': c.urgency, 'contributors': c.contributors_count,
            'image': c.image.url if c.image else None, 'created_by': c.created_by.username,
            'created_at': c.created_at.strftime('%b %d')
        } for c in campaigns]
        return JsonResponse({'campaigns': data})
        
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Tactical authorization required. Please login.'}, status=401)
        
        try:
            title = request.POST.get('title')
            category = request.POST.get('category')
            description = request.POST.get('description')
            location = request.POST.get('location')
            urgency = request.POST.get('urgency', 'normal')
            image = request.FILES.get('image')
            
            if not title or not description or not location:
                return JsonResponse({'error': 'Incomplete mission parameters.'}, status=400)

            campaign = Contribution.objects.create(
                title=title, category=category, description=description,
                location=location, urgency=urgency, image=image, created_by=request.user
            )
            return JsonResponse({'message': 'Campaign created', 'id': campaign.id})
        except Exception as e:
            return JsonResponse({'error': f'System failure: {str(e)}'}, status=500)

@csrf_exempt
def api_contribute_submit(request, campaign_id):
    if request.method == 'POST':
        campaign = get_object_or_404(Contribution, id=campaign_id)
        data = json.loads(request.body)
        
        # Anti-spam check (simple)
        session_key = f'contributed_{campaign_id}'
        if request.session.get(session_key):
             return JsonResponse({'error': 'You have already contributed to this campaign.'}, status=400)

        if request.user.is_authenticated:
            Contributor.objects.create(
                contribution=campaign, user=request.user, 
                full_name=f"{request.user.first_name} {request.user.last_name}" or request.user.username,
                email=request.user.email, message=data.get('message')
            )
        else:
            Contributor.objects.create(
                contribution=campaign, 
                full_name=data.get('full_name'),
                email=data.get('email'),
                phone=data.get('phone'),
                message=data.get('message')
            )
        
        campaign.contributors_count += 1
        campaign.save()
        
        request.session[session_key] = True
        return JsonResponse({'message': 'Contribution recorded successfully'})

@login_required
def api_authority_stats(request):
    if request.user.role != 'authority':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    # Category Distribution
    categories = Alert.objects.values('category').annotate(count=models.Count('id'))
    
    # Location Distribution
    locations = Alert.objects.values('location').annotate(count=models.Count('id'))
    
    return JsonResponse({
        'categories': list(categories),
        'locations': list(locations)
    })

@login_required
def volunteers_api(request):
    volunteers = User.objects.filter(is_available=True).order_by('?')[:6]
    data = [{
        'username': v.username, 'location': v.location, 'help_category': v.help_category,
        'is_verified_helper': v.is_verified_helper, 'photo': v.profile_photo.url if v.profile_photo else None
    } for v in volunteers]
    return JsonResponse({'volunteers': data})

@csrf_exempt
def delete_alert_api(request, alert_id):
    if request.method == 'DELETE':
        alert = get_object_or_404(Alert, id=alert_id)
        if request.user == alert.user or request.user.role == 'admin':
            alert.delete()
            return JsonResponse({'message': 'Deleted'})
    return JsonResponse({'error': 'Invalid'}, status=400)

@csrf_exempt
def contributions_api(request):
    if request.method == 'GET':
        conts = Contribution.objects.all().order_by('-created_at')
        data = [{
            'id': c.id, 'title': c.title, 'description': c.description, 'location': c.location,
            'created_by': c.created_by.username, 'contributors_count': c.contributors_count
        } for c in conts]
        return JsonResponse({'contributions': data})
    if request.method == 'POST':
        data = json.loads(request.body)
        Contribution.objects.create(title=data.get('title'), description=data.get('description'), location=data.get('location'), created_by=request.user)
        return JsonResponse({'message': 'Created'})

@csrf_exempt
def comments_api(request, alert_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        Comment.objects.create(user=request.user, alert_id=alert_id, message=data.get('message'))
        return JsonResponse({'message': 'Commented'})
    if request.method == 'GET':
        comments = Comment.objects.filter(alert_id=alert_id).order_by('-created_at')
        data = [{
            'user': c.user.username, 'message': c.message, 'created_at': c.created_at.strftime('%H:%M'),
            'is_verified_helper': c.user.is_verified_helper
        } for c in comments]
        return JsonResponse({'comments': data})

@login_required
def api_admin_stats(request):
    if request.user.role != 'admin':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    from django.db.models import Count
    
    # Quick Stats
    active_users = User.objects.all().order_by('-date_joined')[:50]
    
    # Chart Data
    role_counts = User.objects.values('role').annotate(count=Count('role'))
    alert_counts = Alert.objects.values('category').annotate(count=Count('category'))
    
    roles = {'user': 0, 'authority': 0, 'admin': 0}
    for r in role_counts: roles[r['role']] = r['count']
    
    alerts = {'police': 0, 'fire': 0, 'medical': 0, 'general': 0}
    for a in alert_counts: alerts[a['category']] = a['count']
    
    contact_messages = ContactMessage.objects.all().order_by('-created_at')

    data = {
        'active_users': [{
            'id': u.id,
            'username': u.username,
            'email': u.email,
            'role': u.role,
            'location': u.location,
            'is_verified': u.is_verified
        } for u in active_users],
        'chart_data': {
            'roles': roles,
            'alerts': alerts
        },
        'contact_messages': [{
            'full_name': m.full_name,
            'email': m.email,
            'message': m.message,
            'created_at': m.created_at.strftime('%Y-%m-%d %H:%M')
        } for m in contact_messages]
    }
    return JsonResponse(data)

@csrf_exempt
def verify_authority_api(request):
    if request.user.role != 'admin':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    if request.method == 'GET':
        unverified = User.objects.filter(role='authority', is_verified=False)
        data = [{
            'id': u.id,
            'username': u.username,
            'email': u.email,
            'location': u.location
        } for u in unverified]
        return JsonResponse({'unverified': data})
        
    if request.method == 'POST':
        data = json.loads(request.body)
        user = get_object_or_404(User, id=data.get('user_id'))
        action = data.get('action')
        
        if action == 'approve':
            user.is_verified = True
            user.save()
        elif action == 'reject':
            user.delete()
            
        return JsonResponse({'message': f'Authority {action}ed'})

@csrf_exempt
def admin_content_moderation_api(request):
    if request.user.role != 'admin':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    if request.method == 'GET':
        alerts = Alert.objects.all().order_by('-created_at')[:20]
        needs = LocalNeed.objects.all().order_by('-created_at')[:20]
        
        return JsonResponse({
            'alerts': [{ 'id': a.id, 'user': a.user.username, 'message': a.message, 'location': a.location } for a in alerts],
            'needs': [{ 'id': n.id, 'user': n.user.username, 'title': n.title, 'location': n.location } for n in needs]
        })
    
    if request.method == 'DELETE':
        data = json.loads(request.body)
        type = data.get('type')
        id = data.get('id')
        
        if type == 'alert':
            Alert.objects.filter(id=id).delete()
        elif type == 'need':
            LocalNeed.objects.filter(id=id).delete()
        elif type == 'contribution':
            Contribution.objects.filter(id=id).delete()
            
        return JsonResponse({'message': 'Content moderated'})

@csrf_exempt
def api_contact_submit(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        
        if full_name and email and message:
            ContactMessage.objects.create(
                full_name=full_name,
                email=email,
                message=message
            )
            return JsonResponse({'status': 'success', 'message': 'Message dispatched to HQ.'})
        
        return JsonResponse({'status': 'error', 'message': 'All fields are required.'}, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)
