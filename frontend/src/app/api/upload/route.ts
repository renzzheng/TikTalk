import { NextRequest, NextResponse } from "next/server";
import { Storage } from "@google-cloud/storage";

// Initialize GCS client
const storage = new Storage({
  keyFilename: process.env.GOOGLE_APPLICATION_CREDENTIALS,
  projectId: process.env.GCLOUD_PROJECT,
});

// Ensure bucket name is configured
const bucketName = process.env.GCP_BUCKET_NAME;
if (!bucketName) {
  throw new Error("❌ Missing GCP_BUCKET_NAME in environment variables");
}
const bucket = storage.bucket(bucketName);

export async function POST(req: NextRequest) {
  try {
    const formData = await req.formData();
    const file = formData.get("file") as File;

    if (!file) {
      return NextResponse.json({ error: "No file uploaded" }, { status: 400 });
    }

    // Convert File → Buffer
    const arrayBuffer = await file.arrayBuffer();
    let buffer = Buffer.from(arrayBuffer);

    // For video files, we'll let the backend handle compression
    // The backend will optimize videos during processing
    console.log(`📁 File type: ${file.type}, Size: ${file.size} bytes`);

    // Replace this with the logged-in user's UID from Firebase later
    const uid = "test-user";

    // GCS path
    const gcsPath = `${uid}/${file.name}`;
    const blob = bucket.file(gcsPath);

    // Upload file with optimized settings
    await blob.save(buffer, {
      contentType: file.type || "application/pdf",
      resumable: false,
      metadata: {
        cacheControl: "public, max-age=31536000",
        // Add metadata for video optimization
        ...(file.type?.startsWith('video/') && {
          'video-optimized': 'true',
          'target-resolution': '720x1280',
          'target-bitrate': '1000k'
        })
      },
    });

    console.log(`✅ Uploaded: gs://${bucketName}/${gcsPath}`);

    return NextResponse.json({
      message: "Upload successful",
      url: `https://storage.googleapis.com/${bucketName}/${gcsPath}`,
      path: gcsPath,
    });
    
  } catch (err) {
    console.error("❌ Upload failed:", err);
    return NextResponse.json({ error: "Upload failed" }, { status: 500 });
  }
}
