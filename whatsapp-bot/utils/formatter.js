/**
 * WhatsApp Message Formatter for DocSetu AI
 * Formats responses to be readable in WhatsApp's text-based interface.
 */

const MAX_MESSAGE_LENGTH = 4000; // WhatsApp limit is ~65k but keep it readable

const EMOJIS = {
  success: '✅',
  error: '❌',
  warning: '⚠️',
  info: 'ℹ️',
  document: '📄',
  processing: '⏳',
  done: '🎉',
  extract: '📋',
  compliance: '🔍',
  question: '❓',
  answer: '💡',
  language: '🌐',
  help: '📖',
  star: '⭐',
  rocket: '🚀',
  clock: '🕐',
  check: '☑️',
  cross: '☒',
  arrow: '➤',
  bullet: '•',
};

/**
 * Format a table as aligned text for WhatsApp
 */
function formatTable(headers, rows) {
  if (!rows || rows.length === 0) return '_No data available_';

  let output = '';
  // Simple key-value style for WhatsApp readability
  rows.forEach((row, idx) => {
    if (rows.length > 1) {
      output += `\n*${idx + 1}.*\n`;
    }
    headers.forEach((header, i) => {
      output += `  ${EMOJIS.bullet} *${header}:* ${row[i] || '-'}\n`;
    });
  });

  return output.trim();
}

/**
 * Format extraction results
 */
function formatExtraction(data, lang = 'en') {
  const title = lang === 'hi' ? '📋 *निष्कर्षण परिणाम*' : '📋 *Extraction Results*';
  let msg = `${title}\n${'─'.repeat(25)}\n\n`;

  if (data.fields && Array.isArray(data.fields)) {
    data.fields.forEach((field) => {
      const confidence = field.confidence
        ? ` (${Math.round(field.confidence * 100)}%)`
        : '';
      msg += `${EMOJIS.arrow} *${field.label}:* ${field.value}${confidence}\n`;
    });
  }

  if (data.summary) {
    const summaryLabel = lang === 'hi' ? 'सारांश' : 'Summary';
    msg += `\n${EMOJIS.star} *${summaryLabel}:*\n${data.summary}`;
  }

  return msg;
}

/**
 * Format compliance report
 */
function formatCompliance(report, lang = 'en') {
  const title = lang === 'hi' ? '🔍 *अनुपालन रिपोर्ट*' : '🔍 *Compliance Report*';
  const statusEmoji = report.passed ? EMOJIS.success : EMOJIS.warning;
  const statusText = report.passed
    ? (lang === 'hi' ? 'पास' : 'PASSED')
    : (lang === 'hi' ? 'समस्याएं मिलीं' : 'ISSUES FOUND');

  let msg = `${title}\n${'─'.repeat(25)}\n\n`;
  msg += `${statusEmoji} *Status:* ${statusText}\n\n`;

  if (report.checks && Array.isArray(report.checks)) {
    report.checks.forEach((check) => {
      const icon = check.passed ? EMOJIS.check : EMOJIS.cross;
      msg += `${icon} ${check.name}\n`;
      if (!check.passed && check.reason) {
        msg += `   _${check.reason}_\n`;
      }
    });
  }

  if (report.score !== undefined) {
    const scoreLabel = lang === 'hi' ? 'स्कोर' : 'Score';
    msg += `\n${EMOJIS.star} *${scoreLabel}:* ${report.score}/100`;
  }

  return msg;
}

/**
 * Truncate and split long messages
 */
function splitMessage(text, maxLength = MAX_MESSAGE_LENGTH) {
  if (text.length <= maxLength) return [text];

  const messages = [];
  let remaining = text;

  while (remaining.length > 0) {
    if (remaining.length <= maxLength) {
      messages.push(remaining);
      break;
    }

    // Find a good split point (newline or space)
    let splitAt = remaining.lastIndexOf('\n', maxLength);
    if (splitAt === -1 || splitAt < maxLength * 0.5) {
      splitAt = remaining.lastIndexOf(' ', maxLength);
    }
    if (splitAt === -1) {
      splitAt = maxLength;
    }

    messages.push(remaining.substring(0, splitAt));
    remaining = remaining.substring(splitAt).trimStart();
  }

  // Add continuation markers
  if (messages.length > 1) {
    messages.forEach((msg, i) => {
      if (i < messages.length - 1) {
        messages[i] += `\n\n_...continued (${i + 1}/${messages.length})_`;
      }
    });
  }

  return messages;
}

/**
 * Format error message
 */
function formatError(error, lang = 'en') {
  const title = lang === 'hi' ? 'त्रुटि' : 'Error';
  return `${EMOJIS.error} *${title}:* ${error}`;
}

/**
 * Format processing status
 */
function formatStatus(status, lang = 'en') {
  const states = {
    queued: { emoji: EMOJIS.clock, en: 'Queued', hi: 'कतार में' },
    processing: { emoji: EMOJIS.processing, en: 'Processing...', hi: 'प्रोसेसिंग...' },
    completed: { emoji: EMOJIS.done, en: 'Completed!', hi: 'पूर्ण!' },
    failed: { emoji: EMOJIS.error, en: 'Failed', hi: 'विफल' },
  };

  const state = states[status.state] || states.processing;
  const label = lang === 'hi' ? state.hi : state.en;

  let msg = `${state.emoji} *Status:* ${label}`;
  if (status.progress) {
    msg += ` (${status.progress}%)`;
  }
  return msg;
}

/**
 * Format welcome message
 */
function formatWelcome(lang = 'en') {
  if (lang === 'hi') {
    return `${EMOJIS.rocket} *DocSetu AI में आपका स्वागत है!*

मैं आपके दस्तावेज़ों को समझने में मदद करता हूँ।

${EMOJIS.bullet} कोई भी दस्तावेज़ (PDF/Image) भेजें
${EMOJIS.bullet} /help टाइप करें सभी कमांड देखने के लिए
${EMOJIS.bullet} हिंदी या English में बात करें

आप क्या करना चाहेंगे? ${EMOJIS.question}`;
  }

  return `${EMOJIS.rocket} *Welcome to DocSetu AI!*

I help you understand and extract data from documents.

${EMOJIS.bullet} Send any document (PDF/Image)
${EMOJIS.bullet} Type /help to see all commands
${EMOJIS.bullet} Chat in Hindi or English

What would you like to do? ${EMOJIS.question}`;
}

module.exports = {
  EMOJIS,
  formatTable,
  formatExtraction,
  formatCompliance,
  splitMessage,
  formatError,
  formatStatus,
  formatWelcome,
  MAX_MESSAGE_LENGTH,
};
