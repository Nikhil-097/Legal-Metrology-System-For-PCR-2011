import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface Violation {
  rule: string;
  code: string;
  severity: 'HIGH' | 'MEDIUM' | 'LOW';
  detail: string;
}

export interface ExtractedDeclarations {
  net_quantity?: string;
  mrp?: string;
  has_tax_clause?: boolean;
  unit_sale_price?: string;
  mfg_date?: string;
  country_of_origin?: string;
}

export interface ScanResult {
  scan_id: string;
  brand_name: string;
  commodity_name: string;
  barcode?: string;
  pdp_area_cm2: number;
  required_min_font_height_mm: number;
  compliance_score: number;
  is_compliant: boolean;
  violations: Violation[];
  extracted_declarations?: ExtractedDeclarations;
  extracted_data?: any;
  created_at?: string;
  status?: string;
}

export const fetchDashboardStats = async () => {
  const response = await apiClient.get('/analytics/dashboard-stats');
  return response.data;
};

export const fetchScanHistory = async (): Promise<ScanResult[]> => {
  const response = await apiClient.get('/scans/history');
  return response.data;
};

export const fetchScanById = async (scanId: string): Promise<ScanResult> => {
  const response = await apiClient.get(`/scans/${scanId}`);
  return response.data;
};

export const fetchRulesSummary = async () => {
  const response = await apiClient.get('/rules/summary');
  return response.data;
};

export const analyzePackageScan = async (formData: FormData): Promise<ScanResult> => {
  const response = await apiClient.post('/scans/analyze', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};