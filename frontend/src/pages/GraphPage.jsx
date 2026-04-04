import { useState, useEffect } from 'react';
import { getGraphData, searchGraph } from '../api';
import KnowledgeGraph from '../components/KnowledgeGraph';

function GraphPage() {
  const [graphData, setGraphData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchKeyword, setSearchKeyword] = useState('');
  const [filteredData, setFilteredData] = useState(null);

  useEffect(() => {
    loadGraphData();
  }, []);

  const loadGraphData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const data = await getGraphData();
      setGraphData(data.data);
      setFilteredData(data.data);
    } catch (err) {
      console.error('加载图谱失败:', err);
      setError('加载图谱数据失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchKeyword.trim()) {
      setFilteredData(graphData);
      return;
    }

    try {
      const data = await searchGraph(searchKeyword);
      setFilteredData({
        nodes: data.nodes || [],
        relations: data.relations || [],
      });
    } catch (err) {
      console.error('搜索失败:', err);
    }
  };

  return (
    <div className="graph-page">
      <header className="graph-header">
        <h1>🕸️ 知识图谱</h1>
        <div className="search-box">
          <input
            type="text"
            value={searchKeyword}
            onChange={(e) => setSearchKeyword(e.target.value)}
            placeholder="搜索节点..."
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          />
          <button onClick={handleSearch}>搜索</button>
        </div>
        <button onClick={loadGraphData} className="refresh-btn">
          🔄 刷新
        </button>
      </header>

      <div className="graph-stats">
        {filteredData && (
          <>
            <span>📍 节点数: {filteredData.nodes?.length || 0}</span>
            <span>🔗 关系数: {filteredData.relations?.length || 0}</span>
          </>
        )}
      </div>

      <div className="graph-container">
        {loading && (
          <div className="loading">
            <div className="loading-dots">
              <span></span><span></span><span></span>
            </div>
            <p>加载图谱数据中...</p>
          </div>
        )}

        {error && (
          <div className="error">
            <p>{error}</p>
            <button onClick={loadGraphData}>重试</button>
          </div>
        )}

        {!loading && !error && filteredData && (
          <KnowledgeGraph data={filteredData} />
        )}
      </div>
    </div>
  );
}

export default GraphPage;
