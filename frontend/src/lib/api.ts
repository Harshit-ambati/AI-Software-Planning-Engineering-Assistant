import axios from "axios";
import type { EngineeringBlueprint } from "../types/workflow";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000",
  timeout: 10000,
});

export async function generateBlueprint(idea: string): Promise<EngineeringBlueprint> {
  const response = await api.post<EngineeringBlueprint>("/api/projects/blueprint", { idea });
  return response.data;
}
