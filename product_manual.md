# EzyAssist Unified System - Product Manual

## Table of Contents
1. [System Overview](#system-overview)
2. [Getting Started](#getting-started)
3. [User Registration Process](#user-registration-process)
4. [Admin Dashboard](#admin-dashboard)
5. [Bot Status Monitoring](#bot-status-monitoring)
6. [User Management](#user-management)
7. [Registration Management](#registration-management)
8. [Communication Features](#communication-features)
9. [System Settings](#system-settings)
10. [Troubleshooting](#troubleshooting)
11. [Technical Specifications](#technical-specifications)

---

## System Overview

### What is EzyAssist Unified System?

EzyAssist Unified System is a comprehensive platform that combines a Telegram bot with a web-based registration system and admin dashboard. It's designed specifically for managing VIP forex trading course registrations for Malaysian users.

### Key Features
- **Telegram Bot Integration**: Interactive bot for user engagement and VIP registration
- **Web Registration System**: Secure online registration form with file upload capabilities
- **Modern Admin Dashboard**: Real-time monitoring and management interface
- **Bot Status Monitoring**: Live tracking of bot performance and user activity
- **Direct Communication Tools**: One-click contact options for admins
- **Bilingual Support**: Malay language interface with English fallbacks

### System Architecture
- **Frontend**: Modern web interface with responsive design
- **Backend**: FastAPI-based REST API
- **Database**: PostgreSQL for data persistence
- **Bot**: Python Telegram Bot API integration
- **Deployment**: Railway platform hosting

---

## Getting Started

### Accessing the System

#### For Users
1. **Telegram Bot**: Search for your EzyAssist bot on Telegram
2. **Registration**: Use bot commands to get registration links
3. **VIP Group**: Join https://t.me/ezyassist_vip after approval

#### For Admins
1. **Admin Dashboard**: Access via `/admin/` URL
2. **Default Credentials**: 
   - Username: `admin`
   - Password: `admin123`
3. **Security**: Change default credentials immediately after first login

### Initial Setup Checklist
- [ ] Test Telegram bot functionality
- [ ] Verify admin dashboard access
- [ ] Check bot status monitoring
- [ ] Test registration flow
- [ ] Configure notification settings

---

## User Registration Process

### Step 1: Bot Interaction
Users interact with the Telegram bot using these commands:

#### Available Commands
- `/start` - Welcome message and bot introduction
- `/register` - Generate VIP registration link
- `/clear` - Reset conversation history

#### VIP Registration Keywords
Users can trigger VIP registration by mentioning these keyword combinations:

**Direct VIP Keywords** (immediate triggers):
- "VIP"
- "daftar VIP"
- "join VIP"
- "nak join VIP"

**Action Keywords** (require "VIP" mention):
- "daftar" + "VIP"
- "pendaftaran" + "VIP"
- "mendaftar" + "VIP"
- "sertai" + "VIP"

**Interest Keywords** (require "VIP" mention):
- "kursus" + "VIP"
- "program" + "VIP"
- "berminat" + "VIP"
- "ingin join" + "VIP"

### Step 2: Registration Form
When users click the registration link, they complete a comprehensive form:

#### Required Information
1. **Personal Details**
   - Full Name
   - Email Address
   - Phone Number
   - Client ID

2. **Trading Information**
   - Brokerage Name
   - Deposit Amount

3. **File Uploads**
   - Deposit Proof 1 (Required)
   - Deposit Proof 2 (Optional)
   - Deposit Proof 3 (Optional)

#### Supported File Types
- Images: JPG, JPEG, PNG, GIF
- Documents: PDF
- Maximum file size: 10MB per file

### Step 3: Submission Confirmation
After successful submission, users see:
- Success confirmation page
- Registration reference number
- Next steps information
- Link to VIP Telegram group

---

## Admin Dashboard

### Dashboard Overview
The admin dashboard provides comprehensive system monitoring and management capabilities.

### Navigation Structure
**Left Sidebar Navigation:**
- **Dashboard** - System overview and statistics
- **Registrations** - All registration records
- **Pending Review** - Registrations awaiting approval
- **Verified Users** - Approved VIP members
- **Logout** - End admin session

### Dashboard Statistics

#### Registration Statistics Cards
1. **Total Registrations** - All-time registration count
2. **Pending Review** - Registrations awaiting admin action
3. **Verified** - Approved VIP members
4. **Rejected** - Declined registrations

#### Bot Status Monitoring
1. **Bot Status Card**
   - Online/Offline/Error status
   - Bot uptime duration
   - Webhook connection status
   - Last activity timestamp

2. **Bot Activity Card**
   - Active users (30-minute window)
   - Total users count
   - Messages processed today
   - Success rate percentage

#### Recent Activity
- New registrations this week
- Active brokers count
- Pending reviews requiring attention

#### Broker Statistics
- Registration distribution by brokerage
- Visual percentage breakdown
- Performance analytics

---

## Bot Status Monitoring

### Real-Time Monitoring
The dashboard updates bot status automatically every 30 seconds.

### Status Indicators

#### Bot Health Status
- **🟢 ONLINE (Healthy)**: Bot is running normally
- **🟡 OFFLINE (Warning)**: Bot is not responding
- **🔴 ERROR (Critical)**: Bot has encountered errors

#### Performance Metrics
- **Uptime**: How long the bot has been running
- **Active Users**: Users who interacted in the last 30 minutes
- **Total Users**: All users who have ever used the bot
- **Messages Today**: Messages processed in the last 24 hours
- **Success Rate**: Percentage of successful interactions
- **Error Count**: Total errors encountered

#### Command Usage Statistics
Track usage of bot commands:
- `/start` command usage
- `/register` command usage
- `/clear` command usage

---

## User Management

### Registration Status Management

#### Status Types
1. **PENDING** - New registration awaiting review
2. **VERIFIED** - Approved for VIP access
3. **REJECTED** - Declined registration requiring follow-up

#### Status Change Actions

##### Verifying a Registration
1. Navigate to registration detail page
2. Review all submitted information and files
3. Click "Verify & Grant VIP" button
4. User receives VIP access notification
5. User gains access to VIP Telegram group

##### Rejecting a Registration
1. Navigate to registration detail page
2. Review issues with the registration
3. Click "Reject Registration" button
4. User receives notification that team will contact them
5. Follow up required within 24 hours

### Bulk Operations

#### Delete All Records
For testing and data management:
1. Navigate to Dashboard
2. Click "Delete All Records" button
3. Complete triple confirmation process:
   - First confirmation dialog
   - Second warning dialog
   - Type "DELETE ALL" to confirm
4. All registration data is permanently removed

---

## Registration Management

### Registration List View

#### Filtering Options
- **Search**: By name, email, or broker
- **Status Filter**: All, Pending, Verified, Rejected
- **Pagination**: Navigate through large datasets

#### Registration Information Display
- Registration ID
- Full Name
- Email Address
- Phone Number
- Brokerage Name
- Deposit Amount
- File Upload Status
- Current Status
- Registration Date
- Action Buttons

### Registration Detail View

#### Information Sections

##### Personal Information
- Full Name
- Email Address (with direct email button)
- Phone Number (with call and WhatsApp buttons)
- Client ID

##### Trading Information
- Brokerage Name
- Deposit Amount

##### Telegram Information
- Telegram ID (with direct chat button)
- Telegram Username (with Telegram web chat button)

##### File Management
- Download buttons for all uploaded files
- File count and status indicators
- Secure file access controls

##### Technical Metadata
- Registration ID
- IP Address
- User Agent
- Registration timestamp
- Status update history
- Admin action logs

---

## Communication Features

### Direct Contact Options
From any registration detail page, admins can instantly contact users:

#### Email Communication
- **Email Button**: Opens default email client
- Pre-filled recipient address
- Professional communication channel

#### Phone Communication
- **Call Button**: Opens phone dialer
- **WhatsApp Button**: Opens WhatsApp chat
- Direct phone number formatting

#### Telegram Communication
- **Telegram ID Button**: Opens Telegram app with user ID
- **Username Button**: Opens Telegram web chat
- Instant messaging capability

### Automated Notifications

#### User Notifications
Users receive automatic Telegram messages for:

1. **Registration Pending**
   - Confirmation of successful submission
   - Review timeline expectations
   - Contact information verification

2. **VIP Access Granted**
   - Congratulations message
   - VIP group access link
   - Welcome to VIP benefits

3. **Registration Rejected**
   - Professional notification
   - Promise of follow-up contact
   - 24-hour response commitment

#### Admin Notifications
Admins receive notifications for:
- New registration submissions
- Registration details summary
- Direct link to admin panel

---

## System Settings

### Configuration Options

#### Environment Variables
- `TELEGRAM_BOT_TOKEN`: Bot authentication token
- `BASE_URL`: Application base URL for links
- `JWT_SECRET_KEY`: Security key for registration tokens
- `DATABASE_URL`: PostgreSQL connection string
- `ADMIN_ID`: Telegram ID for admin notifications

#### Security Settings
- JWT token expiration (default: 30 minutes)
- File upload restrictions
- Admin session management
- Password requirements

#### Notification Settings
- Telegram webhook configuration
- Admin notification preferences
- User message templates

### Database Management

#### Regular Maintenance
- Registration data cleanup
- File storage management
- Performance optimization
- Backup procedures

#### Data Export
- Registration reports
- User analytics
- Bot performance metrics
- Compliance documentation

---

## Troubleshooting

### Common Issues

#### Bot Not Responding
**Symptoms**: Users report bot is not answering
**Solutions**:
1. Check bot status on admin dashboard
2. Verify `TELEGRAM_BOT_TOKEN` environment variable
3. Check webhook configuration
4. Review bot error logs
5. Restart bot service if necessary

#### Registration Form Issues
**Symptoms**: Users cannot submit registration
**Solutions**:
1. Verify JWT token validity (30-minute expiration)
2. Check file upload size limits
3. Validate database connectivity
4. Review form validation errors

#### Admin Dashboard Access
**Symptoms**: Cannot access admin panel
**Solutions**:
1. Verify admin credentials
2. Check session expiration
3. Clear browser cache
4. Verify admin authentication system

#### File Upload Problems
**Symptoms**: Files not uploading properly
**Solutions**:
1. Check file size (max 10MB)
2. Verify supported file types
3. Review upload directory permissions
4. Check disk space availability

### Monitoring and Alerts

#### Health Checks
- Bot responsiveness monitoring
- Database connectivity checks
- File system availability
- API endpoint validation

#### Performance Monitoring
- Response time tracking
- Error rate monitoring
- User engagement metrics
- System resource usage

### Error Logging
- Application error logs
- Bot interaction logs
- User activity tracking
- Security event logging

---

## Technical Specifications

### System Requirements

#### Server Specifications
- **Memory**: Minimum 512MB RAM
- **Storage**: 1GB available disk space
- **Network**: Stable internet connection
- **Platform**: Railway cloud hosting

#### Dependencies
- **Python**: 3.8+
- **FastAPI**: Modern web framework
- **PostgreSQL**: Database system
- **Telegram Bot API**: Bot integration
- **Jinja2**: Template engine

### API Endpoints

#### Public Endpoints
- `GET /` - Registration form page
- `POST /submit` - Registration submission
- `GET /success` - Success confirmation page
- `GET /uploads/{filename}` - File download

#### Admin Endpoints
- `GET /admin/` - Admin dashboard
- `GET /admin/login` - Admin login page
- `POST /admin/login` - Admin authentication
- `GET /admin/registrations` - Registration list
- `GET /admin/registrations/{id}` - Registration details
- `POST /admin/registrations/{id}/verify` - Verify registration
- `POST /admin/registrations/{id}/reject` - Reject registration
- `POST /admin/registrations/delete-all` - Delete all records
- `GET /admin/bot-status` - Real-time bot status
- `GET /admin/logout` - Admin logout

#### Bot Endpoints
- `POST /telegram_webhook` - Telegram webhook handler
- `GET /health` - System health check

### Database Schema

#### VipRegistration Table
```sql
- id: Primary key
- telegram_id: User's Telegram ID
- telegram_username: Telegram username
- full_name: User's full name
- email: Email address
- phone_number: Phone number
- client_id: Trading client ID
- brokerage_name: Broker name
- deposit_amount: Deposit amount
- deposit_proof_1_path: File path
- deposit_proof_2_path: File path
- deposit_proof_3_path: File path
- status: ENUM (PENDING, VERIFIED, REJECTED)
- ip_address: Registration IP
- user_agent: Browser information
- created_at: Registration timestamp
- status_updated_at: Status change timestamp
- updated_by_admin: Admin who changed status
```

### Security Features

#### Data Protection
- JWT token-based authentication
- Secure file upload handling
- SQL injection prevention
- XSS protection
- CSRF protection

#### Access Control
- Admin session management
- Role-based permissions
- Secure password handling
- Environment variable protection

#### Privacy Compliance
- User data encryption
- Secure file storage
- Privacy policy compliance
- Data retention policies

---

## Best Practices

### For Admins

#### Daily Operations
1. Check bot status monitoring regularly
2. Review pending registrations promptly
3. Respond to rejected registrations within 24 hours
4. Monitor system performance metrics
5. Backup important data regularly

#### Security Practices
1. Change default admin credentials immediately
2. Use strong passwords
3. Log out after admin sessions
4. Monitor unauthorized access attempts
5. Keep system updated

#### User Communication
1. Respond professionally to all inquiries
2. Use direct contact features for urgent matters
3. Maintain consistent communication standards
4. Document important interactions
5. Follow up on rejected registrations

### For Users

#### Registration Process
1. Provide accurate information
2. Upload clear, legible documents
3. Use supported file formats
4. Keep registration reference numbers
5. Check Telegram for status updates

#### Bot Interaction
1. Use proper command syntax
2. Include "VIP" in registration requests
3. Wait for bot responses
4. Report issues to admin
5. Join VIP group after approval

---

## Support and Maintenance

### Getting Help

#### For Technical Issues
- Check troubleshooting section
- Review error logs
- Contact system administrator
- Submit issue reports

#### For User Support
- Use admin dashboard communication features
- Respond to user inquiries promptly
- Provide clear instructions
- Escalate complex issues appropriately

### System Updates

#### Regular Maintenance
- Monitor system performance
- Update dependencies
- Review security settings
- Backup data regularly

#### Feature Updates
- Test new features thoroughly
- Update documentation
- Train admin users
- Monitor user feedback

---

## Conclusion

The EzyAssist Unified System provides a comprehensive solution for managing VIP forex course registrations through an integrated Telegram bot and web-based admin dashboard. With real-time monitoring, direct communication features, and automated workflows, it streamlines the entire registration and approval process while maintaining professional standards and user experience.

For additional support or feature requests, please contact the system administrator or development team.

---

**Document Version**: 1.0
**Last Updated**: 2025-01-28
**System Version**: Production Release

---

*This manual covers all features and functionality of the EzyAssist Unified System. For the most current information, always refer to the admin dashboard and system notifications.*