import React, { useState } from 'react';
import { Box, Button, FormControl, FormLabel, Input, Text } from '@chakra-ui/react';
import axios from 'axios';

const TradingOperations = () => {
  const [symbol, setSymbol] = useState('');
  const [message, setMessage] = useState('');

  const handleBuy = async () => {
    try {
      const response = await axios.post(`/portfolio/buy?symbol=${symbol}`);
      setMessage(`Successfully bought ${symbol}`);
    } catch (error) {
      setMessage(`Failed to buy ${symbol}`);
    }
  };

  const handleSell = async () => {
    try {
      const response = await axios.post(`/portfolio/sell?symbol=${symbol}`);
      setMessage(`Successfully sold ${symbol}`);
    } catch (error) {
      setMessage(`Failed to sell ${symbol}`);
    }
  };

  return (
    <Box>
      <FormControl>
        <FormLabel>Symbol</FormLabel>
        <Input
          type="text"
          value={symbol}
          onChange={(e) => setSymbol(e.target.value)}
          placeholder="Enter symbol"
        />
      </FormControl>
      <Button colorScheme="blue" onClick={handleBuy} mt={4}>
        Buy
      </Button>
      <Button colorScheme="red" onClick={handleSell} mt={4} ml={4}>
        Sell
      </Button>
      {message && (
        <Text mt={4} color={message.startsWith('Successfully') ? 'green.500' : 'red.500'}>
          {message}
        </Text>
      )}
    </Box>
  );
};

export default TradingOperations;