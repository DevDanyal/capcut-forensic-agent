import { upload } from "@vercel/blob/client";

type UploadResult = {
  url: string;
  downloadUrl?: string;
  pathname?: string;
  contentType?: string;
};

async function uploadToTmpFiles(file: File): Promise<UploadResult> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch("https://tmpfiles.org/api/v1/upload", {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || "Failed to upload via tmpfiles.org");
  }

  const data = await response.json();
  if (data.status !== "success" || !data.data?.url) {
    throw new Error("tmpfiles.org upload failed: unexpected response");
  }

  return {
    url: data.data.url,
    contentType: file.type,
  };
}

export async function uploadVideoToBlob(file: File): Promise<UploadResult> {
  try {
    const result = await upload(file.name, file, {
      access: "public",
      handleUploadUrl: "/blob-token",
    });
    return result;
  } catch {
    return uploadToTmpFiles(file);
  }
}
