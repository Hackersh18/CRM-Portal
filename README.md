# CRM Management System

A comprehensive Django-based Customer Relationship Management (CRM) System designed for lead management, counsellor performance tracking, and business generation with advanced analytics and reporting features.

## Features

### Admin Features
- **Dashboard Analytics**: Comprehensive dashboard with charts, graphs, and statistical representations
- **Lead Management**: Add, edit, delete, and import leads from Excel/CSV files
- **Counsellor Management**: Add, edit, and manage counsellor accounts
- **Lead Assignment**: Automatic round-robin assignment of leads to counsellors
- **Lead Transfer**: Transfer leads between counsellors when needed
- **Performance Tracking**: Monitor counsellor performance and conversion rates
- **Business Analytics**: Track business generation and revenue metrics
- **Lead Source Management**: Manage different lead sources and their effectiveness
- **Notification System**: Send notifications to counsellors

### Counsellor Features
- **Personal Dashboard**: View assigned leads and performance metrics
- **Lead Management**: Update lead status, add activities, and track progress
- **Activity Tracking**: Log calls, emails, meetings, and follow-ups
- **Business Creation**: Convert qualified leads into business opportunities
- **Follow-up Scheduling**: Schedule and manage follow-up activities
- **Lead Transfer Requests**: Request lead transfers when unable to generate business
- **Performance Analytics**: View personal performance statistics

### Core CRM Features
- **Lead Lifecycle Management**: Complete lead tracking from new to closed
- **Activity Management**: Comprehensive activity logging and tracking
- **Business Generation**: Convert leads to business opportunities
- **Performance Analytics**: Advanced reporting and analytics
- **Real-time Notifications**: Firebase-powered notification system
- **Data Import/Export**: Excel and CSV file support
- **Responsive Design**: Mobile-friendly interface

## Technology Stack

- **Backend**: Python 3.x, Django 3.1.1
- **Frontend**: Bootstrap 4, jQuery, Chart.js
- **Database**: SQLite (Development) / PostgreSQL (Production)
- **Charts**: Chart.js for data visualization
- **File Processing**: Pandas for Excel/CSV import
- **Notifications**: Firebase Cloud Messaging
- **Deployment**: Heroku-ready with WhiteNoise

## Installation

1. **Clone the repository**:
```bash
git clone https://github.com/yourusername/CRM-Management-System.git
cd CRM-Management-System
```

2. **Create a virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**:
Create a `.env` file in the project root and add:
```
DEBUG=True
SECRET_KEY=your_secret_key
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=your_email_password
```

5. **Run migrations**:
```bash
python manage.py makemigrations
python manage.py migrate
```

6. **Create a superuser (Admin)**:
```bash
python manage.py createsuperuser
```

7. **Run the development server**:
```bash
python manage.py runserver
```

## Usage

### Admin Workflow
1. **Login** as admin at `http://localhost:8000`
2. **Add Lead Sources** (Website, Social Media, Referrals, etc.)
3. **Add Counsellors** with employee IDs and departments
4. **Import Leads** from Excel/CSV files or add manually
5. **Assign Leads** to counsellors automatically or manually
6. **Monitor Performance** through dashboard analytics
7. **Transfer Leads** when counsellors cannot generate business

### Counsellor Workflow
1. **Login** with counsellor credentials
2. **View Assigned Leads** in personal dashboard
3. **Update Lead Status** (New → Contacted → Qualified → Closed)
4. **Add Activities** (calls, emails, meetings, follow-ups)
5. **Create Business** from qualified leads
6. **Schedule Follow-ups** for future activities
7. **Request Transfers** if unable to generate business

### Lead Import Format
The system supports Excel/CSV files with the following columns:
- `first_name` (required)
- `last_name` (required)
- `email` (required)
- `phone` (required)
- `company` (optional)
- `position` (optional)
- `industry` (optional)
- `expected_value` (optional)
- `notes` (optional)
- `address`, `city`, `state`, `country`, `postal_code` (optional)
- `website`, `linkedin` (optional)

## Database Schema

### Core Models
- **CustomUser**: Extended user model with email authentication
- **Admin**: Admin user profile
- **Counsellor**: Counsellor user profile with performance metrics
- **LeadSource**: Different sources of leads
- **Lead**: Complete lead information and status tracking
- **LeadActivity**: Activity logging for each lead
- **Business**: Business opportunities generated from leads
- **LeadTransfer**: Lead transfer requests and approvals
- **CounsellorPerformance**: Monthly performance tracking
- **NotificationCounsellor/NotificationAdmin**: Notification system

### Lead Status Flow
1. **NEW** → Initial lead entry
2. **CONTACTED** → First contact made
3. **QUALIFIED** → Lead qualified for business
4. **PROPOSAL_SENT** → Proposal submitted
5. **NEGOTIATION** → Under negotiation
6. **CLOSED_WON** → Business won
7. **CLOSED_LOST** → Business lost
8. **TRANSFERRED** → Transferred to another counsellor

## Analytics & Reporting

### Admin Dashboard Features
- **Lead Status Distribution**: Pie chart showing lead status breakdown
- **Monthly Trends**: Line chart showing leads and business value over time
- **Lead Sources**: Pie chart showing effectiveness of different sources
- **Counsellor Performance**: Bar chart comparing counsellor metrics
- **Recent Activities**: Real-time activity feed
- **Quick Actions**: Direct access to common tasks

### Performance Metrics
- **Conversion Rate**: Leads to business conversion percentage
- **Response Time**: Average time to first contact
- **Business Value**: Total revenue generated
- **Activity Tracking**: Number of activities per lead
- **Follow-up Compliance**: Scheduled vs completed follow-ups

## Security Features

- **Role-based Access Control**: Admin and Counsellor permissions
- **Email Authentication**: Secure email-based login
- **CSRF Protection**: Built-in Django CSRF protection
- **Password Reset**: Email-based password recovery
- **Session Management**: Secure session handling

## Deployment

### Production Settings
1. **Update settings.py**:
   - Set `DEBUG = False`
   - Configure production database
   - Set up static file serving
   - Configure email settings

2. **Environment Variables**:
   - Set production secret key
   - Configure database URL
   - Set up email credentials

3. **Static Files**:
   - Run `python manage.py collectstatic`
   - Configure static file serving

### Heroku Deployment
1. **Add Procfile** (already included)
2. **Configure buildpacks**
3. **Set environment variables**
4. **Deploy using Heroku CLI**

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions, please contact the development team or create an issue in the repository. 