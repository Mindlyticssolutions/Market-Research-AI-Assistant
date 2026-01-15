import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1/databricks';

export interface ExecutionResult {
  status: string;
  output?: string;
  error?: string;
  plot?: string; // Base64 encoded image
}

export const databricksService = {
  /**
   * Execute code on a Databricks cluster
   */
  executeCode: async (clusterId: string, code: string): Promise<ExecutionResult> => {
    const response = await axios.post<ExecutionResult>(`${API_BASE_URL}/execute`, {
      cluster_id: clusterId,
      code,
      language: 'python'
    });
    return response.data;
  },

  /**
   * List available clusters
   */
  listClusters: async (): Promise<Cluster[]> => {
    const response = await axios.get(`${API_BASE_URL}/clusters`);
    return response.data;
  },

  /**
   * Start a cluster
   */
  startCluster: async (clusterId: string): Promise<any> => {
    const response = await axios.post(`${API_BASE_URL}/clusters/${clusterId}/start`);
    return response.data;
  },

  /**
   * Stop/Terminate a cluster
   */
  stopCluster: async (clusterId: string): Promise<any> => {
    const response = await axios.post(`${API_BASE_URL}/clusters/${clusterId}/stop`);
    return response.data;
  },

  /**
   * Restart kernel (Destroy execution context)
   */
  restartContext: async (clusterId: string): Promise<any> => {
    const response = await axios.post(`${API_BASE_URL}/context/destroy`, null, {
      params: { cluster_id: clusterId }
    });
    return response.data;
  },

  /**
   * Mount storage to cluster
   */
  mountStorage: async (clusterId: string): Promise<any> => {
    const response = await axios.post(`${API_BASE_URL}/mount-storage`, null, {
      params: { cluster_id: clusterId }
    });
    return response.data;
  }
};

export interface Cluster {
  cluster_id: string;
  cluster_name: string;
  state: string;
}
