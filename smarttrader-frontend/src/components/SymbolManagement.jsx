import React, { useState, useEffect } from 'react';
import { Box, Button, Input, VStack, HStack, Text } from '@chakra-ui/react';
import axios from 'axios';

const SymbolManagement = () => {
  const [symbols, setSymbols] = useState([]);
  const [newSymbol, setNewSymbol] = useState('');

  useEffect(() => {
    fetchSymbols();
  }, []);

  const fetchSymbols = async () => {
    try {
      const response = await axios.get('/symbols');
      setSymbols(response.data);
    } catch (error) {
      console.error('Error fetching symbols:', error);
    }
  };

  const updateSymbols = async () => {
    try {
      await axios.post('/symbols', { symbols });
      fetchSymbols();
    } catch (error) {
      console.error('Error updating symbols:', error);
    }
  };

  const addSymbol = () => {
    if (newSymbol && !symbols.includes(newSymbol.toUpperCase())) {
      setSymbols([...symbols, newSymbol.toUpperCase()]);
      setNewSymbol('');
    }
  };

  const removeSymbol = (symbol) => {
    setSymbols(symbols.filter((s) => s !== symbol));
  };

  useEffect(() => {
    updateSymbols();
  }, [symbols]);

  return (
    <Box>
      <VStack spacing={4}>
        <Text fontSize="xl">Symbol Management</Text>
        <HStack>
          <Input
            value={newSymbol}
            onChange={(e) => setNewSymbol(e.target.value)}
            placeholder="Add symbol"
          />
          <Button onClick={addSymbol}>Add</Button>
        </HStack>
        <VStack spacing={2}>
          {symbols.map((symbol) => (
            <HStack key={symbol}>
              <Text>{symbol}</Text>
              <Button size="xs" onClick={() => removeSymbol(symbol)}>
                Remove
              </Button>
            </HStack>
          ))}
        </VStack>
      </VStack>
    </Box>
  );
};

export default SymbolManagement;