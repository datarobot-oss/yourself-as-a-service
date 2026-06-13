import { useQuery } from '@tanstack/react-query';
import { getAppConfig, type AppConfig } from './requests';

export const appConfigKeys = {
  config: ['app-config'] as const,
};

const DEFAULT_BOT_NAME = 'Yourself as a Service';

export const useAppConfig = () => {
  const query = useQuery<AppConfig, Error>({
    queryKey: appConfigKeys.config,
    queryFn: () => getAppConfig(),
    staleTime: Infinity,
  });

  return {
    ...query,
    botName: query.data?.bot_name ?? DEFAULT_BOT_NAME,
  };
};
