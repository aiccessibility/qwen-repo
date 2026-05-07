import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Accessibility Multi-Agent Platform',
  description: 'AI-powered web accessibility auditing and monitoring',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
