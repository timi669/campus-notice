// utils/config.js
const env = 'dev'; // dev / prod

const configMap = {
  dev: {
    baseUrl: 'http://127.0.0.1:8000',
  },
  prod: {
    baseUrl: 'https://your-domain.com',
  },
};

module.exports = {
  env,
  baseUrl: configMap[env].baseUrl,
  pageSize: 10,
};
