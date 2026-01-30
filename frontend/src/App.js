import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import DiagramRenderer from './pages/DiagramRenderer';
import DiagramsList from './pages/DiagramsList';
import Login from './pages/Login';
import Signup from './pages/Signup';
import ProtectedRoute from './components/ProtectedRoute';
import { AuthProvider } from './context/AuthContext';
import { Toaster } from './components/ui/sonner';
import './App.css';

function App() {
  return (
    <div className="App">
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
            <Route 
              path="/" 
              element={
                <ProtectedRoute>
                  <DiagramsList />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/diagrams" 
              element={
                <ProtectedRoute>
                  <DiagramsList />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/diagrams/:diagramId" 
              element={
                <ProtectedRoute>
                  <DiagramRenderer />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/editor" 
              element={
                <ProtectedRoute>
                  <DiagramRenderer />
                </ProtectedRoute>
              } 
            />
            {/* Redirect any unknown routes to home */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
        <Toaster position="top-right" richColors />
      </AuthProvider>
    </div>
  );
}

export default App;