# WhatsApp Bulk Messaging System

A comprehensive Flask-based web application for managing WhatsApp bulk messaging campaigns using the Meta WhatsApp Business API.

## Features

### Admin Features
- **Manage Businesses**: Add and configure WhatsApp Business API credentials
- **Manage Users**: Create and manage user accounts with role-based access
- **Manage Tasks**: Assign messaging tasks to users with specific business accounts
- **View Reports**: Comprehensive analytics with delivery, seen, and reply statistics

### User Features
- **Assigned Tasks**: View and manage tasks assigned by admins
- **Bulk Messaging**: Send WhatsApp messages to multiple recipients
  - CSV/Excel upload for recipients
  - Image URL support
  - Custom title and message body
  - Real-time progress tracking
- **Message History**: View past campaigns and their statistics

## Technology Stack

- **Backend**: Flask (Python 3.11)
- **Database**: Firebase Firestore
- **Queue System**: RQ (Redis Queue) for async message processing
- **Frontend**: HTML, Tailwind CSS, Vanilla JavaScript
- **API**: Meta WhatsApp Business Cloud API

## Setup Instructions

### 1. Prerequisites

- Python 3.11+
- Firebase project with Firestore enabled
- Meta WhatsApp Business API credentials
- Redis (optional, for production queue processing)

### 2. Installation

```bash
# Install dependencies (handled automatically by Replit)
# Or manually: pip install -r requirements.txt
```

### 3. Configuration

1. Create a `.env` file from the template:
```bash
cp .env.example .env
```

2. Update the `.env` file with your credentials:
   - `SESSION_SECRET`: Generate a secure random key
   - `FIREBASE_CREDENTIALS_PATH`: Path to your Firebase service account JSON file
   - `META_WEBHOOK_VERIFY_TOKEN`: Your webhook verification token
   - `ENCRYPTION_KEY`: Generate using: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
   - `REDIS_URL`: Your Redis connection URL (if using Redis)

3. Add your Firebase credentials:
   - Download the service account JSON from Firebase Console
   - Save it as `firebase-credentials.json` in the project root

### 4. Initialize Database

Run the seed script to create an initial admin user:

```bash
python seed_data.py
```

Default credentials:
- **Admin**: admin@example.com / admin123

### 5. Run the Application

```bash
# Start the Flask application
python main.py

# In a separate terminal, start the worker (for production)
python worker.py
```

The application will be available at `http://localhost:5000`

## Usage Workflow

### Admin Workflow

1. **Login** as admin (admin@example.com / admin123)
2. **Add Business**: Configure WhatsApp Business API credentials
   - Business name
   - Business token (encrypted automatically)
   - Phone ID
   - WABA ID
3. **Create Users**: Add user accounts who will send messages
4. **Create Tasks**: Assign tasks to users with specific business accounts

### User Workflow

1. **Login** as user
2. **View Assigned Tasks**: See tasks assigned by admin
3. **Send Messages**:
   - Select a task (optional)
   - Upload CSV/Excel file with phone numbers
   - Enter image URL
   - Write title and message body
   - Click "Send Messages"
4. **Monitor Progress**: Real-time stats (queued, sent, delivered, failed)
5. **View History**: Check past campaigns and their performance

## CSV Format

The recipient CSV/Excel file should have a column with phone numbers:

```csv
phone_number
+14155551234
+14155555678
+911234567890
```

Download the template from the "Send Message" page.

## API Endpoints

### Authentication
- `POST /auth/login` - Login
- `GET /auth/logout` - Logout

### Admin APIs
- `GET/POST /admin/api/businesses` - Manage businesses
- `GET/PUT/DELETE /admin/api/businesses/{id}` - Specific business
- `GET/POST /admin/api/users` - Manage users
- `GET/PUT/DELETE /admin/api/users/{id}` - Specific user
- `GET/POST /admin/api/tasks` - Manage tasks
- `GET/PUT/DELETE /admin/api/tasks/{id}` - Specific task

### User APIs
- `GET /user/api/tasks/assigned` - Get assigned tasks
- `PUT /user/api/tasks/{id}/status` - Update task status
- `GET /user/api/messages/history` - Get message history

### Messaging APIs
- `POST /messages/api/send` - Send bulk messages
- `GET /messages/api/messages/{id}/status` - Get message status
- `GET /messages/api/messages/{id}/recipients` - Get recipients

### Webhook
- `GET/POST /webhooks/meta` - Meta webhook for delivery/read/reply events

### Reports
- `GET /reports/api/task/{task_id}` - Get task report
- `GET /reports/api/admin/reports` - Admin reports (with filters)
- `GET /reports/api/export` - Export report to CSV

## Security Features

- Password hashing with Werkzeug
- Business token encryption with Fernet
- Role-based access control (Admin/User)
- Session management
- CSRF protection
- Webhook signature verification
- Input validation and sanitization

## Queue Processing

Messages are processed asynchronously using RQ (Redis Queue):

- Batch processing (configurable batch size)
- Retry logic with exponential backoff
- Rate limit handling
- Status tracking (queued → sent → delivered → seen)

## Meta WhatsApp API Integration

The system integrates with Meta WhatsApp Business Cloud API:

- Send image + text messages
- Receive delivery receipts
- Track read receipts
- Capture replies
- Handle rate limits
- Template message support

## Monitoring & Reporting

- Real-time message status tracking
- Aggregate statistics per task
- Delivery, seen, and reply metrics
- Recipient-level details
- CSV export for detailed analysis

## Troubleshooting

### Firebase Connection Issues
- Verify `firebase-credentials.json` exists and is valid
- Check Firebase project permissions

### Message Sending Fails
- Verify WhatsApp Business API credentials
- Check phone number format (E.164)
- Ensure image URL is publicly accessible
- Check Meta API rate limits

### Queue Not Processing
- Ensure Redis is running
- Start the worker: `python worker.py`
- Check Redis connection in logs

## License

Proprietary - All rights reserved

## Support

For issues or questions, please contact your system administrator.
