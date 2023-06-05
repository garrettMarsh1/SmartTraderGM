import React, { useState, useEffect } from 'react';
import { Box } from '@chakra-ui/react';
import axios from 'axios';
import io from 'socket.io-client';
import RealtimeChart from './RealtimeChart';
import SymbolTable from './SymbolTable';
import MarketRegimeData from './MarketRegimeData'

const TradingInterface = () => {
    const [positions, setPositions] = useState([]);
    const [chartData, setChartData] = useState([]);
    const [symbols, setSymbols] = useState([]);

    useEffect(() => {
        axios.get('http://localhost:5000/api/portfolio')
            .then(response => {
                setPositions(response.data);
            });

        const socket = io.connect('/');

        socket.on('update', (data) => {
            setChartData(data.chartData);
            setSymbols(data.symbols);
        });

        return () => {
            socket.disconnect();
        };
    }, []);

    return (
        <Box>
            <RealtimeChart data={chartData} />
            <SymbolTable symbols={symbols} />
        </Box>
    );
};

export default TradingInterface;