import React, { useState, useEffect } from 'react';
import { Box, Text, VStack, Button, Input } from '@chakra-ui/react';
import { Line } from 'react-chartjs-2';
import { getHistory } from '../utils/api';

const HistoricalData = () => {
  const [symbol, setSymbol] = useState('');
  const [history, setHistory] = useState([]);
  const [chartData, setChartData] = useState({});

  useEffect(() => {
    if (history.length > 0) {
      setChartData({
        labels: history.map((data) => data.date),
        datasets: [
          {
            label: 'Price',
            data: history.map((data) => data.close),
            backgroundColor: 'rgba(75, 192, 192, 0.6)',
            borderColor: 'rgba(75, 192, 192, 1)',
            borderWidth: 1,
          },
        ],
      });
    }
  }, [history]);

  const fetchHistory = async () => {
    const response = await getHistory(symbol);
    setHistory(response.history);
  };

  return (
    <VStack spacing={4}>
      <Text fontSize="2xl">Historical Data</Text>
      <Box>
        <Input
          placeholder="Enter symbol"
          value={symbol}
          onChange={(e) => setSymbol(e.target.value)}
        />
        <Button onClick={fetchHistory}>Fetch History</Button>
      </Box>
      {chartData && (
        <Line
          data={chartData}
          options={{
            responsive: true,
            scales: {
              y: {
                beginAtZero: true,
              },
            },
          }}
        />
      )}
    </VStack>
  );
};

export default HistoricalData;