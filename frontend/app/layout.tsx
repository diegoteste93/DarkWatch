import './globals.css';
import Providers from './providers';

export const metadata = {
  title: 'DarkWatch',
  description: 'Cybersecurity leak monitoring SaaS'
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR" className="dark">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
