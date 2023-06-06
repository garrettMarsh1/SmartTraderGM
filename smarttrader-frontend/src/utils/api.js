import axios from 'axios';

const API_BASE_URL = 'http://localhost:5000';

export const getSymbols = async () => {
  const response = await axios.get(`${API_BASE_URL}/symbols`);
  return response.data;
};

export const updateSymbols = async (symbols) => {
  const response = await axios.post(`${API_BASE_URL}/symbols`, { symbols });
  return response.data;
};

export const getPositions = async () => {
  const response = await axios.get(`${API_BASE_URL}/portfolio/positions`);
  return response.data;
};

export const addPosition = async (symbol, shares, buyPrice) => {
  const response = await axios.post(`${API_BASE_URL}/portfolio/position`, { symbol, shares, buyPrice });
  return response.data;
};

export const removePosition = async () => {
  const response = await axios.delete(`${API_BASE_URL}/portfolio/position`);
  return response.data;
};

export const buyStock = async (symbol) => {
  const response = await axios.post(`${API_BASE_URL}/portfolio/buy`, { symbol });
  return response.data;
};

export const sellStock = async (symbol) => {
  const response = await axios.post(`${API_BASE_URL}/portfolio/sell`, { symbol });
  return response.data;
};

export const getTotalValue = async () => {
  const response = await axios.get(`${API_BASE_URL}/portfolio/get_total_value`);
  return response.data;
};

export const getCash = async () => {
  const response = await axios.get(`${API_BASE_URL}/portfolio/get_buying_power`);
  return response.data;
};

export const getHistory = async (symbol) => {
  const response = await axios.get(`${API_BASE_URL}/portfolio/get_history/${symbol}`);
  return response.data;
};

export const getAssetInfo = async (symbol) => {
  const response = await axios.get(`${API_BASE_URL}/portfolio/get_asset_info/${symbol}`);
  return response.data;
};