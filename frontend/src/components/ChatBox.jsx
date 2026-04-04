import { useState, useRef, useEffect } from 'react';

function ChatBox({ messages, loading, onSend }) {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim() && !loading) {
      onSend(input);
      setInput('');
    }
  };

  return (
    <div className="chat-box">
      <div className="messages-container">
        {messages.length === 0 && (
          <div className="empty-state">
            <p>👋 欢迎使用知识库问答系统</p>
            <p>请先上传文档，然后输入问题进行问答</p>
          </div>
        )}

        {messages.map((msg, index) => (
          <div key={index} className={`message message-${msg.role}`}>
            <div className="message-avatar">
              {msg.role === 'user' ? '👤' : '🤖'}
            </div>
            <div className="message-content">
              <div className="message-text">{msg.content}</div>
              
              {msg.sources && msg.sources.length > 0 && (
                <div className="sources">
                  <p>📚 参考文档：</p>
                  {msg.sources.map((src, i) => (
                    <div key={i} className="source-item">
                      <span className="score">相关度: {(src.score * 100).toFixed(1)}%</span>
                      <p className="source-content">{src.content}</p>
                    </div>
                  ))}
                </div>
              )}

              {msg.graphEntities && msg.graphEntities.length > 0 && (
                <div className="graph-entities">
                  <p>🔗 关联实体：</p>
                  <div className="entity-tags">
                    {msg.graphEntities.map((entity, i) => (
                      <span key={i} className="entity-tag">
                        {entity.name} ({entity.type})
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="message message-assistant">
            <div className="message-avatar">🤖</div>
            <div className="message-content">
              <div className="loading-dots">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <form className="input-form" onSubmit={handleSubmit}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="输入您的问题..."
          disabled={loading}
        />
        <button type="submit" disabled={loading || !input.trim()}>
          发送
        </button>
      </form>
    </div>
  );
}

export default ChatBox;
