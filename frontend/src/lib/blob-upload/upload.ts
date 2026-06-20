import { upload } from "@vercel/blob/client";

type UploadResult = {
  url: string;
  downloadUrl: string;
  pathname: string;
  contentType: string;
};

export async function uploadVideoToBlob(file: File): Promise<UploadResult> {
  const result = await upload(file.name, file, {
    access: "public",
    handleUploadUrl: "/blob-token",
  });

  return result;
}
