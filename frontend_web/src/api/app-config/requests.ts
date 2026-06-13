import apiClient from '../apiClient';

export interface AppConfig {
  bot_name: string;
}

export async function getAppConfig(): Promise<AppConfig> {
  const { data } = await apiClient.get<AppConfig>('/v1/app-config/');
  return data;
}
