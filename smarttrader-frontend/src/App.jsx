import React, { useEffect, useState } from 'react';
import { ChakraProvider, Box } from '@chakra-ui/react';
import { io } from 'socket.io-client';

import Chart from './components/Chart';
import SymbolManagement from './components/SymbolManagement';
import PortfolioManagement from './components/PortfolioManagement';
import TradingOperations from './components/TradingOperations';
import HistoricalData from './components/HistoricalData';
import AssetInfo from './components/AssetInfo';

import { getSymbols } from './utils/api';
import { SOCKET_SERVER_URL } from './utils/socket';

function App() {
  const [symbols, setSymbols] = useState([]);
  const [marketData, setMarketData] = useState({});

  useEffect(() => {
    getSymbols().then((response) => {
      setSymbols(response.data);
    });

    const socket = io(SOCKET_SERVER_URL);

    socket.on('market_data', (data) => {
      setMarketData((prevData) => ({
        ...prevData,
        [data.symbol]: data.data,
      }));
    });

    return () => {
      socket.disconnect();
    };
  }, []);

  return (
    <ChakraProvider>
      <Box>
        <SymbolManagement symbols={symbols} setSymbols={setSymbols} />
        <PortfolioManagement />
        <TradingOperations />
        <Chart marketData={marketData} />
        <HistoricalData />
        <AssetInfo />
      </Box>
    </ChakraProvider>
  );
}

export default App;