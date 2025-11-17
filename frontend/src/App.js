import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import DiagramRenderer from './pages/DiagramRenderer';
import { Toaster } from './components/ui/sonner';
import './App.css';

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<DiagramRenderer />} />
        </Routes>
      </BrowserRouter>
      <Toaster position="top-right" richColors />
    </div>
  );
}

export default App;