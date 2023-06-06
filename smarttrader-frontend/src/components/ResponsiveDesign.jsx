import React from 'react';
import { Box } from '@chakra-ui/react';
import Chart from './Chart';
import SymbolManagement from './SymbolManagement';
import PortfolioManagement from './PortfolioManagement';
import TradingOperations from './TradingOperations';
import HistoricalData from './HistoricalData';
import AssetInfo from './AssetInfo';

const ResponsiveDesign = () => {
  return (
    <Box display={{ base: 'block', md: 'flex' }}>
      <Box flex="1" marginRight={{ md: '4' }}>
        <Chart />
        <SymbolManagement />
        <PortfolioManagement />
      </Box>
      <Box flex="1">
        <TradingOperations />
        <HistoricalData />
        <AssetInfo />
      </Box>
    </Box>
  );
};

export default ResponsiveDesign;