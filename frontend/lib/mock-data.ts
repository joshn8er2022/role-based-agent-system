// Mock data for DSPY Boss Frontend development

import { AgentType, TaskType, MCPServerType, SystemMetrics, SystemOverview } from './types';

export const mockAgents: AgentType[] = [
  {
    id: 'research_specialist',
    name: 'Research Specialist',
    type: 'human',
    description: 'Human expert in research and analysis',
    capabilities: ['research', 'analysis', 'reporting'],
    is_available: true,
    max_concurrent_tasks: 3,
    current_tasks: 1,
    contact_method: 'slack',
    created_at: '2025-08-17T21:31:31.123456',
    last_active: '2025-08-18T00:00:00.000000'
  },
  {
    id: 'sales_manager',
    name: 'Sales Manager',
    type: 'human',
    description: 'Human sales manager for deal management',
    capabilities: ['sales', 'crm', 'customer_relations'],
    is_available: true,
    max_concurrent_tasks: 3,
    current_tasks: 2,
    contact_method: 'close_crm',
    created_at: '2025-08-17T21:31:31.123456',
    last_active: '2025-08-18T00:05:00.000000'
  },
  {
    id: 'data_analyst',
    name: 'Data Analyst Agent',
    type: 'agentic',
    description: 'Autonomous agent for data analysis tasks',
    capabilities: ['data_analysis', 'visualization', 'reporting'],
    is_available: true,
    max_concurrent_tasks: 3,
    current_tasks: 0,
    model_name: 'gpt-4',
    created_at: '2025-08-17T21:31:31.123456'
  }
];

export const mockTasks: TaskType[] = [
  {
    id: 'task_1',
    title: 'Market Research Analysis',
    description: 'Analyze current market trends for Q4 planning',
    priority: 'HIGH',
    status: 'IN_PROGRESS',
    assigned_agent: 'research_specialist',
    capabilities_required: ['research', 'analysis'],
    created_at: '2025-08-18T00:00:00.000000',
    updated_at: '2025-08-18T00:05:00.000000'
  },
  {
    id: 'task_2',
    title: 'Customer Outreach Campaign',
    description: 'Reach out to potential customers for new product launch',
    priority: 'MEDIUM',
    status: 'PENDING',
    capabilities_required: ['sales', 'customer_relations'],
    created_at: '2025-08-18T00:10:00.000000'
  },
  {
    id: 'task_3',
    title: 'Data Visualization Dashboard',
    description: 'Create interactive dashboard for sales metrics',
    priority: 'LOW',
    status: 'COMPLETED',
    assigned_agent: 'data_analyst',
    capabilities_required: ['data_analysis', 'visualization'],
    created_at: '2025-08-17T22:00:00.000000',
    completed_at: '2025-08-18T00:00:00.000000'
  }
];

export const mockMCPServers: MCPServerType[] = [
  {
    id: 'close_crm',
    name: 'Close CRM',
    url: 'https://close-mcp-server.klavis.ai/mcp/',
    description: 'Close CRM integration for customer management',
    capabilities: ['crm', 'contacts', 'deals', 'communication'],
    is_active: true,
    is_connected: true,
    last_connected: '2025-08-18T00:00:00.000000',
    connection_timeout: 30,
    retry_attempts: 3
  },
  {
    id: 'slack',
    name: 'Slack',
    url: 'https://slack-mcp-server.klavis.ai/mcp/',
    description: 'Slack integration for team communication',
    capabilities: ['messaging', 'channels', 'notifications'],
    is_active: true,
    is_connected: true,
    last_connected: '2025-08-18T00:02:00.000000',
    connection_timeout: 30,
    retry_attempts: 3
  },
  {
    id: 'deep_research',
    name: 'Deep Research',
    url: 'https://firecrawl-deep-research-mcp-server.klavis.ai/mcp/',
    description: 'Deep research capabilities using Firecrawl',
    capabilities: ['research', 'web_scraping', 'analysis'],
    is_active: true,
    is_connected: false,
    connection_timeout: 30,
    retry_attempts: 3
  }
];

export const mockSystemMetrics: SystemMetrics = {
  timestamp: '2025-08-18T00:05:00.000000',
  uptime_seconds: 3600,
  total_agents: 3,
  active_agents: 3,
  total_tasks: 5,
  completed_tasks: 12,
  failed_tasks: 1,
  tasks_per_minute: 2.5,
  cpu_usage_percent: 45.2,
  memory_usage_mb: 512.8,
  disk_usage_percent: 23.1
};

export const mockSystemOverview: SystemOverview = {
  boss_state: 'ACTIVE',
  state_data: {
    current_focus: 'task_processing',
    active_workflows: 2,
    pending_decisions: 0
  },
  metrics: mockSystemMetrics,
  health_score: 87
};

export function generateMockSystemOverview(): SystemOverview {
  return {
    boss_state: 'ACTIVE',
    state_data: {
      current_focus: 'task_processing',
      active_workflows: Math.floor(Math.random() * 5) + 1,
      pending_decisions: Math.floor(Math.random() * 3)
    },
    metrics: {
      timestamp: new Date().toISOString(),
      uptime_seconds: Math.floor(Math.random() * 86400) + 3600,
      total_agents: 3,
      active_agents: Math.floor(Math.random() * 3) + 1,
      total_tasks: Math.floor(Math.random() * 10) + 5,
      completed_tasks: Math.floor(Math.random() * 50) + 10,
      failed_tasks: Math.floor(Math.random() * 5),
      tasks_per_minute: Math.random() * 5 + 1,
      cpu_usage_percent: Math.random() * 80 + 10,
      memory_usage_mb: Math.random() * 1000 + 200,
      disk_usage_percent: Math.random() * 50 + 10
    },
    health_score: Math.floor(Math.random() * 30) + 70
  };
}
