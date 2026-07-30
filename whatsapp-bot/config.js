require('dotenv').config();

module.exports = {
  // Backend API
  api: {
    baseUrl: process.env.API_BASE_URL || 'http://localhost:8000',
    timeout: parseInt(process.env.API_TIMEOUT) || 30000,
    apiKey: process.env.API_KEY || '',
  },

  // WhatsApp Bot
  bot: {
    name: 'DocSetu AI',
    prefix: '/',
    sessionPath: './session',
    maxFileSize: parseInt(process.env.MAX_FILE_SIZE_MB) || 16, // MB
    supportedFormats: ['pdf', 'png', 'jpg', 'jpeg', 'tiff', 'bmp'],
  },

  // Rate Limiting
  rateLimit: {
    maxRequestsPerMinute: parseInt(process.env.RATE_LIMIT_PER_MIN) || 10,
    maxDocumentsPerHour: parseInt(process.env.DOC_LIMIT_PER_HOUR) || 20,
    cooldownMs: 3000,
  },

  // Language
  language: {
    default: 'en',
    supported: ['en', 'hi'],
  },

  // Server (for health checks / webhooks)
  server: {
    port: parseInt(process.env.PORT) || 3001,
  },

  // Logging
  logging: {
    level: process.env.LOG_LEVEL || 'info',
    file: process.env.LOG_FILE || 'logs/bot.log',
  },
};
