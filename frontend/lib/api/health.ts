import { request } from "./client";

export async function getHealth(): Promise<{ status: string }> {
  return request("/health");
}
