import React from 'react';
import TradingInterface from './components/TradingInterface';
import './index.css';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>Trading Algorithm Monitoring</h1>
      </header>
      <main>
        <TradingInterface />
      </main>
    </div>
  );
}

export default App;