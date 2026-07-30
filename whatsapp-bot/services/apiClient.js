const axios = require('axios');
const config = require('../config');
const logger = require('../utils/logger');

class ApiClient {
  constructor() {
    this.client = axios.create({
      baseURL: config.api.baseUrl,
      timeout: config.api.timeout,
      headers: { 'X-API-Key': config.api.apiKey },
    });

    this.client.interceptors.request.use((req) => {
      logger.debug(`API Request: ${req.method?.toUpperCase()} ${req.url}`);
      return req;
    });

    this.client.interceptors.response.use(
      (res) => res,
      (error) => {
        logger.error('API Error:', {
          url: error.config?.url,
          status: error.response?.status,
          message: error.message,
        });
        throw error;
      }
    );
  }

  async uploadDocument(fileBuffer, fileName, mimeType, userId) {
    try {
      const FormData = require('form-data');
      const formData = new FormData();
      formData.append('file', fileBuffer, { filename: fileName, contentType: mimeType });
      formData.append('user_id', userId);

      const response = await this.client.post('/api/documents/upload', formData, {
        headers: { ...formData.getHeaders() },
        maxContentLength: config.bot.maxFileSize * 1024 * 1024,
      });

      logger.info(`Document uploaded: ${response.data.document_id}`, { userId });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Failed to upload document.');
    }
  }

  async getExtractionResults(documentId) {
    try {
      const response = await this.client.get(`/api/documents/${documentId}/extract`);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Failed to get extraction results.');
    }
  }

  async submitQuery(documentId, question, language = 'en') {
    try {
      const response = await this.client.post('/api/documents/query', {
        document_id: documentId, question, language,
      });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Failed to process your question.');
    }
  }

  async getComplianceReport(documentId) {
    try {
      const response = await this.client.get(`/api/documents/${documentId}/compliance`);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Failed to get compliance report.');
    }
  }

  async getStatus(documentId) {
    try {
      const response = await this.client.get(`/api/documents/${documentId}/status`);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Failed to check status.');
    }
  }

  async healthCheck() {
    try {
      const response = await this.client.get('/health', { timeout: 5000 });
      return response.status === 200;
    } catch {
      return false;
    }
  }
}

module.exports = new ApiClient();
