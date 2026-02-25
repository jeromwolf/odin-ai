import axios, { AxiosInstance } from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:9000/api';
const TOKEN_KEY = process.env.REACT_APP_TOKEN_KEY || 'odin_ai_token';

export interface GraphNode {
  id: string;
  label: string;
  type: string; // 'bid' | 'organization' | 'tag' | 'region'
  data?: Record<string, any>;
}

export interface GraphEdge {
  source: string;
  target: string;
  label?: string;
  weight?: number;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface GlobalAskResponse {
  success: boolean;
  query: string;
  answer: string;
  communities: Array<{
    community_id: number;
    title: string;
    summary: string;
    entity_count: number;
    bid_count: number;
    findings: Array<{ type: string; entity: string }>;
  }>;
  related_entities: Array<{
    type: string;
    name: string;
    description: string;
    community_id: number;
  }>;
  has_llm_answer: boolean;
}

export interface GraphStatus {
  neo4j_connected: boolean;
  node_counts?: Record<string, number>;
  relationship_counts?: Record<string, number>;
  total_nodes?: number;
  total_relationships?: number;
}

class GraphService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.api.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem(TOKEN_KEY);
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );
  }

  async getStatus(): Promise<GraphStatus> {
    const response = await this.api.get('/graph/status');
    return response.data;
  }

  async getRelatedBids(bidNo: string, depth: number = 2): Promise<any> {
    const response = await this.api.get(
      `/graph/related/${encodeURIComponent(bidNo)}?depth=${depth}`
    );
    return response.data;
  }

  async getOrgNetwork(orgName: string): Promise<any> {
    const response = await this.api.get(
      `/graph/org/${encodeURIComponent(orgName)}`
    );
    return response.data;
  }

  async getTagNetwork(tagName: string): Promise<any> {
    const response = await this.api.get(
      `/graph/tag/${encodeURIComponent(tagName)}`
    );
    return response.data;
  }

  async getRegionBids(region: string): Promise<any> {
    const response = await this.api.get(
      `/graph/region/${encodeURIComponent(region)}`
    );
    return response.data;
  }

  async globalAsk(
    query: string,
    topCommunities: number = 5
  ): Promise<GlobalAskResponse> {
    const response = await this.api.get(
      `/rag/global-ask?q=${encodeURIComponent(query)}&top_communities=${topCommunities}`
    );
    return response.data;
  }

  async getRagStatus(): Promise<any> {
    const response = await this.api.get('/rag/status');
    return response.data;
  }
}

export const graphService = new GraphService();
export default graphService;
