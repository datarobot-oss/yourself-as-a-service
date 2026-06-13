import { useEffect } from 'react';
import { SidebarProvider } from '@/components/ui/sidebar';
import Pages from '@/pages';
import { useCurrentUser } from '@/api/auth/hooks';
import { useAppConfig } from '@/api/app-config/hooks';
import { saveLanguage, useTranslation } from '@/lib/i18n';

export function App() {
  const { data: user } = useCurrentUser();
  const { botName } = useAppConfig();
  const { changeLanguage } = useTranslation();

  useEffect(() => {
    document.title = botName;
  }, [botName]);

  useEffect(() => {
    if (user?.language) {
      saveLanguage(user.language);
      changeLanguage(user.language);
    }
  }, [user?.language, changeLanguage]);

  return (
    <SidebarProvider>
      <Pages />
    </SidebarProvider>
  );
}
