import React, { useState, useEffect } from 'react';
import { Box, Text, VStack, Button, Input } from '@chakra-ui/react';
import { getAssetInfo } from '../utils/api';

const AssetInfo = () => {
  const [symbol, setSymbol] = useState('');
  const [assetInfo, setAssetInfo] = useState(null);

  const fetchAssetInfo = async () => {
    try {
      const response = await getAssetInfo(symbol);
      setAssetInfo(response.data);
    } catch (error) {
      console.error('Error fetching asset info:', error);
    }
  };

  useEffect(() => {
    if (symbol) {
      fetchAssetInfo();
    }
  }, [symbol]);

  return (
    <VStack spacing={4}>
      <Text fontSize="2xl">Asset Information</Text>
      <Input
        placeholder="Enter symbol"
        value={symbol}
        onChange={(e) => setSymbol(e.target.value)}
      />
      <Button onClick={fetchAssetInfo}>Get Asset Info</Button>
      {assetInfo && (
        <Box>
          <Text>Symbol: {assetInfo.symbol}</Text>
          <Text>Name: {assetInfo.name}</Text>
          <Text>Exchange: {assetInfo.exchange}</Text>
          <Text>Asset Class: {assetInfo.asset_class}</Text>
          <Text>Status: {assetInfo.status}</Text>
          <Text>Tradable: {assetInfo.tradable ? 'Yes' : 'No'}</Text>
        </Box>
      )}
    </VStack>
  );
};

export default AssetInfo;