'use client';

export default function LightOrDarkMode({ mode, toggleMode }) {
  return (
    <button onClick={toggleMode}>
      {mode === 'dark' ? 'Darkmode on' : 'Lightmode on'}
    </button>
  );
}