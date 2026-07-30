const config = require('../config');
const apiClient = require('../services/apiClient');
const logger = require('../utils/logger');
const { EMOJIS, formatError } = require('../utils/formatter');
const PersistentStore = require('../store/persistentStore');

// Persistent store of last document per user
const userDocuments = new PersistentStore('user_documents');

async function handleDocument(message, userId, lang = 'en') {
  const chat = await message.getChat();

  try {
    const media = await message.downloadMedia();
    if (!media) {
      const errMsg = lang === 'hi'
        ? 'दस्तावेज़ डाउनलोड नहीं हो सका। कृपया पुनः भेजें।'
        : 'Could not download the document. Please resend it.';
      await chat.sendMessage(formatError(errMsg, lang));
      return;
    }

    const fileSizeBytes = Buffer.from(media.data, 'base64').length;
    const fileSizeMB = fileSizeBytes / (1024 * 1024);

    if (fileSizeMB > config.bot.maxFileSize) {
      const errMsg = lang === 'hi'
        ? `फ़ाइल बहुत बड़ी है (${fileSizeMB.toFixed(1)}MB)। अधिकतम ${config.bot.maxFileSize}MB।`
        : `File too large (${fileSizeMB.toFixed(1)}MB). Max is ${config.bot.maxFileSize}MB.`;
      await chat.sendMessage(formatError(errMsg, lang));
      return;
    }

    const mimeType = media.mimetype || '';
    const extension = getExtension(mimeType, media.filename);

    if (!config.bot.supportedFormats.includes(extension)) {
      const errMsg = lang === 'hi'
        ? `यह फ़ाइल प्रकार (.${extension}) समर्थित नहीं है। PDF या Image भेजें।`
        : `File type (.${extension}) not supported. Please send PDF or Image.`;
      await chat.sendMessage(formatError(errMsg, lang));
      return;
    }

    const ackMsg = lang === 'hi'
      ? `${EMOJIS.document} दस्तावेज़ प्राप्त! ${EMOJIS.processing} प्रोसेस कर रहा हूँ...`
      : `${EMOJIS.document} Document received! ${EMOJIS.processing} Processing...`;
    await chat.sendMessage(ackMsg);

    const fileBuffer = Buffer.from(media.data, 'base64');
    const fileName = media.filename || `document_${Date.now()}.${extension}`;

    const uploadResult = await apiClient.uploadDocument(fileBuffer, fileName, mimeType, userId);

    userDocuments.set(userId, {
      documentId: uploadResult.document_id,
      fileName,
      uploadedAt: new Date(),
      status: 'uploaded',
    });

    const successMsg = lang === 'hi'
      ? `${EMOJIS.success} अपलोड हो गया!\n\n• */extract* - डेटा निकालें\n• */compliance* - अनुपालन जांचें\n• */ask [सवाल]* - पूछें\n\nक्या करना चाहेंगे?`
      : `${EMOJIS.success} Uploaded!\n\n• */extract* - Extract data\n• */compliance* - Check compliance\n• */ask [question]* - Ask about it\n\nWhat would you like to do?`;
    await chat.sendMessage(successMsg);

    logger.info('Document processed', { userId, fileName, docId: uploadResult.document_id });
  } catch (error) {
    logger.error('Document handling error:', { userId, error: error.message });
    const errMsg = lang === 'hi'
      ? 'दस्तावेज़ प्रोसेस करने में समस्या। कृपया पुनः प्रयास करें।'
      : 'Problem processing your document. Please try again.';
    await chat.sendMessage(formatError(errMsg, lang));
  }
}

function getExtension(mimeType, filename) {
  if (filename) {
    const parts = filename.split('.');
    if (parts.length > 1) return parts.pop().toLowerCase();
  }
  const mimeMap = {
    'application/pdf': 'pdf',
    'image/png': 'png',
    'image/jpeg': 'jpg',
    'image/jpg': 'jpg',
    'image/tiff': 'tiff',
    'image/bmp': 'bmp',
  };
  return mimeMap[mimeType] || 'unknown';
}

function getUserDocument(userId) {
  return userDocuments.get(userId);
}

function setUserDocument(userId, docInfo) {
  userDocuments.set(userId, docInfo);
}


module.exports = { handleDocument, getUserDocument, setUserDocument };
