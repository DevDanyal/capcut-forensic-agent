import { handleUpload } from "@vercel/blob/client";

export async function POST(request: Request) {
  if (!process.env.BLOB_READ_WRITE_TOKEN) {
    return Response.json(
      { error: "BLOB_READ_WRITE_TOKEN not configured. Set it in Vercel environment variables." },
      { status: 500 }
    );
  }

  try {
    const body = await request.json();

    const result = await handleUpload({
      body,
      request,
      onBeforeGenerateToken: async () => ({
        allowedContentTypes: [
          "video/mp4",
          "video/quicktime",
          "video/x-msvideo",
          "video/x-matroska",
          "video/webm",
          "video/x-ms-wmv",
          "video/x-flv",
        ],
        maximumSizeInBytes: 500 * 1024 * 1024,
        addRandomSuffix: true,
      }),
      onUploadCompleted: async () => {},
    });

    return Response.json(result);
  } catch (err) {
    return Response.json(
      { error: err instanceof Error ? err.message : "Failed to handle upload" },
      { status: 500 }
    );
  }
}
