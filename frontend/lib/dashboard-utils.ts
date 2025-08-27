// Dashboard utility functions for DSPY Boss

export function formatRelativeTime(timestamp: string): string {
  const now = new Date();
  const time = new Date(timestamp);
  const diffInSeconds = Math.floor((now.getTime() - time.getTime()) / 1000);

  if (diffInSeconds < 60) {
    return `${diffInSeconds}s ago`;
  } else if (diffInSeconds < 3600) {
    const minutes = Math.floor(diffInSeconds / 60);
    return `${minutes}m ago`;
  } else if (diffInSeconds < 86400) {
    const hours = Math.floor(diffInSeconds / 3600);
    return `${hours}h ago`;
  } else {
    const days = Math.floor(diffInSeconds / 86400);
    return `${days}d ago`;
  }
}

export function getStatusColor(status: string): string {
  switch (status.toLowerCase()) {
    case 'active':
    case 'available':
    case 'connected':
    case 'healthy':
      return 'text-green-600';
    case 'idle':
    case 'pending':
      return 'text-yellow-600';
    case 'error':
    case 'failed':
    case 'disconnected':
      return 'text-red-600';
    case 'maintenance':
    case 'scaling':
      return 'text-blue-600';
    default:
      return 'text-gray-600';
  }
}

export function getHealthScoreColor(score: number): string {
  if (score >= 90) return 'text-green-600';
  if (score >= 70) return 'text-yellow-600';
  if (score >= 50) return 'text-orange-600';
  return 'text-red-600';
}

export function formatPercentage(value: number): string {
  return `${Math.round(value)}%`;
}

export function formatNumber(value: number): string {
  if (value >= 1000000) {
    return `${(value / 1000000).toFixed(1)}M`;
  } else if (value >= 1000) {
    return `${(value / 1000).toFixed(1)}K`;
  }
  return value.toString();
}

export function getHealthScore(overview: any): number {
  if (overview && overview.health_score) {
    return overview.health_score;
  }
  return 0;
}
