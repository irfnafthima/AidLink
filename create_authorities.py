from core.models import User

authorities = [
    ('police_hq', 'police123', 'Central Police Dept', 'police@aidlink.com'),
    ('fire_rescue', 'fire123', 'Fire & Rescue Unit', 'fire@aidlink.com'),
    ('med_ambulance', 'med123', 'City Hospital Ambulance', 'med@aidlink.com'),
    ('forest_guard', 'forest123', 'Forest Rangers', 'forest@aidlink.com'),
    ('women_helpline', 'women123', 'Women Safety Cell', 'women@aidlink.com')
]

for username, pwd, loc, email in authorities:
    if not User.objects.filter(username=username).exists():
        u = User.objects.create_user(username=username, email=email, password=pwd, role='authority', is_verified=True, location=loc)
        print(f'Created: {username}')
    else:
        print(f'Exists: {username}')
