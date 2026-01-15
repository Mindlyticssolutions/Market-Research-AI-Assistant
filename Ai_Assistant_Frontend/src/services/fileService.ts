/**
 * File Service
 * Handles file upload and management
 */
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1/files';

export interface FileInfo {
  id: string;
  filename: string;
  file_type: string;
  size: number;
  uploaded_at: string;
  status: 'pending' | 'processing' | 'indexed' | 'failed';
  chunks_indexed?: number;
}

export interface UploadResponse {
  message: string;
  file_id: string;
  filename: string;
  status: string;
}

export const fileService = {
  /**
   * Upload a file for RAG indexing
   */
  uploadFile: async (file: File): Promise<UploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await axios.post<UploadResponse>(`${API_BASE_URL}/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  },

  /**
   * List all uploaded files
   */
  listFiles: async (): Promise<FileInfo[]> => {
    const response = await axios.get<FileInfo[]>(`${API_BASE_URL}/list`);
    return response.data;
  },

  /**
   * Get file status
   */
  getFileStatus: async (fileId: string): Promise<{ status: string; chunks_indexed?: number }> => {
    const response = await axios.get(`${API_BASE_URL}/${fileId}/status`);
    return response.data;
  },

  /**
   * Delete a file
   */
  deleteFile: async (fileId: string): Promise<void> => {
    await axios.delete(`${API_BASE_URL}/${fileId}`);
  },
};
