const config = require('../config');
const apiClient = require('../services/apiClient');
const logger = require('../utils/logger');
const { getUserDocument } = require('./documentHandler');
const { handleQuery } = require('./queryHandler');
const { EMOJIS, formatExtraction, formatCompliance, formatStatus, formatError, splitMessage } = require('../utils/formatter');
const PersistentStore = require('../store/persistentStore');

const userPreferences = new PersistentStore('user_preferences');

async function handleCommand(message, userId, command, args) {
  const chat = await message.getChat();
  const lang = getUserLang(userId);

  try {
    switch (command.toLowerCase()) {
      case 'help':
        await sendHelp(chat, lang);
        break;
      case 'extract':
        await handleExtract(chat, userId, lang);
        break;
      case 'compliance':
        await handleCompliance(chat, userId, lang);
        break;
      case 'ask':
        if (!args) {
          const msg = lang === 'hi'
            ? `${EMOJIS.question} कृपया सवाल लिखें:\n_उदाहरण: /ask यह दस्तावेज़ किसका है?_`
            : `${EMOJIS.question} Please provide your question:\n_Example: /ask What is the total amount?_`;
          await chat.sendMessage(msg);
          return;
        }
        await handleQuery(message, userId, args, lang);
        break;
      case 'status':
        await handleStatus(chat, userId, lang);
        break;
      case 'language':
      case 'lang':
        await handleLanguage(chat, userId, args, lang);
        break;
      default:
        const unknownMsg = lang === 'hi'
          ? `${EMOJIS.warning} अज्ञात कमांड: /${command}\n/help टाइप करें।`
          : `${EMOJIS.warning} Unknown command: /${command}\nType /help to see commands.`;
        await chat.sendMessage(unknownMsg);
    }
  } catch (error) {
    logger.error('Command error:', { userId, command, error: error.message });
    await chat.sendMessage(formatError(error.message, lang));
  }
}

async function sendHelp(chat, lang) {
  if (lang === 'hi') {
    await chat.sendMessage(`${EMOJIS.help} *DocSetu AI - सहायता*\n${'─'.repeat(20)}\n\n📄 *दस्तावेज़ भेजें* — PDF/Image भेजकर शुरू करें\n\n*कमांड:*\n📋 */extract* — डेटा निकालें\n🔍 */compliance* — अनुपालन जांच\n❓ */ask [सवाल]* — दस्तावेज़ के बारे में पूछें\n🕐 */status* — स्थिति देखें\n🌐 */language [en/hi]* — भाषा बदलें\n📖 */help* — यह संदेश\n\nℹ️ _सीधे सवाल भी टाइप कर सकते हैं!_`);
  } else {
    await chat.sendMessage(`${EMOJIS.help} *DocSetu AI - Help*\n${'─'.repeat(20)}\n\n📄 *Send a Document* — Send PDF/Image to start\n\n*Commands:*\n📋 */extract* — Extract data\n🔍 */compliance* — Compliance check\n❓ */ask [question]* — Ask about document\n🕐 */status* — Processing status\n🌐 */language [en/hi]* — Change language\n📖 */help* — This message\n\nℹ️ _You can also just type a question directly!_`);
  }
}

async function handleExtract(chat, userId, lang) {
  const doc = getUserDocument(userId);
  if (!doc) {
    const msg = lang === 'hi'
      ? `${EMOJIS.warning} कोई दस्तावेज़ नहीं। पहले एक दस्तावेज़ भेजें।`
      : `${EMOJIS.warning} No document found. Send a document first.`;
    await chat.sendMessage(msg);
    return;
  }
  await chat.sendMessage(`${EMOJIS.processing} Extracting from *${doc.fileName}*...`);
  const results = await apiClient.getExtractionResults(doc.documentId);
  const messages = splitMessage(formatExtraction(results, lang));
  for (const msg of messages) await chat.sendMessage(msg);
}

async function handleCompliance(chat, userId, lang) {
  const doc = getUserDocument(userId);
  if (!doc) {
    const msg = lang === 'hi'
      ? `${EMOJIS.warning} कोई दस्तावेज़ नहीं। पहले एक दस्तावेज़ भेजें।`
      : `${EMOJIS.warning} No document found. Send a document first.`;
    await chat.sendMessage(msg);
    return;
  }
  await chat.sendMessage(`${EMOJIS.processing} Running compliance check...`);
  const report = await apiClient.getComplianceReport(doc.documentId);
  const messages = splitMessage(formatCompliance(report, lang));
  for (const msg of messages) await chat.sendMessage(msg);
}

async function handleStatus(chat, userId, lang) {
  const doc = getUserDocument(userId);
  if (!doc) {
    const msg = lang === 'hi'
      ? `${EMOJIS.info} कोई सक्रिय दस्तावेज़ नहीं।`
      : `${EMOJIS.info} No active document being processed.`;
    await chat.sendMessage(msg);
    return;
  }
  const status = await apiClient.getStatus(doc.documentId);
  await chat.sendMessage(formatStatus(status, lang));
}

async function handleLanguage(chat, userId, args, currentLang) {
  const newLang = (args || '').trim().toLowerCase();
  if (!newLang) {
    const msg = currentLang === 'hi'
      ? `${EMOJIS.language} वर्तमान: *हिंदी*\n/language en — English\n/language hi — हिंदी`
      : `${EMOJIS.language} Current: *English*\n/language en — English\n/language hi — हिंदी`;
    await chat.sendMessage(msg);
    return;
  }
  if (!config.language.supported.includes(newLang)) {
    await chat.sendMessage(`${EMOJIS.warning} Supported: en (English), hi (हिंदी)`);
    return;
  }
  setUserLang(userId, newLang);
  const confirmMsg = newLang === 'hi'
    ? `${EMOJIS.success} भाषा हिंदी में बदल दी गई!`
    : `${EMOJIS.success} Language changed to English!`;
  await chat.sendMessage(confirmMsg);
}

function getUserLang(userId) {
  const prefs = userPreferences.get(userId);
  return prefs?.language || config.language.default;
}

function setUserLang(userId, lang) {
  const prefs = userPreferences.get(userId) || {};
  prefs.language = lang;
  userPreferences.set(userId, prefs);
}


module.exports = { handleCommand, getUserLang, setUserLang };
