import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aidlink.settings')
django.setup()

from core.models import Review

def seed_reviews():
    reviews = [
        {
            "user_name": "Marcus Thorne",
            "user_role": "Chief of Operations at Metro Safety",
            "content": "AidLink has been thoughtful, professional, and genuinely understood who we are as a community. They took the infrastructure we already had and helped us go further with it, making it more impactful while staying true to our identity. Their approach felt collaborative and considered, and the results spoke for themselves. We would highly recommend AidLink to any modern city looking to strengthen its digital safety presence."
        },
        {
            "user_name": "Elena Rodriguez",
            "user_role": "Community Coordinator, Sector 07",
            "content": "The localized intelligence hubs have transformed how we respond to neighborhood needs. It's not just about alerts; it's about the social safety layer that AidLink provides. The platform is intuitive, high-performance, and most importantly, it builds trust within the community."
        },
        {
            "user_name": "Sarah Jenkins",
            "user_role": "Medical Response Lead, North District",
            "content": "In critical situations, clarity is everything. AidLink's real-time telemetry and professional command center integration have streamlined our dispatch process significantly. It's a game-changer for emergency services."
        }
    ]

    for r in reviews:
        Review.objects.get_or_create(
            user_name=r['user_name'],
            user_role=r['user_role'],
            content=r['content']
        )
    print("Reviews seeded successfully.")

if __name__ == "__main__":
    seed_reviews()
