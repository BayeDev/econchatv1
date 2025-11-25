import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'EconChat - Economic Data Assistant',
  description: 'Conversational interface for economists to query, visualize, and export international economic data',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-background text-text-primary min-h-screen">
        {children}
      </body>
    </html>
  );
}
