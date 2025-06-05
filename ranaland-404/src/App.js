import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import './App.css'; 

import Home from './pages/Home';
function App() {
  return (
    <Router>
      <div className="container">
        <div className="body">
          
          
          <Routes>
            <Route path="/" element={<Home />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;