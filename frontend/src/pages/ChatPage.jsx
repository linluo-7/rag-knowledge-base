import { useState } from 'react';
import { chat, uploadDocument } from '../api';
import ChatBox from '../components/ChatBox';
import UploadModal from '../components/UploadModal';

function ChatPage() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showUpload, setShowUpload] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadLoading, setUploadLoading] = useState(false);

  const handleSend = async (question) => {
    if (!question.trim()) return;

    setMessages(prev => [...prev, { role: 'user', content: question }]);
    setLoading(true);

    try {
      const response = await chat(question);
      
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: response.answer,
        sources: response.sources,
        graphEntities: response.graph_entities,
      }]);
    } catch (error) {
      console.error('问答失败:', error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: '抱歉，发生了错误，请稍后重试。',
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (file) => {
    setUploadLoading(true);
    setUploadProgress(0);

    try {
      const result = await uploadDocument(file, setUploadProgress);
      alert(`文档上传成功！\n${result.message}`);
      setShowUpload(false);
    } catch (error) {
      console.error('上传失败:', error);
      alert('文档上传失败，请稍后重试。');
    } finally {
      setUploadLoading(false);
      setUploadProgress(0);
    }
  };

  return (
    <div className="chat-page">
      <header className="chat-header">
        <h1>💬 知识库问答</h1>
        <button onClick={() => setShowUpload(true)}>上传文档</button>
      </header>

      <ChatBox
        messages={messages}
        loading={loading}
        onSend={handleSend}
      />

      {showUpload && (
        <UploadModal
          onClose={() => setShowUpload(false)}
          onUpload={handleUpload}
          progress={uploadProgress}
          loading={uploadLoading}
        />
      )}
    </div>
  );
}

export default ChatPage;
