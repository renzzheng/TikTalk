# TikTalk API

A secure, Firebase-integrated REST API for managing users, videos, and notes with Google Cloud Storage integration.

## 🔐 Authentication

All endpoints (except public ones) require Firebase authentication. Include the Firebase ID token in the Authorization header:

```
Authorization: Bearer <firebase_id_token>
```

## 📡 API Endpoints

### User Management

#### Register User
```http
POST /api/users/register
Content-Type: application/json
Authorization: Bearer <firebase_token>

{
  "email": "user@example.com",
  "full_name": "John Doe",
  "username": "johndoe"  // optional
}
```

#### Get Current User Profile
```http
GET /api/users/me
Authorization: Bearer <firebase_token>
```

#### Update User Profile
```http
PUT /api/users/me
Content-Type: application/json
Authorization: Bearer <firebase_token>

{
  "email": "newemail@example.com",
  "full_name": "John Smith",
  "username": "johnsmith"  // optional
}
```

#### Delete User Account
```http
DELETE /api/users/me
Authorization: Bearer <firebase_token>
```

### Video Management

#### Create Video
```http
POST /api/videos
Content-Type: application/json
Authorization: Bearer <firebase_token>

{
  "videos_link": "gs://bucket/path/to/video.mp4"
}
```

#### Get User's Videos
```http
GET /api/videos/my-videos
Authorization: Bearer <firebase_token>
```

#### Get Specific Video
```http
GET /api/videos/{video_id}
Authorization: Bearer <firebase_token>
```

#### Update Video
```http
PUT /api/videos/{video_id}
Content-Type: application/json
Authorization: Bearer <firebase_token>

{
  "videos_link": "gs://bucket/new/path/to/video.mp4"
}
```

#### Delete Video
```http
DELETE /api/videos/{video_id}
Authorization: Bearer <firebase_token>
```

### Notes Management

#### Create Notes
```http
POST /api/notes
Content-Type: application/json
Authorization: Bearer <firebase_token>

{
  "notes_link": "gs://bucket/path/to/notes.pdf",
  "status": "not_started"  // optional, defaults to "not_started"
}
```

#### Get User's Notes
```http
GET /api/notes/my-notes
Authorization: Bearer <firebase_token>
```

#### Get Notes by Status
```http
GET /api/notes/status/{status}
Authorization: Bearer <firebase_token>
```

#### Get Specific Notes
```http
GET /api/notes/{notes_id}
Authorization: Bearer <firebase_token>
```

#### Update Notes
```http
PUT /api/notes/{notes_id}
Content-Type: application/json
Authorization: Bearer <firebase_token>

{
  "notes_link": "gs://bucket/new/path/to/notes.pdf",
  "status": "started"
}
```

#### Update Notes Status Only
```http
PATCH /api/notes/{notes_id}/status
Content-Type: application/json
Authorization: Bearer <firebase_token>

{
  "status": "scripted"
}
```

#### Delete Notes
```http
DELETE /api/notes/{notes_id}
Authorization: Bearer <firebase_token>
```

#### Get Available Statuses (Public)
```http
GET /api/notes/statuses
```

**Available Statuses:**
- `not_started`
- `started`
- `scripted`
- `audio_generated`
- `video_generated`
- `completed`

### File Processing

#### Process PDF (Public)
```http
POST /api/files/process-pdf
Content-Type: application/json

{
  "pdf_url": "gs://bucket/path/to/document.pdf"
}
```

### Health Check

#### Check API Status
```http
GET /health
```

## 🔧 Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables in `.env`:
```env
GOOGLE_APPLICATION_CREDENTIALS=/path/to/firebase-service-account.json
GCLOUD_PROJECT=your-project-id
BUCKET_NAME=your-bucket-name
DB_HOST=your-db-host
DB_PORT=5432
DB_NAME=your-db-name
DB_USER=your-db-user
DB_PASSWORD=your-db-password
```

3. Run the application:
```bash
python3 app.py
```

The API will be available at `http://localhost:5001`

## 🔒 Security Features

- **Firebase Authentication**: All user authentication handled by Firebase
- **JWT Token Validation**: Every request verified by Firebase Admin SDK
- **User Ownership**: Users can only access their own data
- **Automatic User Detection**: Backend automatically knows who's making requests
- **Cascade Delete**: Deleting a user removes all their associated data

## 📝 Notes

- All Google Cloud Storage URLs must be valid GCS URLs (gs:// or https://storage.googleapis.com/)
- User registration is required before accessing video/notes endpoints
- All timestamps are in UTC
- Database tables are created automatically on first run