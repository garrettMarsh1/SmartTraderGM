import React, { useState, useEffect } from 'react';
import { Line } from 'react-chartjs-2';
import { Box } from '@chakra-ui/react';
import { io } from 'socket.io-client';

const RealtimeChart = () => {
    const [chartData, setChartData] = useState([]);

    useEffect(() => {
        const socket = io.connect('http://localhost:3001');

        socket.on('chart_data', (data) => {
            const parsedData = JSON.parse(data);
            const formattedData = {
                labels: parsedData.index,
                datasets: [
                    {
                        label: 'SMA 50',
                        data: parsedData.data.map(item => item.sma_50),
                        borderColor: 'rgba(75,192,192,1)',
                    },
                    {
                        label: 'SMA 200',
                        data: parsedData.data.map(item => item.sma_200),
                        borderColor: 'rgba(255,99,132,1)',
                    },
                    {
                        label: 'upper_bb',
                        data: parsedData.data.map(item => item.upper_bb),
                        borderColor: 'rgba(255,99,132,1)',
                    },
                    {
                        label: 'middle_bb',
                        data: parsedData.data.map(item => item.lower_bb),
                        borderColor: 'rgba(255,99,132,1)',
                    },
                    {
                        label: 'lower_bb',
                        data: parsedData.data.map(item => item.lower_bb),
                        borderColor: 'rgba(255,99,132,1)',
                    },

                ],
            };
            setChartData(formattedData);
        });

        return () => {
            socket.disconnect();
        };
    }, []);

    const options = {
        scales: {
            x: {
                type: 'time',
                time: {
                    unit: 'minute',
                },
            },
            y: {
                beginAtZero: true,
            },
        },
    };

    return (
        <Box>
            <h2>Real-Time Chart</h2>
            <Line data={chartData} options={options} />
        </Box>
    );
};

export default RealtimeChart;