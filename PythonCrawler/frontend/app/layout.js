'use client';

import './global.css';
import { useState } from 'react';
import LightOrDarkMode from './lightdarkmodeButton';

export default function RootLayout({ children }) {
  const [mode, setMode] = useState('dark');

  function toggleMode() {
    setMode((prev) => (prev === 'dark' ? 'light' : 'dark'));
  }

  return (
    <html lang="en">
      <body className={mode}>
        {children}
        <LightOrDarkMode mode={mode} toggleMode={toggleMode} />
      </body>
    </html>
  );
}