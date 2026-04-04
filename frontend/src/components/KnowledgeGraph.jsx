import { useEffect, useRef } from 'react';
import * as echarts from 'echarts';

function KnowledgeGraph({ data }) {
  const chartRef = useRef(null);
  const chartInstance = useRef(null);

  useEffect(() => {
    if (!chartRef.current || !data) return;

    chartInstance.current = echarts.init(chartRef.current);

    const chartData = convertToEChartsData(data);

    const option = {
      title: {
        text: '知识图谱',
        left: 'center',
      },
      tooltip: {
        formatter: (params) => {
          if (params.dataType === 'node') {
            return `${params.data.name}<br/>类型: ${params.data.type}`;
          } else {
            return `${params.data.source} → ${params.data.target}<br/>关系: ${params.data.relType}`;
          }
        },
      },
      legend: {
        data: getNodeTypes(data.nodes),
        left: 'left',
      },
      series: [
        {
          name: '知识图谱',
          type: 'graph',
          layout: 'force',
          roam: true,
          draggable: true,
          label: {
            show: true,
            position: 'right',
            formatter: '{b}',
          },
          force: {
            repulsion: 200,
            gravity: 0.1,
            edgeLength: [50, 200],
            layoutAnimation: true,
          },
          data: chartData.nodes,
          links: chartData.links,
          lineStyle: {
            width: 2,
            curveness: 0.3,
          },
          emphasis: {
            focus: 'adjacency',
            lineStyle: {
              width: 4,
            },
          },
          categories: getCategories(data.nodes),
          edgeLabel: {
            show: true,
            formatter: '{c}',
            fontSize: 10,
          },
          edgeSymbol: ['circle', 'arrow'],
        },
      ],
    };

    chartInstance.current.setOption(option);

    const handleResize = () => {
      chartInstance.current?.resize();
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chartInstance.current?.dispose();
    };
  }, [data]);

  const convertToEChartsData = (data) => {
    const nodes = (data.nodes || []).map((node, index) => ({
      id: index,
      name: node.name,
      type: node.type,
      symbolSize: 40,
    }));

    const links = (data.relations || []).map((rel) => {
      const sourceNode = nodes.find((n) => n.name === rel.from);
      const targetNode = nodes.find((n) => n.name === rel.to);
      
      if (sourceNode && targetNode) {
        return {
          source: sourceNode.id,
          target: targetNode.id,
          relType: rel.type,
          name: rel.type,
        };
      }
      return null;
    }).filter(Boolean);

    return { nodes, links };
  };

  const getNodeTypes = (nodes) => {
    const types = [...new Set((nodes || []).map((n) => n.type))];
    return types;
  };

  const getCategories = (nodes) => {
    const types = [...new Set((nodes || []).map((n) => n.type))];
    return types.map((type) => ({
      name: type,
    }));
  };

  return <div ref={chartRef} style={{ width: '100%', height: '100%', minHeight: '500px' }} />;
}

export default KnowledgeGraph;
