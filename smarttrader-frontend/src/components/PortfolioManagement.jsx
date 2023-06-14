import React, { useState, useEffect } from 'react';
import { Box, Button, Flex, Text, VStack } from '@chakra-ui/react';
import axios from 'axios';

const PortfolioManagement = () => {
  const [positions, setPositions] = useState([]);
  const [totalValue, setTotalValue] = useState(0);
  const [cash, setCash] = useState(0);

  useEffect(() => {
    fetchPositions();
    fetchTotalValue();
    fetchCash();
  }, []);

  const fetchPositions = async () => {
    const response = await axios.get('/portfolio/positions');
    setPositions(response.data);
  };

  const fetchTotalValue = async () => {
    const response = await axios.get('/portfolio/get_total_value');
    setTotalValue(response.data.total_value);
  };

  const fetchCash = async () => {
    const response = await axios.get('/portfolio/get_cash');
    setCash(response.data.cash);
  };

  return (
    <Box>
      <Text fontSize="2xl" fontWeight="bold">
        Portfolio Management
      </Text>
      <VStack spacing={4}>
        {positions.map((position) => (
          <Flex key={position.symbol} justifyContent="space-between" w="100%">
            <Text>{position.symbol}</Text>
            <Text>{position.shares} shares</Text>
            <Text>${position.buy_price.toFixed(2)}</Text>
          </Flex>
        ))}
      </VStack>
      <Text fontSize="xl" fontWeight="bold" mt={4}>
        Total Value: ${totalValue.toFixed(2)}
      </Text>
      <Text fontSize="xl" fontWeight="bold">
        Cash: ${cash.toFixed(2)}
      </Text>
    </Box>
  );
};

export default PortfolioManagement;