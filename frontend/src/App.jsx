import { useState } from 'react'
import ChatPage from './pages/ChatPage'
import GraphPage from './pages/GraphPage'
import './App.css'

function App() {
  const [currentPage, setCurrentPage] = useState('chat')

  return (
    <div className="app">
      <nav className="nav">
        <button
          className={currentPage === 'chat' ? 'active' : ''}
          onClick={() => setCurrentPage('chat')}
        >
          💬 问答
        </button>
        <button
          className={currentPage === 'graph' ? 'active' : ''}
          onClick={() => setCurrentPage('graph')}
        >
          🕸️ 图谱
        </button>
      </nav>

      <main className="main-content">
        {currentPage === 'chat' && <ChatPage />}
        {currentPage === 'graph' && <GraphPage />}
      </main>
    </div>
  );
}

export default App
