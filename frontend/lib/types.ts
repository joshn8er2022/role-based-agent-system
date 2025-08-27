// Types for DSPY Boss Frontend

export interface AgentType {
  id: string;
  name: string;
  type: 'human' | 'agentic';
  description: string;
  capabilities: string[];
  is_available: boolean;
  max_concurrent_tasks: number;
  current_tasks: number;
  model_name?: string;
  contact_method?: string;
  created_at: string;
  last_active?: string;
}

export interface TaskType {
  id: string;
  title: string;
  description: string;
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT';
  status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED';
  assigned_agent?: string;
  capabilities_required: string[];
  created_at: string;
  updated_at?: string;
  completed_at?: string;
}

export interface MCPServerType {
  id: string;
  name: string;
  url: string;
  description: string;
  capabilities: string[];
  is_active: boolean;
  is_connected: boolean;
  last_connected?: string;
  connection_timeout: number;
  retry_attempts: number;
}

export interface SystemMetrics {
  timestamp: string;
  uptime_seconds: number;
  total_agents: number;
  active_agents: number;
  total_tasks: number;
  completed_tasks: number;
  failed_tasks: number;
  tasks_per_minute: number;
  cpu_usage_percent: number;
  memory_usage_mb: number;
  disk_usage_percent: number;
}

export interface BossState {
  state: 'IDLE' | 'ACTIVE' | 'SCALING' | 'MAINTENANCE' | 'ERROR';
  data: any;
  timestamp: string;
}

export interface SystemOverview {
  boss_state: string;
  state_data: any;
  metrics: SystemMetrics;
  health_score: number;
}

export interface LLMProvider {
  name: string;
  type: string;
  models: string[];
  is_active: boolean;
  config: any;
}
