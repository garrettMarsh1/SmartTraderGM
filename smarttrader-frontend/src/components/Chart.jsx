import React, { useEffect, useState } from 'react';
import { Line } from 'react-chartjs-2';
import { Box } from '@chakra-ui/react';
import { useSocket } from '../utils/socket';

const Chart = () => {
  const [chartData, setChartData] = useState({});
  const socket = useSocket();

  useEffect(() => {
    if (socket) {
      socket.on('market_data', (data) => {
        const parsedData = JSON.parse(data.data);
        const labels = Object.keys(parsedData);
        const closePrices = labels.map((label) => parsedData[label].close);

        setChartData({
          labels: labels,
          datasets: [
            {
              label: data.symbol,
              data: closePrices,
              fill: false,
              backgroundColor: 'rgba(75,192,192,0.4)',
              borderColor: 'rgba(75,192,192,1)',
            },
          ],
        });
      });
    }

    return () => {
      if (socket) {
        socket.off('market_data');
      }
    };
  }, [socket]);

  return (
    <Box>
      <Line
        data={chartData}
        options={{
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            x: {
              type: 'time',
              time: {
                unit: 'day',
              },
            },
          },
        }}
      />
    </Box>
  );
};

export default Chart;