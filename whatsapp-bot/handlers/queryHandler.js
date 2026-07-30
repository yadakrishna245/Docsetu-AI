const apiClient = require('../services/apiClient');
const logger = require('../utils/logger');
const { getUserDocument } = require('./documentHandler');
const { EMOJIS, formatError, splitMessage } = require('../utils/formatter');
const PersistentStore = require('../store/persistentStore');

const conversationContext = new PersistentStore('conversation_context');

async function handleQuery(message, userId, question, lang = 'en') {
  const chat = await message.getChat();

  try {
    const doc = getUserDocument(userId);

    if (!doc) {
      const msg = lang === 'hi'
        ? `${EMOJIS.warning} कोई दस्तावेज़ नहीं मिला। पहले एक दस्तावेज़ भेजें।`
        : `${EMOJIS.warning} No document found. Please send a document first.`;
      await chat.sendMessage(msg);
      return;
    }

    await chat.sendStateTyping();

    const response = await apiClient.submitQuery(doc.documentId, question, lang);
    addToContext(userId, question, response.answer);

    const answer = formatAnswer(response, lang);
    const messages = splitMessage(answer);

    for (const msg of messages) {
      await chat.sendMessage(msg);
    }

    logger.info('Query answered', { userId, question: question.substring(0, 50) });
  } catch (error) {
    logger.error('Query error:', { userId, question, error: error.message });
    const errMsg = lang === 'hi'
      ? 'जवाब देने में समस्या हुई। कृपया पुनः प्रयास करें।'
      : 'Problem answering your question. Please try again.';
    await chat.sendMessage(formatError(errMsg, lang));
  }
}

function formatAnswer(response, lang) {
  let msg = `${EMOJIS.answer} `;
  msg += response.answer || (lang === 'hi' ? 'कोई उत्तर नहीं मिला।' : 'No answer found.');

  if (response.confidence && Math.round(response.confidence * 100) < 70) {
    const conf = Math.round(response.confidence * 100);
    msg += lang === 'hi'
      ? `\n\n_${EMOJIS.warning} विश्वास: ${conf}%_`
      : `\n\n_${EMOJIS.warning} Confidence: ${conf}%_`;
  }

  if (response.suggestions && response.suggestions.length > 0) {
    msg += lang === 'hi' ? '\n\n*सुझाव:*' : '\n\n*Follow-ups:*';
    response.suggestions.slice(0, 3).forEach((s) => {
      msg += `\n• _${s}_`;
    });
  }

  return msg;
}

function addToContext(userId, question, answer) {
  const context = conversationContext.get(userId) || [];
  context.push({ question, answer, timestamp: Date.now() });
  if (context.length > 5) context.shift();
  conversationContext.set(userId, context);
}

function clearContext(userId) {
  conversationContext.delete(userId);
}


module.exports = { handleQuery, clearContext };
