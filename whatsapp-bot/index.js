require('dotenv').config();

const { Client, LocalAuth, MessageMedia } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const express = require('express');
const config = require('./config');
const logger = require('./utils/logger');
const { formatWelcome, formatError, EMOJIS } = require('./utils/formatter');
const { handleDocument } = require('./handlers/documentHandler');
const { handleCommand, getUserLang } = require('./handlers/commandHandler');
const { handleQuery } = require('./handlers/queryHandler');

// Rate limiting store
const rateLimiter = new Map();

// Initialize WhatsApp client
const client = new Client({
  authStrategy: new LocalAuth({ dataPath: config.bot.sessionPath }),
  puppeteer: {
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  },
});

// QR Code Authentication
client.on('qr', (qr) => {
  logger.info('QR Code generated. Scan with WhatsApp:');
  qrcode.generate(qr, { small: true });
  console.log('\n📱 Scan this QR code with WhatsApp to login\n');
});

client.on('ready', () => {
  logger.info('✅ DocSetu AI WhatsApp Bot is ready!');
  console.log(`\n${EMOJIS.rocket} Bot is online and ready to receive messages!\n`);
});

client.on('authenticated', () => {
  logger.info('WhatsApp authentication successful');
});

client.on('auth_failure', (msg) => {
  logger.error('Authentication failed:', msg);
  console.error('❌ Auth failed. Delete session folder and restart.');
});

client.on('disconnected', (reason) => {
  logger.warn('Client disconnected:', reason);
});

// Main message handler
client.on('message', async (message) => {
  try {
    const userId = message.from;

    // Skip group messages and status updates
    if (message.from.includes('@g.us') || message.isStatus) return;

    // Rate limiting
    if (!checkRateLimit(userId)) {
      const lang = getUserLang(userId);
      const msg = lang === 'hi'
        ? `${EMOJIS.warning} बहुत तेज़! कृपया कुछ सेकंड रुकें।`
        : `${EMOJIS.warning} Too fast! Please wait a few seconds.`;
      await message.reply(msg);
      return;
    }

    // Handle documents/media
    if (message.hasMedia) {
      const lang = getUserLang(userId);
      await handleDocument(message, userId, lang);
      return;
    }

    const body = message.body.trim();
    if (!body) return;

    // Handle commands (starting with /)
    if (body.startsWith('/')) {
      const parts = body.substring(1).split(' ');
      const command = parts[0];
      const args = parts.slice(1).join(' ');
      await handleCommand(message, userId, command, args);
      return;
    }

    // Handle greeting / first message
    if (isGreeting(body)) {
      const lang = getUserLang(userId);
      await message.reply(formatWelcome(lang));
      return;
    }

    // Treat plain text as a question about the document
    const lang = getUserLang(userId);
    await handleQuery(message, userId, body, lang);

  } catch (error) {
    logger.error('Message handler error:', { from: message.from, error: error.message });
    try {
      await message.reply(formatError('Something went wrong. Please try again.', 'en'));
    } catch (e) {
      logger.error('Failed to send error reply:', e.message);
    }
  }
});

// Rate limiter
function checkRateLimit(userId) {
  const now = Date.now();
  const userRate = rateLimiter.get(userId) || [];
  const recent = userRate.filter((t) => now - t < 60000);

  if (recent.length >= config.rateLimit.maxRequestsPerMinute) {
    return false;
  }

  recent.push(now);
  rateLimiter.set(userId, recent);
  return true;
}

// Greeting detection
function isGreeting(text) {
  const greetings = ['hi', 'hello', 'hey', 'hola', 'namaste', 'namaskar',
    'hii', 'start', 'begin', 'shuru'];
  return greetings.includes(text.toLowerCase());
}

// Health check server
const app = express();
app.get('/health', (req, res) => {
  res.json({ status: 'ok', bot: 'DocSetu AI WhatsApp Bot', uptime: process.uptime() });
});
app.listen(config.server.port, () => {
  logger.info(`Health check server on port ${config.server.port}`);
});

// Start the bot
logger.info('Starting DocSetu AI WhatsApp Bot...');
client.initialize();

// Graceful shutdown
process.on('SIGINT', async () => {
  logger.info('Shutting down...');
  await client.destroy();
  process.exit(0);
});
