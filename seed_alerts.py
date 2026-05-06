import os
import django
import requests
from django.core.files import File
from io import BytesIO

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aidlink.settings')
django.setup()

from core.models import User, Alert

def seed_alerts():
    # 1. Create or get Authority user
    authority, created = User.objects.get_or_create(
        username='Global_Response_Node',
        defaults={
            'email': 'hq@aidlink.org',
            'role': 'authority',
            'is_verified': True,
            'location': 'HQ - Global'
        }
    )
    if created:
        authority.set_password('AidLink2026!')
        authority.save()
        print("Created Global Authority User.")

    # 2. Sample Alert Data
    samples = [
        {
            'category': 'police',
            'message': 'CRITICAL: Strategic security perimeter established around District 4. Unauthorized access restricted until 0600 hrs. Monitor local frequencies for updates.',
            'location': 'Downtown Metro Area',
            'scope': 'global',
            'img_url': 'https://images.unsplash.com/photo-1517486808906-6ca8b3f04846?auto=format&fit=crop&q=80&w=1000'
        },
        {
            'category': 'fire',
            'message': 'EMERGENCY: High-intensity thermal anomaly detected in Sector B Industrial Park. Multi-agency response teams deployed. Immediate evacuation of adjacent sectors required.',
            'location': 'Industrial Sector B',
            'scope': 'global',
            'img_url': 'https://images.unsplash.com/photo-1534067783941-51c9c23ecefd?auto=format&fit=crop&q=80&w=1000'
        },
        {
            'category': 'medical',
            'message': 'ADVISORY: Rapid Deployment Medical Units (RDMU) now operational across all major hubs. Oxygen supply levels verified and stable. Priority routing enabled for critical transports.',
            'location': 'Global Network Hubs',
            'scope': 'global',
            'img_url': 'https://images.unsplash.com/photo-1516574187841-cb9cc2ca948b?auto=format&fit=crop&q=80&w=1000'
        }
    ]

    for s in samples:
        # Check if alert already exists
        if not Alert.objects.filter(message=s['message']).exists():
            alert = Alert.objects.create(
                user=authority,
                category=s['category'],
                message=s['message'],
                location=s['location'],
                scope=s['scope'],
                is_global=True,
                status='in progress'
            )
            
            # Download and attach image
            try:
                response = requests.get(s['img_url'])
                if response.status_code == 200:
                    img_temp = BytesIO()
                    img_temp.write(response.content)
                    file_name = f"sample_{s['category']}_{alert.id}.jpg"
                    alert.image.save(file_name, File(img_temp), save=True)
                    print(f"Created {s['category']} alert with image.")
            except Exception as e:
                print(f"Failed to download image for {s['category']}: {e}")
        else:
            print(f"Alert for {s['category']} already exists.")

if __name__ == '__main__':
    seed_alerts()
