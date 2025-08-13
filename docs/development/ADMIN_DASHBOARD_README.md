# Admin Dashboard - KI Wellness

## Overview

The Admin Dashboard is a comprehensive system management interface that provides administrators with powerful tools to manage users, moderate content, and monitor system health. This dashboard is only accessible to users with admin privileges.

## Features

### 🔐 Security & Access Control
- **Admin-only access**: Restricted to users with `is_admin=True`
- **Session-based authentication**: Secure login required
- **Role-based permissions**: Different actions available based on user role

### 👥 User Management
- **View all users**: Complete list with profile information
- **User status management**: Activate/suspend user accounts
- **Role management**: Promote users to admin or demote admins
- **Account deletion**: Remove inactive or problematic accounts
- **Profile completion tracking**: Monitor users with incomplete profiles

### 📝 Content Moderation
- **Review management**: Approve or reject user-submitted reviews
- **Spam detection**: Built-in spam scoring system
- **Content quality control**: Monitor and manage user-generated content
- **Bulk operations**: Process multiple reviews efficiently

### 📊 System Monitoring
- **Real-time statistics**: User counts, content metrics, system health
- **Performance metrics**: Uptime, error rates, memory usage
- **Database monitoring**: Connection status, table counts
- **System health checks**: Automated health monitoring

### 📈 Analytics & Insights
- **User growth tracking**: Recent signups, active users
- **Content analytics**: Food entries, mood entries, reminders
- **Activity monitoring**: Recent user activity, system usage
- **Trend analysis**: User engagement patterns

## Technical Implementation

### Backend Routes

#### Core Admin Routes
- `GET /admin` - Main admin dashboard
- `GET /admin/system/health` - System health information

#### User Management Routes
- `POST /admin/users/<id>/suspend` - Suspend user account
- `POST /admin/users/<id>/activate` - Activate suspended account
- `POST /admin/users/<id>/promote` - Promote user to admin
- `POST /admin/users/<id>/demote` - Demote admin to user
- `POST /admin/users/<id>/delete` - Delete user account

#### Review Management Routes
- `POST /admin/reviews/<id>/approve` - Approve review
- `POST /admin/reviews/<id>/reject` - Reject and delete review

### Database Models

#### Enhanced User Model
```python
class User(db.Model):
    # ... existing fields ...
    is_active = db.Column(db.Boolean, default=True, nullable=False)  # Account status
```

#### Data Relationships
- Users have profiles (UserProfile)
- Users can submit reviews (Review)
- Users can create reminders (Reminder)
- Users can log food entries (FoodJournal)
- Users can log mood entries (MoodEntry)

### Frontend Components

#### Tabbed Interface
- **User Management**: Complete user table with actions
- **Review Management**: Pending review processing
- **System Monitoring**: Health checks and metrics

#### Interactive Elements
- Confirmation dialogs for destructive actions
- Real-time status updates
- Responsive design for mobile/desktop
- TailwindCSS styling with custom color scheme

## Installation & Setup

### 1. Database Migration
Run the migration script to add the `is_active` field:

```bash
cd cleanup_backup
python migrate_admin_dashboard.py
```

### 2. Admin Account Setup
Ensure you have an admin account by setting environment variables:

```bash
export ADMIN_USERNAME="your_admin_username"
export ADMIN_EMAIL="your_admin_email"
export ADMIN_PASSWORD="your_secure_password"
export ADMIN_NAME="Your Name"
```

### 3. Access the Dashboard
Navigate to `/admin` in your browser while logged in as an admin user.

## Usage Guide

### Managing Users

#### Suspend a User
1. Navigate to User Management tab
2. Find the user in the table
3. Click "Suspend" button
4. Confirm the action

#### Promote to Admin
1. Find the user in User Management
2. Click "Promote" button
3. Confirm the promotion
4. User will now have admin privileges

#### Delete User Account
1. Locate the user in the table
2. Click "Delete" button
3. Confirm the permanent deletion
4. User and all associated data will be removed

### Managing Reviews

#### Approve a Review
1. Go to Review Management tab
2. Review the submitted content
3. Click "Approve" button
4. Review will be publicly visible

#### Reject a Review
1. Find the review in the pending list
2. Click "Reject" button
3. Confirm the rejection
4. Review will be permanently deleted

### System Monitoring

#### Check System Health
1. Navigate to System Monitoring tab
2. Click "Run System Check" button
3. Review the health metrics
4. Address any issues identified

#### Monitor Performance
- View real-time statistics
- Track user growth
- Monitor content creation rates
- Check system resource usage

## Security Considerations

### Access Control
- Admin routes are protected with `@admin_required` decorator
- Session validation on every request
- CSRF protection for all POST requests

### Data Protection
- Users can only modify their own data
- Admin actions are logged and auditable
- Sensitive operations require confirmation

### Rate Limiting
- API endpoints have rate limiting
- Brute force protection on authentication
- CAPTCHA protection on public forms

## Customization

### Adding New Admin Features
1. Create new route with `@admin_required` decorator
2. Add corresponding frontend tab/component
3. Update the admin dashboard template
4. Add necessary JavaScript functions

### Modifying Statistics
1. Update the `admin_dashboard()` route
2. Add new metrics to the statistics objects
3. Update the frontend template to display new data

### Styling Changes
- Modify TailwindCSS classes in the template
- Update the custom color scheme in the script
- Adjust responsive breakpoints as needed

## Troubleshooting

### Common Issues

#### Migration Errors
- Ensure database connection is working
- Check that all required models are imported
- Verify database permissions

#### Access Denied
- Confirm user has admin privileges
- Check session is still valid
- Verify admin_required decorator is working

#### Data Not Loading
- Check database queries in admin routes
- Verify model relationships are correct
- Check for JavaScript console errors

### Debug Mode
Enable debug mode in Flask to see detailed error messages:

```python
app.run(debug=True)
```

## Future Enhancements

### Planned Features
- **Advanced Analytics**: User behavior tracking
- **Bulk Operations**: Mass user management
- **Audit Logging**: Detailed action history
- **API Management**: External service monitoring
- **Backup Management**: Automated backup scheduling

### Integration Opportunities
- **Monitoring Services**: Prometheus, Grafana
- **Log Aggregation**: ELK stack, Splunk
- **Alert Systems**: PagerDuty, Slack notifications
- **Analytics Platforms**: Google Analytics, Mixpanel

## Support

For technical support or feature requests:
1. Check the troubleshooting section above
2. Review the code comments and documentation
3. Create an issue in the project repository
4. Contact the development team

---

**Note**: This admin dashboard is designed for production use with proper security measures. Always test changes in a development environment before deploying to production.
