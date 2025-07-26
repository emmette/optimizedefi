'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { RefreshCw, AlertCircle, TrendingUp, DollarSign, Clock, Users } from 'lucide-react';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  ChartOptions,
} from 'chart.js';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

interface MetricsData {
  timestamp: string;
  ai_metrics: {
    overall: {
      total_requests: number;
      total_tokens: number;
      total_cost: number;
      average_duration: number;
    };
    agents: Record<string, any>;
    models: Record<string, any>;
  };
  rate_limits: Record<string, any>;
  model_usage: Record<string, string[]>;
}

interface PerformanceData {
  overall: {
    average_duration_ms: number;
    total_requests: number;
    requests_per_hour: number;
  };
  by_agent: Record<string, any>;
  by_model: Record<string, any>;
}

export function MetricsDashboard() {
  const [metrics, setMetrics] = useState<MetricsData | null>(null);
  const [performance, setPerformance] = useState<PerformanceData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const fetchMetrics = async () => {
    try {
      setRefreshing(true);
      const token = localStorage.getItem('auth_token');
      
      // Fetch summary metrics
      const metricsRes = await fetch('/api/metrics/summary', {
        headers: { Authorization: `Bearer ${token}` },
      });
      
      // Fetch performance metrics
      const perfRes = await fetch('/api/metrics/performance?hours=24', {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!metricsRes.ok || !perfRes.ok) {
        throw new Error('Failed to fetch metrics');
      }

      const metricsData = await metricsRes.json();
      const perfData = await perfRes.json();

      setMetrics(metricsData);
      setPerformance(perfData);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load metrics');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchMetrics();
    // Refresh every 30 seconds
    const interval = setInterval(fetchMetrics, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 dark:border-white"></div>
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  if (!metrics || !performance) {
    return null;
  }

  // Prepare chart data
  const agentRequestsData = {
    labels: Object.keys(metrics.ai_metrics.agents || {}),
    datasets: [{
      label: 'Requests by Agent',
      data: Object.values(metrics.ai_metrics.agents || {}).map((a: any) => a.requests || 0),
      backgroundColor: [
        'rgba(255, 99, 132, 0.5)',
        'rgba(54, 162, 235, 0.5)',
        'rgba(255, 206, 86, 0.5)',
        'rgba(75, 192, 192, 0.5)',
        'rgba(153, 102, 255, 0.5)',
      ],
      borderColor: [
        'rgba(255, 99, 132, 1)',
        'rgba(54, 162, 235, 1)',
        'rgba(255, 206, 86, 1)',
        'rgba(75, 192, 192, 1)',
        'rgba(153, 102, 255, 1)',
      ],
      borderWidth: 1,
    }],
  };

  const modelCostsData = {
    labels: Object.keys(metrics.ai_metrics.models || {}),
    datasets: [{
      label: 'Cost by Model ($)',
      data: Object.values(metrics.ai_metrics.models || {}).map((m: any) => m.cost || 0),
      backgroundColor: 'rgba(75, 192, 192, 0.5)',
      borderColor: 'rgba(75, 192, 192, 1)',
      borderWidth: 1,
    }],
  };

  const chartOptions: ChartOptions<'bar'> = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top' as const,
      },
    },
  };

  const doughnutOptions: ChartOptions<'doughnut'> = {
    responsive: true,
    plugins: {
      legend: {
        position: 'right' as const,
      },
    },
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-3xl font-bold">AI Metrics Dashboard</h2>
        <Button
          onClick={fetchMetrics}
          disabled={refreshing}
          variant="outline"
          size="sm"
        >
          <RefreshCw className={`mr-2 h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Requests</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {metrics.ai_metrics.overall.total_requests.toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground">
              {performance.overall.requests_per_hour.toFixed(1)} per hour
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Cost</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              ${metrics.ai_metrics.overall.total_cost.toFixed(4)}
            </div>
            <p className="text-xs text-muted-foreground">
              All time usage
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Response Time</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {performance.overall.average_duration_ms.toFixed(0)}ms
            </div>
            <p className="text-xs text-muted-foreground">
              Across all agents
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Models</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {Object.keys(metrics.ai_metrics.models || {}).length}
            </div>
            <p className="text-xs text-muted-foreground">
              Unique models in use
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Metrics Tabs */}
      <Tabs defaultValue="agents" className="space-y-4">
        <TabsList>
          <TabsTrigger value="agents">Agents</TabsTrigger>
          <TabsTrigger value="models">Models</TabsTrigger>
          <TabsTrigger value="costs">Costs</TabsTrigger>
          <TabsTrigger value="rate-limits">Rate Limits</TabsTrigger>
        </TabsList>

        <TabsContent value="agents" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Requests by Agent</CardTitle>
              </CardHeader>
              <CardContent>
                <Bar data={agentRequestsData} options={chartOptions} />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Agent Performance</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {Object.entries(performance.by_agent).map(([agent, data]: [string, any]) => (
                    <div key={agent} className="flex justify-between items-center p-2 border rounded">
                      <span className="font-medium">{agent}</span>
                      <div className="text-sm text-muted-foreground">
                        <span>{data.average_duration_ms.toFixed(0)}ms</span>
                        <span className="ml-4">{data.requests} requests</span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="models" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Model Usage</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {Object.entries(metrics.model_usage).map(([model, agents]) => (
                    <div key={model} className="p-2 border rounded">
                      <div className="font-medium">{model}</div>
                      <div className="text-sm text-muted-foreground">
                        Used by: {agents.join(', ')}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Model Performance</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {Object.entries(performance.by_model).map(([model, data]: [string, any]) => (
                    <div key={model} className="flex justify-between items-center p-2 border rounded">
                      <span className="font-medium text-sm">{model}</span>
                      <div className="text-sm text-muted-foreground">
                        <span>{data.average_duration_ms.toFixed(0)}ms</span>
                        {data.rate_limit_hits > 0 && (
                          <span className="ml-2 text-red-500">
                            {data.rate_limit_hits} limits hit
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="costs" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Cost Breakdown by Model</CardTitle>
            </CardHeader>
            <CardContent>
              <Bar data={modelCostsData} options={chartOptions} />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="rate-limits" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Rate Limit Status</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {Object.entries(metrics.rate_limits).map(([model, limits]: [string, any]) => (
                  <div key={model} className="p-3 border rounded">
                    <div className="font-medium mb-2">{model}</div>
                    {limits.limits?.map((limit: any, idx: number) => (
                      <div key={idx} className="flex justify-between text-sm">
                        <span>{limit.limit_type}</span>
                        <span className={limit.usage_percent > 80 ? 'text-red-500' : ''}>
                          {limit.used}/{limit.limit} ({limit.usage_percent.toFixed(1)}%)
                        </span>
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}