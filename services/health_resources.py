#!/usr/bin/env python3
"""
Health resources database for AI chat responses
"""

# Medium blog categories and links
MEDIUM_BLOG_RESOURCES = {
    'nutrition': [
        {
            'title': '10 Energy-Boosting Foods for Better Performance',
            'url': 'https://kiwellness.medium.com/10-energy-boosting-foods-for-better-performance',
            'description': 'Discover the best foods to fuel your day'
        },
        {
            'title': 'The Complete Guide to Healthy Meal Planning',
            'url': 'https://kiwellness.medium.com/complete-guide-to-healthy-meal-planning',
            'description': 'Learn how to plan nutritious meals that support your goals'
        },
        {
            'title': 'Understanding Calories: Quality vs Quantity',
            'url': 'https://kiwellness.medium.com/understanding-calories-quality-vs-quantity',
            'description': 'Why the quality of your calories matters more than the number'
        }
    ],
    'mood': [
        {
            'title': '5 Simple Ways to Boost Your Mood Naturally',
            'url': 'https://kiwellness.medium.com/5-simple-ways-to-boost-your-mood-naturally',
            'description': 'Natural strategies for improving your mental wellbeing'
        },
        {
            'title': 'The Connection Between Diet and Mental Health',
            'url': 'https://kiwellness.medium.com/diet-and-mental-health-connection',
            'description': 'How what you eat affects how you feel'
        },
        {
            'title': 'Tracking Your Mood: A Beginner\'s Guide',
            'url': 'https://kiwellness.medium.com/tracking-your-mood-beginners-guide',
            'description': 'Learn how to monitor and improve your emotional health'
        }
    ],
    'hydration': [
        {
            'title': 'Hydration 101: How Much Water Do You Really Need?',
            'url': 'https://kiwellness.medium.com/hydration-101-how-much-water-do-you-really-need',
            'description': 'The science behind proper hydration'
        },
        {
            'title': 'Signs You\'re Not Drinking Enough Water',
            'url': 'https://kiwellness.medium.com/signs-youre-not-drinking-enough-water',
            'description': 'Recognize the warning signs of dehydration'
        },
        {
            'title': 'Creative Ways to Stay Hydrated Throughout the Day',
            'url': 'https://kiwellness.medium.com/creative-ways-to-stay-hydrated',
            'description': 'Fun and effective hydration strategies'
        }
    ],
    'wellness': [
        {
            'title': 'Building Healthy Habits That Actually Stick',
            'url': 'https://kiwellness.medium.com/building-healthy-habits-that-actually-stick',
            'description': 'The psychology behind lasting behavior change'
        },
        {
            'title': 'Self-Care for Busy People: 5-Minute Wellness Rituals',
            'url': 'https://kiwellness.medium.com/self-care-for-busy-people',
            'description': 'Quick wellness practices for your busy lifestyle'
        },
        {
            'title': 'The Power of Small Changes in Your Health Journey',
            'url': 'https://kiwellness.medium.com/power-of-small-changes-in-health-journey',
            'description': 'Why incremental improvements lead to lasting results'
        }
    ],
    'general': [
        {
            'title': 'Getting Started with Ki Wellness: Your Complete Guide',
            'url': 'https://kiwellness.medium.com/getting-started-with-ki-wellness',
            'description': 'Everything you need to know to begin your wellness journey'
        },
        {
            'title': 'The Science Behind Self Health Tracking',
            'url': 'https://kiwellness.medium.com/science-behind-self-health-tracking',
            'description': 'Why tracking your health data leads to better outcomes'
        }
    ]
}

# Authoritative health sources
AUTHORITATIVE_SOURCES = {
    'nutrition': [
        {
            'title': 'Nutrition Basics - Mayo Clinic',
            'url': 'https://www.mayoclinic.org/healthy-lifestyle/nutrition-and-healthy-eating/basics/nutrition-basics/hlv-20049477',
            'description': 'Comprehensive nutrition information from Mayo Clinic'
        },
        {
            'title': 'Healthy Eating - Harvard Health',
            'url': 'https://www.health.harvard.edu/topics/healthy-eating',
            'description': 'Evidence-based nutrition advice from Harvard Medical School'
        }
    ],
    'mood': [
        {
            'title': 'Mental Health - Mayo Clinic',
            'url': 'https://www.mayoclinic.org/healthy-lifestyle/adult-health/in-depth/mental-health/art-20044098',
            'description': 'Mental health resources and information'
        },
        {
            'title': 'Depression and Anxiety - WebMD',
            'url': 'https://www.webmd.com/depression/default.htm',
            'description': 'Understanding and managing mood disorders'
        }
    ],
    'hydration': [
        {
            'title': 'Water: How Much Should You Drink? - Mayo Clinic',
            'url': 'https://www.mayoclinic.org/healthy-lifestyle/nutrition-and-healthy-eating/in-depth/water/art-20044256',
            'description': 'Official hydration guidelines from Mayo Clinic'
        },
        {
            'title': 'Hydration - Harvard Health',
            'url': 'https://www.health.harvard.edu/staying-healthy/how-much-water-should-you-drink',
            'description': 'Research-based hydration advice'
        }
    ],
    'exercise': [
        {
            'title': 'Exercise - Mayo Clinic',
            'url': 'https://www.mayoclinic.org/healthy-lifestyle/fitness/in-depth/exercise/art-20048389',
            'description': 'Exercise guidelines and benefits'
        },
        {
            'title': 'Physical Activity - CDC',
            'url': 'https://www.cdc.gov/physicalactivity/basics/index.htm',
            'description': 'Official physical activity recommendations'
        }
    ]
}

def get_relevant_resources(question_type, topic=None):
    """Get relevant resources based on question type and topic"""
    
    resources = []
    
    # Add Medium blog resources
    if topic in MEDIUM_BLOG_RESOURCES:
        resources.extend(MEDIUM_BLOG_RESOURCES[topic][:2])  # Get up to 2 blog posts
    elif question_type in MEDIUM_BLOG_RESOURCES:
        resources.extend(MEDIUM_BLOG_RESOURCES[question_type][:2])
    else:
        resources.extend(MEDIUM_BLOG_RESOURCES['general'][:1])
    
    # Add authoritative sources
    if topic in AUTHORITATIVE_SOURCES:
        resources.extend(AUTHORITATIVE_SOURCES[topic][:1])  # Get 1 authoritative source
    
    return resources

def format_resources_for_prompt(resources):
    """Format resources for inclusion in AI prompt"""
    if not resources:
        return ""
    
    formatted = "\n\nAvailable Resources:\n"
    for i, resource in enumerate(resources, 1):
        formatted += f"{i}. {resource['title']} - {resource['url']}\n"
    
    return formatted
